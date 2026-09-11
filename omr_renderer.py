"""公考《行测》选择题答题卡 (OMR) 电子报告与高保真对错矩阵渲染器
生成包含总分印章、五大模块得分率进度、1~135 题答题卡红绿对错网格以及行测专属学情诊断的专业长图报告。
"""

import math
from typing import Dict, Any, List
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import renderer


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取指定大小的中英文字体"""
    if bold:
        return renderer.get_bold_number_font(size)  # type: ignore
    return renderer.get_available_chinese_font(size)  # type: ignore


def render_omr_report_card(
    judged_data: Dict[str, Any],
    exam_title: str = "公务员考试《行测》客观题答题卡诊断报告"
) -> np.ndarray:
    """渲染生成专业的行测电子答题卡全景分析报告图 (返回 BGR numpy ndarray)

    参数：
        judged_data: omr_judge.judge_omr_sheet 返回的完整结构，包含 summary, section_results, diagnosis, items
        exam_title: 试卷标题
    """
    summary = judged_data.get("summary", {})
    section_results = judged_data.get("section_results", [])
    diagnosis = judged_data.get("diagnosis", {})
    items: List[Dict[str, Any]] = judged_data.get("items", [])

    total_q = summary.get("total_questions", len(items))

    # 1. 动态计算画幅尺寸
    img_w = 1200
    # 顶部头部高约 260px，模块区域约 200px
    # 题卡区域：每行排 5 列，每列一个题块。135 题约 27 行，每行高 50px -> 1350px
    # 底部学情诊断约 320px
    num_cols = 5
    num_rows = math.ceil(total_q / num_cols)
    grid_h = num_rows * 56 + 60
    img_h = 300 + 210 + grid_h + 340

    bg_color = (248, 250, 252)  # 优雅浅蓝灰 #F8FAFC
    card_img = Image.new("RGB", (img_w, img_h), bg_color)
    draw = ImageDraw.Draw(card_img)

    font_title = get_font(34, bold=True)
    font_subtitle = get_font(18, bold=False)
    font_score_big = get_font(52, bold=True)
    font_label = get_font(20, bold=False)
    font_label_bold = get_font(20, bold=True)
    font_q_num = get_font(18, bold=True)
    font_q_ans = get_font(17, bold=False)
    font_tip = get_font(18, bold=False)

    # ----------------------------------------------------
    # 区域 1: 顶部标题与总分卡片 (y: 24 ~ 280)
    # ----------------------------------------------------
    header_box = (30, 24, img_w - 30, 280)
    draw.rounded_rectangle(header_box, radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # 装饰渐变彩条
    draw.rounded_rectangle((30, 24, img_w - 30, 32), radius=4, fill=(59, 130, 246))

    # 标题与时间
    draw.text((60, 50), exam_title, fill=(15, 23, 42), font=font_title)
    draw.text((60, 96), f"交卷用时: {summary.get('time_str', '--')}  |  总题量: {total_q} 题  |  答对: {summary.get('total_correct', 0)} 题  |  做错: {summary.get('total_wrong', 0)} 题  |  未填: {summary.get('total_unanswered', 0)} 题", fill=(100, 116, 139), font=font_subtitle)

    # 左侧大分值展示
    earned = summary.get("total_earned_score", 0.0)
    max_score = summary.get("total_max_score", 100.0)
    acc = summary.get("accuracy_pct", 0.0)

    score_str = f"{earned:g}"
    draw.text((60, 140), "行测实得分", fill=(71, 85, 105), font=font_label)
    draw.text((60, 172), score_str, fill=(37, 99, 235), font=font_score_big)
    draw.text((60 + len(score_str) * 32 + 10, 204), f"/ {max_score:g} 满分", fill=(148, 163, 184), font=font_label_bold)

    # 核心指标胶囊
    stat_capsules = [
        ("正确率", f"{acc}%", (16, 185, 129)),
        ("做对", f"{summary.get('total_correct', 0)} 题", (37, 99, 235)),
        ("做错", f"{summary.get('total_wrong', 0)} 题", (239, 68, 68)),
        ("未填", f"{summary.get('total_unanswered', 0)} 题", (156, 163, 175)),
    ]
    start_cap_x = 450
    for idx, (lbl, val, col) in enumerate(stat_capsules):
        cx = start_cap_x + idx * 135
        cy = 160
        draw.rounded_rectangle((cx, cy, cx + 120, cy + 86), radius=12, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
        draw.text((cx + 15, cy + 12), lbl, fill=(100, 116, 139), font=get_font(15))
        draw.text((cx + 15, cy + 42), val, fill=col, font=get_font(24, bold=True))

    # 右侧等级印章
    grade_level = summary.get("grade_level", "良好")
    grade_badge = summary.get("grade_badge", "B")
    stamp_cx = img_w - 120
    stamp_cy = 195
    r = 52
    draw.ellipse((stamp_cx - r, stamp_cy - r, stamp_cx + r, stamp_cy + r), outline=(220, 38, 38), width=3)
    draw.ellipse((stamp_cx - r + 5, stamp_cy - r + 5, stamp_cx + r - 5, stamp_cy + r - 5), outline=(220, 38, 38), width=1)
    draw.text((stamp_cx - 26, stamp_cy - 36), grade_badge, fill=(220, 38, 38), font=get_font(36, bold=True))
    draw.text((stamp_cx - 24, stamp_cy + 8), grade_level, fill=(220, 38, 38), font=get_font(16, bold=True))

    # ----------------------------------------------------
    # 区域 2: 行测五大模块得分看板 (y: 295 ~ 485)
    # ----------------------------------------------------
    sec_box = (30, 295, img_w - 30, 485)
    draw.rounded_rectangle(sec_box, radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((50, 312), "📊 各模块实战得分与正确率分解", fill=(15, 23, 42), font=get_font(22, bold=True))

    if section_results:
        sec_count = len(section_results)
        col_w = (img_w - 100) / max(sec_count, 1)
        for idx, sec in enumerate(section_results):
            sx = 50 + idx * col_w
            sy = 356
            s_name = sec.get("name", f"模块{idx+1}")
            s_acc = sec.get("accuracy_pct", 0.0)
            s_earned = sec.get("earned_score", 0.0)
            s_max = sec.get("max_score", 0.0)
            s_q_range = f"{sec.get('start_q')}-{sec.get('end_q')}题 ({sec.get('total_q')}题)"

            # 背景小块
            draw.rounded_rectangle((sx, sy, sx + col_w - 12, sy + 105), radius=10, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
            draw.text((sx + 10, sy + 8), s_name[:7], fill=(30, 41, 59), font=get_font(16, bold=True))
            draw.text((sx + 10, sy + 30), s_q_range, fill=(148, 163, 184), font=get_font(12))

            # 正确率与得分
            acc_color = (16, 185, 129) if s_acc >= 75 else ((234, 88, 12) if s_acc >= 60 else (220, 38, 38))
            draw.text((sx + 10, sy + 48), f"{s_earned:g}/{s_max:g}分", fill=(37, 99, 235), font=get_font(18, bold=True))
            draw.text((sx + 10, sy + 74), f"正确率 {s_acc}%", fill=acc_color, font=get_font(14, bold=True))

    # ----------------------------------------------------
    # 区域 3: 1~N 题答题卡矩阵 (y: 500 ~ 500 + grid_h)
    # ----------------------------------------------------
    grid_y_start = 500
    draw.rounded_rectangle((30, grid_y_start, img_w - 30, grid_y_start + grid_h), radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((50, grid_y_start + 18), "📝 电子答题卡全卷填涂与对错映射 (绿色对勾 ✓ / 红色错题 ➔ 正确选项 / 灰色未填)", fill=(15, 23, 42), font=get_font(20, bold=True))

    item_map = {it.get("q_num"): it for it in items}

    # 每列宽度
    cell_w = (img_w - 100) / num_cols
    cell_h = 46

    for q_idx in range(1, total_q + 1):
        col = (q_idx - 1) % num_cols
        row = (q_idx - 1) // num_cols

        cx = 50 + col * cell_w
        cy = grid_y_start + 60 + row * 52

        it = item_map.get(q_idx, {})
        stu = it.get("student_choice", "未涂")
        std = it.get("standard_choice", "")
        status = it.get("status", "unknown")

        # 样式定义
        if status == "correct":
            box_bg = (236, 253, 245)      # 浅绿
            box_border = (167, 243, 208)  # 翠绿边框
            text_col = (5, 150, 105)       # 深绿
            display_txt = f"{stu} ✓"
        elif status == "unanswered":
            box_bg = (248, 250, 252)      # 浅灰
            box_border = (203, 213, 225)
            text_col = (100, 116, 139)
            display_txt = f"⚪➔{std}" if std else "⚪"
        elif status == "multiple":
            box_bg = (255, 241, 242)      # 浅红
            box_border = (254, 205, 211)
            text_col = (225, 29, 72)
            display_txt = f"多涂➔{std}" if std else "多涂"
        else:
            # 错题
            box_bg = (254, 242, 242)      # 浅红
            box_border = (254, 202, 202)
            text_col = (220, 38, 38)
            display_txt = f"{stu}➔{std}" if std else f"{stu} ✗"

        # 绘制单个题项小卡
        item_box = (cx, cy, cx + cell_w - 10, cy + cell_h)
        draw.rounded_rectangle(item_box, radius=8, fill=box_bg, outline=box_border, width=1)

        # 题号
        q_label = f"{q_idx:02d}." if q_idx < 100 else f"{q_idx}."
        draw.text((cx + 10, cy + 12), q_label, fill=(30, 41, 59), font=font_q_num)

        # 选项与对比
        draw.text((cx + 56, cy + 13), display_txt, fill=text_col, font=font_q_ans)

    # ----------------------------------------------------
    # 区域 4: 底部行测学情诊断与提分锦囊
    # ----------------------------------------------------
    diag_y_start = grid_y_start + grid_h + 18
    draw.rounded_rectangle((30, diag_y_start, img_w - 30, diag_y_start + 290), radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((50, diag_y_start + 18), "💡 行测专属学情诊断与备考突破锦囊", fill=(15, 23, 42), font=get_font(22, bold=True))

    weakest = diagnosis.get("weakest_section", "无明显短板")
    strongest = diagnosis.get("strongest_section", "均衡")
    draw.text((50, diag_y_start + 56), f"• 核心薄弱短板: {weakest}", fill=(220, 38, 38), font=get_font(18, bold=True))
    draw.text((500, diag_y_start + 56), f"• 稳定拿分阵地: {strongest}", fill=(16, 185, 129), font=get_font(18, bold=True))

    tips = diagnosis.get("actionable_tips", [])
    for idx, tip in enumerate(tips[:4]):
        ty = diag_y_start + 96 + idx * 44
        # 装饰小圆点
        draw.ellipse((52, ty + 6, 60, ty + 14), fill=(37, 99, 235))
        draw.text((68, ty), tip, fill=(51, 65, 85), font=font_tip)

    # 转换为 BGR numpy ndarray
    rgb_arr = np.array(card_img)
    bgr_arr = rgb_arr[:, :, ::-1].copy()
    return bgr_arr
