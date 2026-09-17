"""公考行测选择题答题卡纯本地 CV 高速扫描与置信度裁决引擎
负责利用物理点阵几何投影、局部背景白平衡自适应校准与多尺度石墨填充积分，
对答题卡进行 0 毫秒高速纯本地识别；
输出高置信度选项与需大模型靶向审验的争议题（contested）列表及其微型条带切片。
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger("math-grader")

cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

import omr_annotator


def measure_bubble_patch(
    gray: np.ndarray,
    cx: int,
    cy: int,
    local_bg: float,
    img_w: int,
    img_h: int
) -> Tuple[int, float, int]:
    """在气泡中心局部窗口内进行多尺度自适应微位移搜索，测定真实石墨填涂物理特征。

    返回：
        (best_dark_count, best_mean_gray, min_gray)
    """
    best_dark = 0
    best_mean = 255.0
    best_min = 255

    # 动态暗像素阈值：比局部纸张背景显著暗出 38 灰阶，或者绝对灰度 < 142
    dark_thresh = min(142, int(local_bg - 38))

    for dy in (-3, 0, 3):
        for dx in (-3, 0, 3):
            y1 = max(0, cy + dy - 6)
            y2 = min(img_h, cy + dy + 7)
            x1 = max(0, cx + dx - 11)
            x2 = min(img_w, cx + dx + 12)
            patch = gray[y1:y2, x1:x2]
            if patch.size == 0:
                continue

            dark_cnt = int(np.sum(patch < dark_thresh))
            m = float(np.mean(patch))
            min_v = int(np.min(patch))

            if dark_cnt > best_dark or (dark_cnt == best_dark and m < best_mean):
                best_dark = dark_cnt
                best_mean = m
                best_min = min_v

    return best_dark, best_mean, best_min


def scan_sheet_cv(
    img_bgr: np.ndarray,
    expected_total_q: int = 135,
    custom_layout: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """执行传统计算机视觉快速扫描，对整卷客观题进行填涂判定并评估置信度。

    参数：
        img_bgr: 手机拍摄或上传的原始/预处理答题卡 BGR 图像
        expected_total_q: 预期题数 (通常为 120, 130, 135 等)
        custom_layout: 可选自定义答题卡排版参数字典

    返回字典包含：
        - answers: Dict[int, Optional[str]] 初步识别结果
        - confidences: Dict[int, str] 每题置信度 ('high_single' | 'high_blank' | 'contested')
        - contested_questions: List[int] 属于低置信度/争议题的题号列表
        - details: Dict[int, Dict] 各题详细物理测量分值 (用于复盘排查)
        - deskewed_img: np.ndarray 经过高精倾斜校正后的图像
        - layout: Dict[str, Any] 最终使用的几何排版布局
    """
    if img_bgr is None or img_bgr.size == 0:
        return {
            "answers": {},
            "confidences": {},
            "contested_questions": [],
            "details": {},
            "deskewed_img": img_bgr,
            "layout": omr_annotator.DEFAULT_OMR_LAYOUT
        }

    # 1. 倾斜摆正
    deskewed, detected_angle = omr_annotator.deskew_omr_sheet(img_bgr)
    if abs(detected_angle) > 0.3:
        logger.info(f"[OMR-CV] 答题卡完成倾斜校正: 纠正角度={detected_angle:.2f}°")

    img_h, img_w = deskewed.shape[:2]
    gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY)

    layout = dict(omr_annotator.DEFAULT_OMR_LAYOUT)
    if custom_layout and isinstance(custom_layout, dict):
        for k, v in custom_layout.items():
            if v is not None:
                layout[k] = v

    answers: Dict[int, Optional[str]] = {}
    confidences: Dict[int, str] = {}
    contested_questions: List[int] = []
    details: Dict[int, Dict[str, Any]] = {}

    for q in range(1, expected_total_q + 1):
        geom = omr_annotator.get_question_geometry(q, layout, img_w, img_h)
        if not geom:
            answers[q] = None
            confidences[q] = "contested"
            contested_questions.append(q)
            continue

        x1, y1, _, y2, bubbles = geom

        # 测量本行纸张局部背景均值（采样题号左侧空白区域）
        bg_x1 = max(0, x1 - 25)
        bg_x2 = max(1, x1 - 5)
        bg_y1 = max(0, y1)
        bg_y2 = min(img_h, y2)
        bg_patch = gray[bg_y1:bg_y2, bg_x1:bg_x2]
        local_bg = float(np.mean(bg_patch)) if bg_patch.size > 0 else 225.0
        # 限制背景均值在合理纸张范围内
        local_bg = max(180.0, min(245.0, local_bg))

        scores = {}
        for opt in ["A", "B", "C", "D"]:
            cx, cy = bubbles[opt]
            dark_cnt, mean_g, min_g = measure_bubble_patch(gray, cx, cy, local_bg, img_w, img_h)
            scores[opt] = {
                "dark_count": dark_cnt,
                "mean_gray": mean_g,
                "min_gray": min_g,
                "diff_bg": local_bg - mean_g
            }

        # 排序寻找最大填涂
        ranked = sorted(scores.items(), key=lambda it: (it[1]["dark_count"], it[1]["diff_bg"]))
        top1_opt, top1_val = ranked[-1]
        top2_opt, top2_val = ranked[-2]

        top1_dark = top1_val["dark_count"]
        top2_dark = top2_val["dark_count"]
        top1_mean = top1_val["mean_gray"]
        top2_mean = top2_val["mean_gray"]
        top1_diff = top1_val["diff_bg"]

        # ============================================================
        # 严谨置信度决策矩阵 (三级分类)
        # ============================================================
        details[q] = {
            "top1": (top1_opt, top1_dark, top1_mean),
            "top2": (top2_opt, top2_dark, top2_mean),
            "local_bg": local_bg
        }

        # 1. 明确单选 (HIGH_CONF_SINGLE)：
        # 条件：Top1 填涂饱满，且是 Top2 的 1.6 倍以上，其余 3 项暗像素极低接近白纸
        is_clear_single = (
            (top1_dark >= 60 and top1_dark >= 1.6 * top2_dark and top2_dark < 38 and top1_diff > 35.0) or
            (top1_dark >= 80 and top1_dark >= 1.45 * top2_dark and top2_dark < 45) or
            (top1_dark >= 110 and top1_dark >= 1.35 * top2_dark) or
            (top1_mean < 125.0 and top1_dark >= 50 and top2_dark < 28)
        )

        # 2. 明确空白未填 (HIGH_CONF_BLANK)：
        # 条件：所有 4 个选项暗像素均极低，无任何有效石墨痕迹
        is_clear_blank = (
            top1_dark < 24 and
            top1_diff < 18.0 and
            all(v["dark_count"] < 24 for v in scores.values())
        )

        if is_clear_single:
            answers[q] = top1_opt
            confidences[q] = "high_single"
        elif is_clear_blank:
            answers[q] = None
            confidences[q] = "high_blank"
        else:
            # 标记为争议题 (需多模态 LLM 进一步裁决)
            # 包含：疑似多涂、橡皮擦改擦除不净、浅涂笔迹、手写字母等
            is_multiple = (top1_dark >= 45 and top2_dark >= 40 and top1_dark < 1.35 * top2_dark)
            answers[q] = "multiple" if is_multiple else top1_opt
            confidences[q] = "contested"
            contested_questions.append(q)

    logger.info(
        f"[OMR-CV] 本地快速扫描完成: 总题数={expected_total_q}, "
        f"高置信单选={sum(1 for c in confidences.values() if c == 'high_single')}, "
        f"高置信空白={sum(1 for c in confidences.values() if c == 'high_blank')}, "
        f"争议题数={len(contested_questions)}"
    )

    return {
        "answers": answers,
        "confidences": confidences,
        "contested_questions": contested_questions,
        "details": details,
        "deskewed_img": deskewed,
        "layout": layout
    }


def crop_question_strip(
    img_bgr: np.ndarray,
    q_num: int,
    layout: Dict[str, Any],
    padding_x: int = 15,
    padding_y: int = 6
) -> Optional[np.ndarray]:
    """裁剪指定题号的完整水平条带 (包括题号印刷字与 A/B/C/D 四个气泡)。"""
    img_h, img_w = img_bgr.shape[:2]
    geom = omr_annotator.get_question_geometry(q_num, layout, img_w, img_h)
    if not geom:
        return None

    _, y1, _, y2, bubbles = geom
    # 向左延伸包含题号数字，向右延伸包含 D 选项
    xA, _ = bubbles["A"]
    xD, _ = bubbles["D"]
    dx = xD - xA

    strip_x1 = max(0, xA - int(dx * 0.9) - padding_x)
    strip_x2 = min(img_w, xD + int(dx * 0.5) + padding_x)
    strip_y1 = max(0, y1 - padding_y)
    strip_y2 = min(img_h, y2 + padding_y)

    strip = img_bgr[strip_y1:strip_y2, strip_x1:strip_x2]
    if strip.size == 0:
        return None
    return strip


def build_contested_composite(
    img_bgr: np.ndarray,
    contested_questions: List[int],
    layout: Dict[str, Any]
) -> Optional[np.ndarray]:
    """将所有争议题切成水平小条带，左侧贴上清晰醒目的题号标牌，并垂直堆叠拼成一张极小的紧凑微图。

    生成微图尺寸通常仅约 360px × (35px × N)，极小、极大降低多模态大模型的视觉输入负担与 Token 消耗。
    """
    if not contested_questions:
        return None

    strips = []
    max_strip_w = 0
    font = cv2.FONT_HERSHEY_SIMPLEX

    for q in contested_questions:
        raw_strip = crop_question_strip(img_bgr, q, layout)
        if raw_strip is None:
            continue

        sh, sw = raw_strip.shape[:2]
        # 统一规范条带高度为 42px (高质量 Lanczos 插值)
        target_h = 42
        scale = target_h / float(sh)
        target_w = max(100, int(sw * scale))
        resized = cv2.resize(raw_strip, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        # 在条带左侧添加 65px 宽度的纯白题号指示牌
        tag_w = 70
        labeled_strip = np.full((target_h, target_w + tag_w, 3), 255, dtype=np.uint8)
        # 绘制题号文字：例如 "Q.12"
        tag_text = f"Q.{q}"
        cv2.putText(
            labeled_strip,
            tag_text,
            (6, int(target_h * 0.68)),
            font,
            0.62,
            (180, 50, 20),  # 醒目深蓝/深红色
            2,
            cv2.LINE_AA
        )
        # 绘制浅灰竖分隔线
        cv2.line(labeled_strip, (tag_w - 2, 4), (tag_w - 2, target_h - 4), (200, 200, 200), 1)

        # 贴上题目原图切片
        labeled_strip[:, tag_w:] = resized

        strips.append(labeled_strip)
        if labeled_strip.shape[1] > max_strip_w:
            max_strip_w = labeled_strip.shape[1]

    if not strips:
        return None

    # 规范所有条带宽度一致，并拼成一张紧凑大图
    pad_strips = []
    for s in strips:
        sh, sw = s.shape[:2]
        if sw < max_strip_w:
            padded = np.full((sh, max_strip_w, 3), 255, dtype=np.uint8)
            padded[:, :sw] = s
            pad_strips.append(padded)
        else:
            pad_strips.append(s)

    # 拼接并在各题目条带之间加上 3px 浅灰分割线
    divider = np.full((3, max_strip_w, 3), 240, dtype=np.uint8)
    final_rows = []
    for i, s in enumerate(pad_strips):
        if i > 0:
            final_rows.append(divider)
        final_rows.append(s)

    composite = np.vstack(final_rows)
    return composite
