"""公考速算练习册自动批改系统命令行主入口
实现对手机拍摄练习册的自动定位、透视矫正、多模态智能识别、精准数学判分，
并将批改勾叉、统计卡片高保真标注在原图与展平图上。
"""

import os
import sys
import argparse
import json
from typing import Optional, Dict, Any
import cv2
import numpy as np

# 确保当前目录在 sys.path 中
cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

import cv_detector
import vision_ocr
import math_judge
import renderer


def process_sheet(
    orig_img: np.ndarray,
    base_name: str,
    output_dir: str = "./output",
    time_str: str = "23分18秒",
    model: Optional[str] = None,
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """处理单张试卷的完整批改流水线并返回结构化数据与图片路径"""
    os.makedirs(output_dir, exist_ok=True)
    h, w = orig_img.shape[:2]
    print(f"[1/5] 原始图片加载完成 (尺寸: {w}x{h})")

    # 2. 表格角点检测与透视校正
    corners = cv_detector.detect_table_corners(orig_img)
    warped_img, _M, M_inv = cv_detector.warp_table(orig_img, corners, target_w=1600, target_h=2200)
    row_bounds, col_bounds = cv_detector.detect_grid_cells(warped_img, total_rows=21, total_cols=11)
    print(f"[2/5] 表格透视矫正与网格分割完成 (检测到 {len(row_bounds)} 行, {len(col_bounds)} 列)")

    # 3. 视觉模型识别题目与学生作答
    print(f"[3/5] 正在调用多模态视觉模型提取题目与手写答案...")
    ocr_res = vision_ocr.recognize_sheet_table(
        warped_img,
        model=model,
        base_url=api_base_url,
        api_key=api_key
    )
    sheet_title = ocr_res.get("sheet_title", "速算练习")
    items_raw = ocr_res.get("items", [])
    print(f"      识别到卷面标题: 《{sheet_title}》, 题目数量: {len(items_raw)}")

    # 4. 精确数学核算与成绩评定
    print(f"[4/5] 正在执行精准数学规则核算与判分...")
    judged_items = []
    for item in items_raw:
        res = math_judge.judge_item(
            item.get("op_type", ""),
            item.get("a", 0),
            item.get("b", 0),
            item.get("student_ans")
        )
        judged_items.append({**item, **res})

    report = math_judge.grade_sheet(judged_items, custom_time_str=time_str)

    # 5. 高保真渲染与导出
    print(f"[5/5] 正在生成标注图层 (原图标注与展平图标注)...")
    detected_type = ocr_res.get("detected_type", "mul_add_sub")
    scan_annotated = renderer.render_on_warped_sheet(
        warped_img, row_bounds, col_bounds, judged_items, report, sheet_type=detected_type
    )
    scan_path = os.path.join(output_dir, f"{base_name}_annotated_scan.jpg")
    cv2.imwrite(scan_path, scan_annotated)

    orig_annotated = renderer.render_on_original_sheet(
        orig_img, M_inv, row_bounds, col_bounds, judged_items, report, corners=corners
    )
    orig_path = os.path.join(output_dir, f"{base_name}_annotated_original.jpg")
    cv2.imwrite(orig_path, orig_annotated)

    # 保存 JSON 结果明细
    json_path = os.path.join(output_dir, f"{base_name}_report.json")
    result_data = {
        "title": sheet_title,
        "summary": {
            "total": report["total"],
            "correct": report["correct"],
            "wrong": report["wrong"],
            "unknown": report["unknown"],
            "accuracy_pct": report["accuracy_pct"],
            "grade_level": report["grade_level"],
            "time_str": report["time_str"]
        },
        "diagnosis": report.get("diagnosis", {}),
        "items": judged_items,
        "scan_path": scan_path,
        "orig_path": orig_path,
        "json_path": json_path
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return result_data


def grade_image(
    image_path: str,
    output_dir: str = "./output",
    time_str: str = "23分18秒",
    model: Optional[str] = None,
    api_base_url: Optional[str] = None,
    api_key: Optional[str] = None
):
    """端到端批改入口函数"""
    if not os.path.exists(image_path):
        print(f"错误: 找不到输入图片文件: {image_path}", file=sys.stderr)
        return False

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    print(f"==================================================")
    print(f" 开始批改试卷: {image_path}")
    print(f"==================================================")

    orig_img = cv2.imread(image_path)
    if orig_img is None:
        print(f"错误: 无法读取图像: {image_path}", file=sys.stderr)
        return False

    result_data = process_sheet(
        orig_img,
        base_name,
        output_dir=output_dir,
        time_str=time_str,
        model=model,
        api_base_url=api_base_url,
        api_key=api_key
    )
    report = result_data["summary"]
    sheet_title = result_data["title"]
    judged_items = result_data["items"]
    scan_path = result_data["scan_path"]
    orig_path = result_data["orig_path"]
    json_path = result_data["json_path"]

    # 终端打印精美摘要
    diag = result_data.get("diagnosis", {})
    print("\n" + "=" * 54)
    print("                批 改 结 果 摘 要")
    print("=" * 54)
    print(f" 试卷标题 : {sheet_title}")
    print(f" 总 题 数 : {report['total']}")
    print(f" 正 确 数 : {report['correct']} ({report['accuracy_pct']}%)")
    print(f" 错 误 数 : {report['wrong']}")
    print(f" 待 确 认 : {report['unknown']}")
    print(f" 完成用时 : {report['time_str']}")
    print(f" 综合评级 : {report['grade_level']}")
    if diag.get("primary_weakness"):
        print(f" 学情诊断 : {diag['primary_weakness']}")
    if diag.get("speed_advice"):
        print(f" 速度画像 : {diag['speed_advice']}")
    print("-" * 54)

    if report['wrong'] > 0:
        print(" 错题明细与智能归因分析:")
        for it in judged_items:
            if it.get("is_correct") is False and it.get("status") != "unknown":
                op_map = {"mul": "×", "add": "+", "sub": "-", "div1": "÷", "div2": "÷"}
                op_sym = op_map.get(it.get("op_type"), it.get("op_type"))
                err_label = f"[{it.get('error_name', '计算偏差')}]"
                print(f"  • 第 {it.get('row_num', '?')} 行 第 {it.get('col_idx', '?')} 列 {err_label}: "
                      f"{it.get('a')} {op_sym} {it.get('b')} = 标准答案 {it.get('expected')}, "
                      f"学生作答: {it.get('student_raw')}")
                if it.get("diagnosis"):
                    print(f"    ↳ 错因分析: {it.get('diagnosis')}")
                if it.get("advice"):
                    print(f"    💡 提分建议: {it.get('advice')}")
        print("-" * 54)

    if diag.get("actionable_tips"):
        print(" 🎯 专属提分锦囊:")
        for tip in diag["actionable_tips"]:
            print(f"  • {tip}")
        print("-" * 54)

    print(f" 结果保存:")
    print(f"  - 扫描展平标注图 : {scan_path}")
    print(f"  - 原始照片标注图 : {orig_path}")
    print(f"  - 完整数据报告   : {json_path}")
    print("=" * 54 + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(description="公考速算练习册自动批改程序")
    parser.add_argument("image_path", help="待批改的手机拍照或扫描试卷图片路径")
    parser.add_argument("--output-dir", default="./output", help="标注图片输出目录 (默认: ./output)")
    parser.add_argument("--time-str", default="23分18秒", help="作答用时描述 (默认: 23分18秒)")
    parser.add_argument("--model", default=None, help="指定多模态视觉模型名称")
    parser.add_argument("--base-url", default=None, help="自定义多模态大模型 API Base URL")
    parser.add_argument("--api-key", default=None, help="自定义多模态大模型 API Key")

    args = parser.parse_args()
    success = grade_image(
        image_path=args.image_path,
        output_dir=args.output_dir,
        time_str=args.time_str,
        model=args.model,
        api_base_url=args.base_url,
        api_key=args.api_key
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
