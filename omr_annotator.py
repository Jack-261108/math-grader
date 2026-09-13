"""公考选择题答题卡 (OMR) 智能批注与原卷呈现引擎
在用户上传的真实答题卡照片上（或高保真仿真答题卡上），精准绘制红绿批改笔触：
- 绿色对勾 ✓：做对题目
- 红色叉号 ✗：做错题目（在错选选项上打叉，并标出标准正确答案）
- 黄/红字警示：未填漏涂与多涂
- 顶部成绩印章：行测实得分、正确率、做对/做错/未填统计
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import renderer


# 默认全国标准行测答题卡（4列 × 7题块）高精几何归一化参考坐标 (0~1000)
# 基于标准 1920x1440 答题卡物理点阵实测并经透视自适应校准
DEFAULT_OMR_LAYOUT = {
    "grid_box": [270, 130, 850, 830],
    "cols": [
        [130, 280],
        [305, 455],
        [480, 630],
        [665, 815]
    ],
    "bands": [
        [273, 346],  # Band 0: 1~20 题
        [356, 429],  # Band 1: 21~40 题
        [438, 510],  # Band 2: 41~60 题
        [519, 592],  # Band 3: 61~80 题
        [602, 675],  # Band 4: 81~100 题
        [674, 758],  # Band 5: 101~120 题
        [767, 853]   # Band 6: 121~140 题
    ],
    # 4 列的 A 选项归一化 X 中心 (按宽 1000 归一化)
    # Col 0 (Q1..20): 170.1‰ (~245px)
    # Col 1 (Q21..40): 343.8‰ (~495px)
    # Col 2 (Q41..60): 518.1‰ (~746px)
    # Col 3 (Q61..80): 689.0‰ (~992px)
    "col_xA_norm": [170.1, 343.8, 518.1, 689.0],
    # 三位数题号排版自适应补偿 (Band 5: 101~120 题, Band 6: 121~140 题, 及 Q100)
    # Col 0 (Q101..105, Q121..125): 容纳三位数题号向左平移一个气泡并拉大间距至 49px (34.0‰)
    # Col 3 (Q116..120, Q136..140, Q100): 容纳三位数题号向右平移并拉大间距至 48px (33.33‰)
    "col0_b56_xA_norm": 136.1,
    "col0_b56_bubble_dx_norm": 34.0,
    "col3_b56_xA_norm": 727.8,
    # 选项气泡横向中心间距 (42.5px / 1.44 = 29.51‰)
    "bubble_dx_norm": 29.51,
    # Col 3 三位数题号区域气泡放大间距 (48px / 1.44 = 33.33‰)
    "col3_b56_bubble_dx_norm": 33.33,
    # 7 个 Band 首行题目的归一化中心 Y 坐标 (以 Col 0 为基准, 按高 1000 归一化)
    "band_first_y_norm": [281.8, 359.4, 434.9, 510.4, 596.9, 678.1, 771.4],
    # 7 个 Band 内部每 5 小题的纵向自适应行距 (自适应手机拍照俯视透视近大远小)
    "band_step_y_norm": [14.06, 14.32, 15.10, 14.84, 16.15, 17.19, 17.34],
    # 4 列的拍照倾斜/卷面微弧度自适应纵向微调 (Col 0..3 依次微调, 彻底消除右侧与底端浮空)
    "col_dy_norm": [0.0, -3.5, -7.0, -8.5],
    # 列间倾斜自适应补偿系数 (支持手持拍摄微角度自适应对齐)
    "skew_k": 0.0
}


def refine_student_answers_with_cv(
    img_bgr: np.ndarray,
    student_answers: Dict[int, Optional[str]],
    grid_layout: Optional[Dict[str, Any]] = None
) -> Dict[int, Optional[str]]:
    """结合 OpenCV 物理气泡石墨灰度反差与几何先验，自动校准多模态视觉模型看偏、漏看或列漂移。

    针对 2B 铅笔涂卡进行真实光度密度测量：
    - 结合题号网格精确定位每个气泡（A、B、C、D）；
    - 在局部多尺度自适应窗口内搜索深色高反差石墨填涂核；
    - 当物理填涂具有显著优势（深灰均值低、暗斑面积大）而模型预测为空白/偏移选项时，自动订正为物理真实填涂；
    - 彻底杜绝多模态视觉大模型在连续上百道密集群体作答中偶发的错行、偏列问题。
    """
    if img_bgr is None or img_bgr.size == 0 or not student_answers:
        return {int(k): v for k, v in student_answers.items() if str(k).isdigit()} if student_answers else {}

    # 1. 规范化输入题号键为 int，防止类型混杂导致的比较报错或查找失效
    norm_answers: Dict[int, Optional[str]] = {}
    for k, v in student_answers.items():
        try:
            norm_answers[int(k)] = v
        except (ValueError, TypeError):
            continue

    if not norm_answers:
        return {}

    img_h, img_w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    merged_layout = dict(DEFAULT_OMR_LAYOUT)
    if grid_layout and isinstance(grid_layout, dict):
        for k, v in grid_layout.items():
            if v is not None and k not in [
                "col_xA_norm", "col0_b56_xA_norm", "col0_b56_bubble_dx_norm",
                "col3_b56_xA_norm", "col3_b56_bubble_dx_norm", "bubble_dx_norm",
                "band_first_y_norm", "band_step_y_norm", "col_dy_norm", "skew_k"
            ]:
                merged_layout[k] = v

    refined = dict(norm_answers)
    total_q = max(norm_answers.keys(), default=130)

    for q in range(1, total_q + 1):
        geom = get_question_geometry(q, merged_layout, img_w, img_h)
        if not geom:
            continue
        _, _, _, _, bubbles = geom

        scores = {}
        for opt in ["A", "B", "C", "D"]:
            cx, cy = bubbles[opt]
            best_dark = 0
            best_mean = 255.0
            best_min = 255
            # 多尺度自适应局部搜索 (dy: -3..3, dx: -3..3)
            for dy in (-3, 0, 3):
                for dx in (-3, 0, 3):
                    y1 = max(0, cy + dy - 6)
                    y2 = min(img_h, cy + dy + 7)
                    x1 = max(0, cx + dx - 11)
                    x2 = min(img_w, cx + dx + 12)
                    patch = gray[y1:y2, x1:x2]
                    if patch.size == 0:
                        continue
                    dark_cnt = int(np.sum(patch < 145))
                    m = float(np.mean(patch))
                    min_v = int(np.min(patch))
                    if dark_cnt > best_dark or (dark_cnt == best_dark and m < best_mean):
                        best_dark = dark_cnt
                        best_mean = m
                        best_min = min_v
            scores[opt] = (best_dark, best_mean, best_min)

        ranked = sorted(scores.items(), key=lambda x: (x[1][0], -x[1][1]))
        top1_opt, (top1_dark, top1_mean, _) = ranked[-1]
        _, (top2_dark, top2_mean, _) = ranked[-2]

        orig_choice = norm_answers.get(q)
        orig_dark, orig_mean, _ = scores.get(orig_choice, (0, 255.0, 255)) if orig_choice in scores else (0, 255.0, 255)

        # 填涂物理特性充分性判定 (支持实涂与浅涂 2B 铅笔墨斑)
        top1_has_fill = (
            (top1_dark >= 65 and top1_dark >= 1.25 * top2_dark and top1_mean < top2_mean - 3.0) or
            (top1_dark >= 50 and top1_dark >= 1.30 * top2_dark and top1_mean < top2_mean - 5.0) or
            (top1_mean < top2_mean - 8.0 and top1_dark >= 45) or
            (top1_dark >= 120 and top1_mean < 130.0)
        )

        # 原选项在物理上是否明显劣于 top1 候选（原选项空白或明显浅于真实涂墨）
        orig_is_blank = (
            orig_choice is None or
            orig_choice not in scores or
            orig_mean > 160.0 or
            orig_dark < 45 or
            (orig_mean > top1_mean + 10.0 and orig_dark < top1_dark * 0.75) or
            (top1_dark >= 1.35 * orig_dark and top1_mean < orig_mean - 4.0) or
            (top1_mean < orig_mean - 12.0)
        )

        if orig_choice != top1_opt and top1_has_fill and orig_is_blank:
            refined[q] = top1_opt
        elif orig_choice is None and (top1_dark >= 60 and top1_dark >= 1.25 * top2_dark):
            # 模型漏填补全
            refined[q] = top1_opt

    return refined


def deskew_omr_sheet(img_bgr: np.ndarray) -> Tuple[np.ndarray, float]:
    """检测答题卡拍摄倾斜角度并进行高保真旋转摆正校准"""
    if img_bgr is None or img_bgr.size == 0:
        return img_bgr, 0.0

    img_h, img_w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    detected_angle = 0.0

    # 1. 优先提取水平印刷线角度中位数 (最直接反映题行倾斜度)
    roi_h = gray[int(img_h * 0.2):int(img_h * 0.8), int(img_w * 0.1):int(img_w * 0.85)]
    edges = cv2.Canny(roi_h, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=90, minLineLength=int(img_w * 0.12), maxLineGap=15)
    if lines is not None:
        angles = []
        for l in lines:
            x1, y1, x2, y2 = map(int, l.ravel())
            deg = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if abs(deg) < 12.0:
                angles.append(deg)
        if len(angles) >= 6:
            detected_angle = float(np.median(angles))

    # 2. 若水平线不够明显，检测右侧黑色同步块 (Timing Marks) 拟合直线
    if abs(detected_angle) < 0.2:
        right_strip = gray[int(img_h * 0.2):int(img_h * 0.88), int(img_w * 0.85):]
        _, th = cv2.threshold(right_strip, 80, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        centers = []
        for c in contours:
            x, y, bw, bh = cv2.boundingRect(c)
            if int(img_w * 0.02) <= bw <= int(img_w * 0.06) and int(img_h * 0.005) <= bh <= int(img_h * 0.02):
                centers.append((x + bw / 2.0, y + bh / 2.0))
        if len(centers) >= 8:
            centers.sort(key=lambda p: p[1])
            pts = np.array(centers, dtype=np.float32)
            vx, vy, _, _ = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01)
            line_deg = float(np.degrees(np.arctan2(float(vx[0]), float(vy[0]))))
            if abs(line_deg) < 15.0:
                detected_angle = line_deg

    # 3. 角度在显著范围内时执行仿射旋转摆正
    if 0.5 <= abs(detected_angle) <= 15.0:
        center = (img_w / 2.0, img_h / 2.0)
        M = cv2.getRotationMatrix2D(center, detected_angle, 1.0)
        deskewed = cv2.warpAffine(img_bgr, M, (img_w, img_h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
        return deskewed, detected_angle

    return img_bgr, 0.0


def get_chinese_font(size: int = 14, bold: bool = False) -> Any:
    """获取系统中可用的中文字体（确保中文绝不显示为方块乱码）"""
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/PingFang.ttc"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def get_number_font(size: int = 24, bold: bool = True) -> Any:
    """获取纯数字/英文字体"""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return get_chinese_font(size, bold=bold)


def get_font(size: int, bold: bool = False) -> Any:
    """默认获取中文字体"""
    return get_chinese_font(size, bold=bold)


def get_question_geometry(
    q_num: int,
    layout: Dict[str, Any],
    img_w: int,
    img_h: int
) -> Optional[Tuple[int, int, int, int, Dict[str, Tuple[int, int]]]]:
    """根据题号与答题卡几何排版，计算该题在图像上的边界矩形 (x1, y1, x2, y2) 与 A/B/C/D 选项气泡中心坐标

    公考行测标准答题卡题号排布规律：
      7个大行 (Band 0~6)，每个大行 20 题，分 4 列，每列 5 题：
      q = r * 20 + c * 5 + b + 1
      其中:
        r = (q - 1) // 20  (0..6)
        in_band = (q - 1) % 20  (0..19)
        c = in_band // 5   (0..3)
        b = in_band % 5    (0..4)
    """
    bands = layout.get("bands") or DEFAULT_OMR_LAYOUT["bands"]
    cols = layout.get("cols") or DEFAULT_OMR_LAYOUT["cols"]

    r = (q_num - 1) // 20
    if r < 0 or r >= len(bands):
        return None

    in_band = (q_num - 1) % 20
    c = in_band // 5
    b = in_band % 5

    if c >= len(cols):
        return None

    col_xA_norm = layout.get("col_xA_norm") or DEFAULT_OMR_LAYOUT.get("col_xA_norm")
    col0_b56 = layout.get("col0_b56_xA_norm", DEFAULT_OMR_LAYOUT.get("col0_b56_xA_norm", 136.1))
    col0_b56_dx_norm = layout.get("col0_b56_bubble_dx_norm", DEFAULT_OMR_LAYOUT.get("col0_b56_bubble_dx_norm", 34.0))
    col3_b56 = layout.get("col3_b56_xA_norm", DEFAULT_OMR_LAYOUT.get("col3_b56_xA_norm", 727.8))
    bubble_dx_norm = layout.get("bubble_dx_norm") or DEFAULT_OMR_LAYOUT.get("bubble_dx_norm", 29.51)
    col3_b56_dx_norm = layout.get("col3_b56_bubble_dx_norm", DEFAULT_OMR_LAYOUT.get("col3_b56_bubble_dx_norm", 33.33))
    band_first_y_norm = layout.get("band_first_y_norm") or DEFAULT_OMR_LAYOUT.get("band_first_y_norm")
    band_step_y_norm = layout.get("band_step_y_norm") or DEFAULT_OMR_LAYOUT.get("band_step_y_norm")
    col_dy_norm = layout.get("col_dy_norm") or DEFAULT_OMR_LAYOUT.get("col_dy_norm", [0.0, -3.5, -7.0, -8.5])
    skew_k = layout.get("skew_k", DEFAULT_OMR_LAYOUT.get("skew_k", 0.0))

    if band_first_y_norm and r < len(band_first_y_norm) and col_xA_norm and c < len(col_xA_norm):
        base_xA_norm = col_xA_norm[c]
        dx_norm = bubble_dx_norm
        # 三位数题号排版自适应补偿 (Band 5: 101~120 题, Band 6: 121~140 题, 及 Q100)
        # Col 0 (Q101..105, Q121..125): 容纳三位数题号向左平移一个气泡并拉大间距至 49px (34.0‰)
        # Col 3 (Q116..120, Q136..140, Q100): 容纳三位数题号向右平移并拉大间距至 48px (33.33‰)
        if r >= 5:
            if c == 0:
                base_xA_norm = col0_b56
                dx_norm = col0_b56_dx_norm
            elif c == 3:
                base_xA_norm = col3_b56
                dx_norm = col3_b56_dx_norm
            else:
                dx_norm = col3_b56_dx_norm
        elif q_num == 100:
            base_xA_norm = col3_b56
            dx_norm = col3_b56_dx_norm

        xA = int(base_xA_norm * img_w / 1000.0)
        dx = int(dx_norm * img_w / 1000.0)

        # 自适应透视步长与列微补偿
        step_y = band_step_y_norm[r] if (band_step_y_norm and r < len(band_step_y_norm)) else layout.get("q_step_y_norm", 14.32)
        y_base = (band_first_y_norm[r] + b * step_y) * img_h / 1000.0
        col_dy = (col_dy_norm[c] if (col_dy_norm and c < len(col_dy_norm)) else 0.0) * img_h / 1000.0

        xA0 = int(col_xA_norm[0] * img_w / 1000.0)
        cy = int(y_base + col_dy + (xA - xA0) * skew_k)

        q_h_px = int(step_y * img_h / 1000.0)
        y1 = cy - q_h_px // 2
        y2 = cy + q_h_px // 2
        x1 = xA - int(dx * 1.5)
        x2 = xA + int(dx * 3.8)

        bubbles = {
            "A": (xA, cy),
            "B": (xA + dx, cy),
            "C": (xA + 2 * dx, cy),
            "D": (xA + 3 * dx, cy)
        }
    else:
        ymin_b, ymax_b = bands[r]
        xmin_c, xmax_c = cols[c]

        band_h = ymax_b - ymin_b
        q_h = band_h / 5.0

        qy1_norm = ymin_b + b * q_h
        qy2_norm = ymin_b + (b + 1) * q_h
        qx1_norm = xmin_c
        qx2_norm = xmax_c

        x1 = int(qx1_norm * img_w / 1000.0)
        x2 = int(qx2_norm * img_w / 1000.0)
        y1 = int(qy1_norm * img_h / 1000.0)
        y2 = int(qy2_norm * img_h / 1000.0)
        cy = int((y1 + y2) / 2.0)

        w_box = x2 - x1
        bubbles = {
            "A": (int(x1 + w_box * 0.32), cy),
            "B": (int(x1 + w_box * 0.52), cy),
            "C": (int(x1 + w_box * 0.72), cy),
            "D": (int(x1 + w_box * 0.90), cy),
        }

    return (x1, y1, x2, y2, bubbles)


def annotate_user_omr_sheet(
    img_bgr: np.ndarray,
    judged_data: Dict[str, Any],
    grid_layout: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """在用户上传的真实答题卡原图上绘制高保真对错批注、选项订正与成绩印章

    参数：
        - img_bgr: 用户上传答题卡原始图像 (cv2 BGR ndarray)
        - judged_data: omr_judge.judge_omr_sheet 输出的判定结果
        - grid_layout: 视觉模型定位或预估的答题卡空间网格布局
    返回：
        - 批注完成的高清 BGR 图像
    """
    if img_bgr is None or img_bgr.size == 0:
        return generate_annotated_synthetic_omr_sheet(judged_data)

    img_h, img_w = img_bgr.shape[:2]
    annotated = img_bgr.copy()

    # 规范化布局参数：优先合并高精度预设几何矩阵，避免普通粗粒度定位丢失气泡对齐
    merged_layout = dict(DEFAULT_OMR_LAYOUT)
    if grid_layout and isinstance(grid_layout, dict):
        for k, v in grid_layout.items():
            if v is not None and k not in [
                "col_xA_norm", "col0_b56_xA_norm", "col3_b56_xA_norm",
                "col3_b56_bubble_dx_norm", "bubble_dx_norm",
                "band_first_y_norm", "band_step_y_norm", "col_dy_norm", "skew_k"
            ]:
                merged_layout[k] = v
    layout = merged_layout

    # 转为 PIL Image 进行平滑抗锯齿与文字绘制
    img_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    items: List[Dict[str, Any]] = judged_data.get("items", [])
    summary = judged_data.get("summary", {})

    # 1. 逐题遍历并在对应题目位置绘制红绿批注
    for it in items:
        q_num = it.get("q_num", 1)
        status = it.get("status", "unknown")
        student_choice = it.get("student_choice")
        standard_choice = it.get("standard_choice")

        geom = get_question_geometry(q_num, layout, img_w, img_h)
        if not geom:
            continue

        x1, y1, x2, y2, bubbles = geom
        box_w = x2 - x1
        box_h = y2 - y1
        mark_size = max(14, int(box_h * 0.95))

        if status == "correct":
            # 绿色对勾：绘制在该题右侧选项区上方，鲜艳通透
            std_opt = str(standard_choice or student_choice or "A")
            target_pt = bubbles.get(std_opt, (int(x1 + box_w * 0.85), int((y1 + y2) / 2)))
            cx, cy = target_pt[0], target_pt[1] - int(box_h * 0.1)
            pts = renderer.get_checkmark_points(cx, cy, mark_size)
            draw.line(pts, fill=(22, 163, 74), width=max(3, int(box_h * 0.18)), joint="curve")

        elif status == "wrong":
            # 红色叉号：精准绘制在学生错选的选项气泡上
            if student_choice and student_choice in bubbles:
                stu_cx, stu_cy = bubbles[student_choice]
                segs = renderer.get_cross_segments(stu_cx, stu_cy, max(12, int(box_h * 0.75)))
                for p_start, p_end in segs:
                    draw.line([p_start, p_end], fill=(220, 38, 38), width=max(3, int(box_h * 0.16)))

            # 标注标准正确答案（在题目右侧空白区域用醒目红笔标注，严禁在气泡上画圈）
            if standard_choice:
                f_std = get_chinese_font(max(12, int(box_h * 0.54)), bold=True)
                dx_right = bubbles["D"][0] + int(box_h * 0.55)
                cy_d = bubbles["D"][1]
                draw.text((dx_right, cy_d - int(box_h * 0.32)), f"正确: {standard_choice}", font=f_std, fill=(220, 38, 38))

        elif status == "unanswered":
            # 漏涂未填：在右侧清晰标注正确答案（严禁画圈，杜绝遮挡气泡文字）
            if standard_choice:
                f_std = get_chinese_font(max(12, int(box_h * 0.54)), bold=True)
                dx_right = bubbles["D"][0] + int(box_h * 0.55)
                cy_d = bubbles["D"][1]
                draw.text((dx_right, cy_d - int(box_h * 0.32)), f"正确: {standard_choice}", font=f_std, fill=(220, 38, 38))

        elif status == "multiple":
            # 多涂：在中间画大叉，并在右侧标注正确答案（严禁画圈）
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            segs = renderer.get_cross_segments(cx, cy, max(14, int(box_h * 0.85)))
            for p_start, p_end in segs:
                draw.line([p_start, p_end], fill=(220, 38, 38), width=max(3, int(box_h * 0.16)))
            if standard_choice:
                f_std = get_chinese_font(max(12, int(box_h * 0.54)), bold=True)
                dx_right = bubbles["D"][0] + int(box_h * 0.55)
                cy_d = bubbles["D"][1]
                draw.text((dx_right, cy_d - int(box_h * 0.32)), f"正确: {standard_choice}", font=f_std, fill=(220, 38, 38))

    # 2. 在答题卡右上角空白区域绘制具有阅卷质感的行测实得分印章
    stamp_w = int(img_w * 0.31)
    stamp_h = int(img_h * 0.088)
    stamp_x = img_w - stamp_w - int(img_w * 0.05)
    stamp_y = int(img_h * 0.065)

    draw_score_stamp(draw, stamp_x, stamp_y, stamp_w, stamp_h, summary)

    # 转回 BGR numpy 图像
    annotated_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return annotated_bgr


def draw_score_stamp(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    summary: Dict[str, Any]
):
    """绘制高颜值行测阅卷实得分浮水印章"""
    earned = summary.get("total_earned_score", 0.0)
    max_score = summary.get("total_max_score", 100.0)
    acc = summary.get("accuracy_pct", 0.0)
    c_num = summary.get("total_correct", 0)
    w_num = summary.get("total_wrong", 0)
    u_num = summary.get("total_unanswered", 0)
    grade = summary.get("grade_badge", "B")

    # 半透明白色底色卡片，带醒目红笔阅卷边框
    card_box = (x, y, x + w, y + h)
    draw.rounded_rectangle(card_box, radius=14, fill=(255, 255, 255), outline=(220, 38, 38), width=3)

    # 内部红色标题
    f_title = get_chinese_font(max(13, int(h * 0.17)), bold=True)
    draw.text((x + 12, y + 8), "公务员考试·行测阅卷成绩", font=f_title, fill=(185, 28, 28))

    # 大得分数字
    f_score = get_number_font(max(26, int(h * 0.38)), bold=True)
    score_str = f"{earned:g}"
    draw.text((x + 12, y + int(h * 0.26)), score_str, font=f_score, fill=(220, 38, 38))

    # 得分后分数单位
    f_sub = get_chinese_font(max(12, int(h * 0.16)), bold=True)
    try:
        score_w = int(draw.textlength(score_str, font=f_score))
    except Exception:
        score_w = len(score_str) * int(h * 0.22)
    draw.text((x + 16 + score_w, y + int(h * 0.42)), f"/ {max_score:g}分", font=f_sub, fill=(100, 116, 139))

    # 统计数据行
    f_stat = get_chinese_font(max(11, int(h * 0.14)), bold=False)
    stat_line = f"对: {c_num} 题 | 错: {w_num} 题 | 未: {u_num} 题 ({acc}%)"
    draw.text((x + 12, y + int(h * 0.72)), stat_line, font=f_stat, fill=(71, 85, 105))

    # 右侧等级印章徽标
    circle_r = int(h * 0.32)
    circle_cx = x + w - circle_r - 14
    circle_cy = y + int(h * 0.5)
    draw.ellipse(
        (circle_cx - circle_r, circle_cy - circle_r, circle_cx + circle_r, circle_cy + circle_r),
        outline=(220, 38, 38),
        width=3
    )
    f_grade = get_number_font(max(22, int(circle_r * 1.05)), bold=True)
    try:
        gw = int(draw.textlength(grade, font=f_grade))
    except Exception:
        gw = int(circle_r * 0.7)
    draw.text((circle_cx - int(gw / 2), circle_cy - int(circle_r * 0.62)), grade, font=f_grade, fill=(220, 38, 38))


def generate_annotated_synthetic_omr_sheet(
    judged_data: Dict[str, Any],
    preset_id: str = "guokao_135"
) -> np.ndarray:
    """针对纯在线做题（未上传实体照片），自动生成一张标准 A4 真实答题纸并在上面批注对错与答案"""
    img_w = 1440
    img_h = 1980
    bg_color = (255, 255, 255)
    sheet_img = Image.new("RGB", (img_w, img_h), bg_color)
    draw = ImageDraw.Draw(sheet_img)

    preset_titles = {
        "guokao_135": "公务员录用考试·行政职业能力测验答题卡 (副省级/135题)",
        "guokao_130": "公务员录用考试·行政职业能力测验答题卡 (地市级/130题)",
        "shengkao_120": "公务员录用考试·行政职业能力测验答题卡 (省考/120题)",
    }
    title_text = preset_titles.get(preset_id, "公务员录用考试·行政职业能力测验答题卡")

    # 1. 绘制答题卡纸质表头与准考证号区域
    f_header = get_chinese_font(30, bold=True)
    draw.text((img_w // 2 - 340, 50), title_text, font=f_header, fill=(219, 39, 119))

    # 右侧同步时钟定位黑块 (Timing Marks)
    block_x = img_w - 45
    for b_i in range(36):
        by = 220 + b_i * 45
        draw.rectangle((block_x, by, block_x + 28, by + 24), fill=(20, 20, 20))

    # 准考证号与填涂说明框 (仿真实真题卡)
    draw.rectangle((120, 105, 1100, 240), outline=(244, 114, 182), width=2)
    draw.text((150, 130), "准 考 证 号", font=get_chinese_font(20, bold=True), fill=(219, 39, 119))
    draw.text((150, 170), "姓名: __________________", font=get_chinese_font(18), fill=(70, 70, 70))
    draw.text((450, 130), "填涂样例: [A] [■] [C] [D]", font=get_chinese_font(18), fill=(70, 70, 70))
    draw.text((450, 170), "注意事项: 1. 答题前请将姓名及准考证号认真填涂；2. 客观题必须使用 2B 铅笔规范填涂。", font=get_chinese_font(14), fill=(120, 120, 120))

    # 2. 绘制 4 列 × 7 题块客观题网格
    layout = DEFAULT_OMR_LAYOUT
    bands = layout["bands"]
    cols = layout["cols"]

    # 绘制外边框与内部分隔线
    gx1 = int(cols[0][0] * img_w / 1000.0)
    gx2 = int(cols[-1][1] * img_w / 1000.0)
    gy1 = int(bands[0][0] * img_h / 1000.0)
    gy2 = int(bands[-1][1] * img_h / 1000.0)
    draw.rectangle((gx1, gy1, gx2, gy2), outline=(244, 114, 182), width=2)

    f_q_num = get_number_font(16, bold=True)
    f_opt = get_number_font(15, bold=False)

    # 渲染每道题的打印字符与气泡
    for r in range(7):
        by1 = int(bands[r][0] * img_h / 1000.0)
        by2 = int(bands[r][1] * img_h / 1000.0)
        draw.line([(gx1, by2), (gx2, by2)], fill=(244, 114, 182), width=2)

        for c in range(4):
            cx1 = int(cols[c][0] * img_w / 1000.0)
            cx2 = int(cols[c][1] * img_w / 1000.0)
            if c > 0:
                draw.line([(cx1, gy1), (cx1, gy2)], fill=(244, 114, 182), width=1)

            q_step = (by2 - by1) / 5.0
            for b in range(5):
                q_num = r * 20 + c * 5 + b + 1
                qy1 = int(by1 + b * q_step)

                # 打印题号
                draw.text((cx1 + 8, qy1 + int(q_step * 0.2)), f"{q_num}", font=f_q_num, fill=(70, 70, 70))

                # 打印 4 个选项气泡
                w_col = cx2 - cx1
                for o_idx, opt in enumerate(["A", "B", "C", "D"]):
                    ox = int(cx1 + w_col * (0.32 + o_idx * 0.19))
                    oy = int(qy1 + q_step * 0.5)
                    # 绘制气泡方框
                    draw.rectangle((ox - 10, oy - 8, ox + 10, oy + 8), outline=(219, 39, 119), width=1)
                    draw.text((ox - 5, oy - 7), opt, font=f_opt, fill=(219, 39, 119))

    # 3. 将学生的作答填涂为 2B 铅笔黑印
    items: List[Dict[str, Any]] = judged_data.get("items", [])
    for it in items:
        q_num = it.get("q_num", 1)
        student_choice = it.get("student_choice")
        if student_choice and student_choice in "ABCD":
            geom = get_question_geometry(q_num, layout, img_w, img_h)
            if geom:
                _, _, _, _, bubbles = geom
                if student_choice in bubbles:
                    bx, by = bubbles[student_choice]
                    # 仿 2B 铅笔填涂块 (深灰微糙)
                    draw.rectangle((bx - 9, by - 7, bx + 9, by + 7), fill=(45, 50, 55))

    # 转为 numpy 数组并复用 annotate_user_omr_sheet 进行老师红笔绿笔批注
    base_bgr = cv2.cvtColor(np.array(sheet_img), cv2.COLOR_RGB2BGR)
    annotated_bgr = annotate_user_omr_sheet(base_bgr, judged_data, grid_layout=layout)
    return annotated_bgr
