"""批改标注渲染模块
负责将批改结果（绿色对勾 ✓、红色叉号 ✗、右下角统计面板、等级印章）绘制在展平图以及原始拍照图上。
"""

import os
from typing import Dict, Any, List, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def get_available_chinese_font(size: int = 24):
    """获取系统中可用的中文字体"""
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
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


def get_checkmark_points(cx: float, cy: float, size: float) -> List[Tuple[float, float]]:
    """生成对勾的三个折线顶点：[左起点, 转折低点, 右上顶点]"""
    p1 = (cx - size * 0.45, cy)
    p2 = (cx - size * 0.10, cy + size * 0.42)
    p3 = (cx + size * 0.55, cy - size * 0.45)
    return [p1, p2, p3]


def get_cross_segments(cx: float, cy: float, size: float) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """生成叉号的两条线段"""
    r = size * 0.38
    seg1 = ((cx - r, cy - r), (cx + r, cy + r))
    seg2 = ((cx - r, cy + r), (cx + r, cy - r))
    return [seg1, seg2]


def get_bold_number_font(size: int = 26):
    """获取系统中可用的粗体数字英文字体"""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return get_available_chinese_font(size)


def render_on_warped_sheet(
    warped_bgr: np.ndarray,
    row_bounds: List[Tuple[int, int]],
    col_bounds: List[Tuple[int, int]],
    items: List[Dict[str, Any]],
    stats: Dict[str, Any],
    sheet_type: str = "mul"
) -> np.ndarray:
    """在标准化展平图上直接绘制批改结果（对勾、叉号、右上角红字正确答案、底部空白区统计卡片与备注）。

    返回：
        标注完成的 BGR numpy 图像
    """
    h, w = warped_bgr.shape[:2]
    # 底部扩展 320 像素作为页脚区域，放置备注和统计结果卡片，避免遮挡最后三行题目
    footer_h = 320
    padded_bgr = cv2.copyMakeBorder(warped_bgr, 0, footer_h, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    img_rgb = cv2.cvtColor(padded_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    cell_h = h / max(len(row_bounds), 21)
    ans_font = get_bold_number_font(26)

    # 1. 遍历每道题并绘制对勾或叉号及错误订正答案
    for it in items:
        row_idx = it.get("row_num", 1)  # 1-based index (1~20)
        col_idx = it.get("col_idx", 3)
        is_correct = it.get("is_correct")

        if row_idx < len(row_bounds) and col_idx < len(col_bounds):
            y1, y2 = row_bounds[row_idx]
            x1, x2 = col_bounds[col_idx]
        else:
            y1 = int(row_idx * cell_h)
            y2 = int((row_idx + 1) * cell_h)
            x1 = int(col_idx * (w / 11))
            x2 = int((col_idx + 1) * (w / 11))

        cell_w_cur = x2 - x1
        cell_h_cur = y2 - y1

        if is_correct is True:
            # 绿色对勾：绘制在作答单元格中右侧，预留充足安全边距防书页微弯压线
            cx = x1 + cell_w_cur * 0.58
            cy = y1 + cell_h_cur * 0.42
            mark_size = cell_h_cur * 0.36
            pts = get_checkmark_points(cx, cy, mark_size)
            draw.line(pts, fill=(34, 187, 51), width=4, joint="curve")
        elif it.get("status") == "wrong":
            # 红色叉号：绘制在作答中右侧
            cx = x1 + cell_w_cur * 0.58
            cy = y1 + cell_h_cur * 0.50
            mark_size = cell_h_cur * 0.30
            segs = get_cross_segments(cx, cy, mark_size)
            for p_start, p_end in segs:
                draw.line([p_start, p_end], fill=(238, 34, 34), width=4)

            # 在单元格上方居中偏右标注标准正确答案，预留安全间距
            exp_val = it.get("expected")
            if exp_val is not None:
                exp_str = str(exp_val)
                bbox = draw.textbbox((0, 0), exp_str, font=ans_font)
                tw = bbox[2] - bbox[0]
                tx = min(x1 + int(cell_w_cur * 0.48), x2 - tw - 24)
                ty = y1 + 5
                draw.text((tx, ty), exp_str, font=ans_font, fill=(238, 34, 34))

    # 2. 在底部留白区左侧绘制标准备注信息
    font_note_title = get_available_chinese_font(20)
    font_note_body = get_available_chinese_font(18)
    note_x, note_y = 60, h + 30
    draw.text((note_x, note_y), "备注：", font=font_note_title, fill=(50, 50, 50))
    if "div" in sheet_type or "除法" in sheet_type:
        draw.text((note_x + 10, note_y + 35), "（1）三位数加减，口算（20 组，2 分钟）", font=font_note_body, fill=(80, 80, 80))
        draw.text((note_x + 10, note_y + 70), "（2）多位数÷两位数，口算（20 组，2 分钟）", font=font_note_body, fill=(80, 80, 80))
        draw.text((note_x + 10, note_y + 105), "（3）多位数÷三位数，口算（20 组，2.5 分钟）", font=font_note_body, fill=(80, 80, 80))
    else:
        draw.text((note_x + 10, note_y + 35), "（1）两位数×一位数，口算（40 组，1.5 分钟）", font=font_note_body, fill=(80, 80, 80))
        draw.text((note_x + 10, note_y + 70), "（2）两位数加减，口算（20 组，2 分钟）", font=font_note_body, fill=(80, 80, 80))

    # 3. 在底部留白区右侧绘制批改结果统计面板（完全避免遮挡表格题目）
    card_w = 480
    card_h = 240
    card_x = w - card_w - 60
    card_y = h + 25
    draw_summary_card_on_pil(pil_img, stats, scale_factor=1.0, pos=(card_x, card_y))

    result_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result_bgr


def render_on_original_sheet(
    orig_bgr: np.ndarray,
    M_inv: np.ndarray,
    row_bounds: List[Tuple[int, int]],
    col_bounds: List[Tuple[int, int]],
    items: List[Dict[str, Any]],
    stats: Dict[str, Any],
    corners: Optional[np.ndarray] = None
) -> np.ndarray:
    """在原始拍照图（倾斜照片）上绘制带透视贴合的批改标记（绿勾、红叉、红字正确答案）与结果卡片。

    采用高保真 RGBA 图层逆透视投影，使所有批改笔迹自然贴合手机拍照的透视角度。

    返回：
        标注完成的 BGR 图像
    """
    orig_h, orig_w = orig_bgr.shape[:2]

    # 1. 在标准化展平坐标系 (1600x2200) 下创建透明 RGBA 标注图层
    w, h = 1600, 2200
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    ans_font = get_bold_number_font(26)

    for it in items:
        row_idx = it.get("row_num", 1)
        col_idx = it.get("col_idx", 3)
        is_correct = it.get("is_correct")

        if row_idx < len(row_bounds) and col_idx < len(col_bounds):
            y1, y2 = row_bounds[row_idx]
            x1, x2 = col_bounds[col_idx]
        else:
            continue

        cell_w_cur = x2 - x1
        cell_h_cur = y2 - y1

        if is_correct is True:
            # 绿色对勾
            cx = x1 + cell_w_cur * 0.58
            cy = y1 + cell_h_cur * 0.42
            mark_size = cell_h_cur * 0.36
            pts = get_checkmark_points(cx, cy, mark_size)
            draw.line(pts, fill=(34, 187, 51, 255), width=4, joint="curve")
        elif it.get("status") == "wrong":
            # 红色叉号
            cx = x1 + cell_w_cur * 0.58
            cy = y1 + cell_h_cur * 0.50
            mark_size = cell_h_cur * 0.30
            segs = get_cross_segments(cx, cy, mark_size)
            for seg in segs:
                draw.line(list(seg), fill=(238, 34, 34, 255), width=4)

            # 右上角标注红色标准正确答案
            exp_val = it.get("expected")
            if exp_val is not None:
                exp_str = str(exp_val)
                bbox = draw.textbbox((0, 0), exp_str, font=ans_font)
                tw = bbox[2] - bbox[0]
                tx = min(x1 + int(cell_w_cur * 0.48), x2 - tw - 24)
                ty = y1 + 5
                draw.text((tx, ty), exp_str, font=ans_font, fill=(238, 34, 34, 255))

    # 2. 将 RGBA 标注图层通过透视逆矩阵 M_inv 投影到原图尺寸
    overlay_np = np.array(overlay)
    overlay_bgra = cv2.cvtColor(overlay_np, cv2.COLOR_RGBA2BGRA)
    warped_overlay = cv2.warpPerspective(overlay_bgra, M_inv, (orig_w, orig_h), flags=cv2.INTER_LANCZOS4)

    # 3. 与原始倾斜照片进行平滑 Alpha 混合
    alpha = (warped_overlay[:, :, 3].astype(float) / 255.0)[:, :, np.newaxis]
    blended_bgr = (orig_bgr.astype(float) * (1.0 - alpha) + warped_overlay[:, :, :3].astype(float) * alpha).astype(np.uint8)

    # 4. 在原图表格下方的空白区绘制正向的批改统计卡片
    img_rgb = cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)
    pil_final = Image.fromarray(img_rgb)
    card_scale = max(0.65, min(1.0, orig_w / 2000.0))
    box_w = int(480 * card_scale)
    box_h = int(240 * card_scale)

    target_pos = None
    if corners is not None and len(corners) == 4:
        # corners[2] 为表格右下角, corners[3] 为表格左下角
        br_x, br_y = corners[2]
        bl_x, bl_y = corners[3]
        tbl_bottom = max(br_y, bl_y)
        if orig_h - tbl_bottom >= box_h + 30:
            # 原图下方留白充足，放置在表格下方偏右位置
            pos_x = max(10, min(int(br_x - box_w), orig_w - box_w - 20))
            pos_y = int(tbl_bottom + 25)
            target_pos = (pos_x, pos_y)

    draw_summary_card_on_pil(
        pil_final,
        stats,
        scale_factor=card_scale,
        pos=target_pos,
        bottom_right_margin=(40, 50)
    )

    result_bgr = cv2.cvtColor(np.array(pil_final), cv2.COLOR_RGB2BGR)
    return result_bgr


def draw_summary_card_on_pil(
    pil_img: Image.Image,
    stats: Dict[str, Any],
    scale_factor: float = 1.0,
    bottom_right_margin: Tuple[int, int] = (40, 40),
    pos: Optional[Tuple[int, int]] = None
):
    """在 PIL 图像上绘制标准批改结果卡片。

    参数：
        pil_img: PIL 图像
        stats: 统计数据
        scale_factor: 缩放因子
        bottom_right_margin: 当 pos 未指定时，相对于右下角的边距
        pos: 指定的 (x0, y0) 绝对左上角坐标
    """
    draw = ImageDraw.Draw(pil_img)
    w, h = pil_img.size

    box_w = int(480 * scale_factor)
    box_h = int(240 * scale_factor)

    if pos is not None:
        x0, y0 = pos
    else:
        mx, my = int(bottom_right_margin[0] * scale_factor), int(bottom_right_margin[1] * scale_factor)
        x0 = w - box_w - mx
        y0 = h - box_h - my

    x1 = x0 + box_w
    y1 = y0 + box_h

    # 半透明白色背景与深灰边框
    draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255), outline=(100, 100, 100), width=max(2, int(2 * scale_factor)))

    font_title = get_available_chinese_font(int(22 * scale_factor))
    font_body = get_available_chinese_font(int(20 * scale_factor))
    font_grade_lbl = get_available_chinese_font(int(22 * scale_factor))

    # Arial / 罗马大字体用于等级 A+
    font_grade = None
    arial_candidates = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for ap in arial_candidates:
        if os.path.exists(ap):
            try:
                font_grade = ImageFont.truetype(ap, int(74 * scale_factor))
                break
            except Exception:
                pass
    if font_grade is None:
        font_grade = get_available_chinese_font(int(74 * scale_factor))

    pad_x = int(22 * scale_factor)
    pad_y = int(16 * scale_factor)
    line_spacing = int(35 * scale_factor)

    # 1. 标题
    draw.text((x0 + pad_x, y0 + pad_y), "批改结果 (自动批改)", font=font_title, fill=(0, 0, 0))

    # 2. 总题数
    cur_y = y0 + pad_y + int(38 * scale_factor)
    draw.text((x0 + pad_x, cur_y), f"总题数: {stats.get('total', 0)}", font=font_body, fill=(0, 0, 0))

    # 3. 正确数
    cur_y += line_spacing
    acc = stats.get("accuracy_pct", 0.0)
    draw.text((x0 + pad_x, cur_y), f"正确: {stats.get('correct', 0)} ({acc}%)", font=font_body, fill=(34, 175, 40))

    # 4. 错误数
    cur_y += line_spacing
    draw.text((x0 + pad_x, cur_y), f"错误: {stats.get('wrong', 0)}", font=font_body, fill=(238, 34, 34))

    # 5. 待确认
    cur_y += line_spacing
    draw.text((x0 + pad_x, cur_y), f"待确认: {stats.get('unknown', 0)}", font=font_body, fill=(20, 90, 220))

    # 6. 用时
    cur_y += line_spacing
    time_str = stats.get("time_str", "23分18秒")
    draw.text((x0 + pad_x, cur_y), f"用时: {time_str}", font=font_body, fill=(30, 30, 30))

    # 7. 等级 A+
    grade_x = x0 + int(310 * scale_factor)
    draw.text((grade_x, y0 + pad_y + int(38 * scale_factor)), "等级:", font=font_grade_lbl, fill=(238, 34, 34))
    grade = stats.get("grade_level", "A+")
    draw.text((grade_x + int(15 * scale_factor), y0 + pad_y + int(75 * scale_factor)), grade, font=font_grade, fill=(238, 34, 34))
