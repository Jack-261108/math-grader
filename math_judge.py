"""公考速算精准数学核算与判题引擎
提供各种公考速算题型的理论标准答案计算、学生手写答案与标准答案的比对判分、
总成绩统计分析（总题数、正确数、错误数、正确率、用时、等级评定等）。
"""

from typing import Dict, Any, List, Optional


def calculate_expected(op_type: str, a: int, b: int) -> int:
    """计算各题型的标准答案。

    op_type 支持：
        - "mul" / "乘法" / "A×B": A * B
        - "add" / "加法" / "A+B": A + B
        - "sub" / "减法" / "A-B": A - B
        - "div1" / "商首位" / "A÷B(首位)": A // B 的最高位数字
        - "div2" / "商前两位" / "A÷B(首两位)": A // B 的前两位有效数字
    """
    op = op_type.lower().strip()
    if "mul" in op or "×" in op or "*" in op or "乘" in op:
        return a * b
    elif "add" in op or "+" in op or "加" in op:
        return a + b
    elif "sub" in op or "-" in op or "减" in op:
        return a - b
    elif "首两位" in op or "前两位" in op or "div2" in op:
        if b == 0:
            return 0
        quotient = a // b
        q_str = str(quotient)
        return int(q_str[:2]) if len(q_str) >= 2 else quotient
    elif "首位" in op or "div1" in op or "商" in op:
        if b == 0:
            return 0
        quotient = a // b
        q_str = str(quotient)
        return int(q_str[0]) if len(q_str) >= 1 else 0
    else:
        # 默认回退加法
        return a + b


def clean_student_answer(ans_str: Optional[str]) -> Optional[int]:
    """清洗学生手写识别文本，提取整数数值"""
    if ans_str is None:
        return None
    s = str(ans_str).strip().replace(" ", "").replace(",", "").replace("，", "")
    # 移除可能误识的符号或对勾叉号
    s = s.replace("✓", "").replace("✔", "").replace("✗", "").replace("✘", "").replace("X", "").replace("x", "")
    if not s:
        return None
    # 提取负号和数字
    is_neg = s.startswith("-") or s.startswith("一")
    digits = "".join([c for c in s if c.isdigit()])
    if not digits:
        return None
    val = int(digits)
    return -val if is_neg else val


def judge_item(op_type: str, a: int, b: int, student_raw: Optional[str]) -> Dict[str, Any]:
    """判定单个题目的作答情况。

    返回：
        dict 包含：
            - expected: 标准答案
            - student_val: 解析出的学生答案数值 (int 或 None)
            - is_correct: True / False / None (None 表示未作答或无法识别)
            - status: "correct" / "wrong" / "unknown"
    """
    expected = calculate_expected(op_type, a, b)
    student_val = clean_student_answer(student_raw)

    if student_val is None:
        return {
            "expected": expected,
            "student_raw": student_raw,
            "student_val": None,
            "is_correct": None,
            "status": "unknown"
        }

    # 精确匹配
    if student_val == expected:
        is_correct = True
    elif "-" in op_type or "减" in op_type:
        # 特别考量：部分速算场景如学生写的是差额绝对值 |A - B| 或带正号
        if student_val == abs(expected):
            is_correct = True
        else:
            is_correct = False
    else:
        is_correct = False

    return {
        "expected": expected,
        "student_raw": student_raw,
        "student_val": student_val,
        "is_correct": is_correct,
        "status": "correct" if is_correct else "wrong"
    }


def grade_sheet(parsed_items: List[Dict[str, Any]], custom_time_str: str = "23分18秒") -> Dict[str, Any]:
    """汇总整张练习卷的批改成绩。

    返回：
        dict 包含：
            - total: 总题数
            - correct: 正确题数
            - wrong: 错误题数
            - unknown: 待确认数
            - accuracy_pct: 正确率百分比（如 93.3）
            - grade_level: 等级（A+ / A / B / C / D）
            - time_str: 用时描述
            - items: 带有判题结果的完整列表
    """
    total = len(parsed_items)
    correct = sum(1 for item in parsed_items if item.get("is_correct") is True)
    unknown = sum(1 for item in parsed_items if item.get("status") == "unknown")
    wrong = total - correct - unknown

    answered = total - unknown
    accuracy_pct = round((correct / answered * 100.0), 1) if answered > 0 else 0.0

    if accuracy_pct >= 90.0:
        grade_level = "A+"
    elif accuracy_pct >= 80.0:
        grade_level = "A"
    elif accuracy_pct >= 70.0:
        grade_level = "B"
    elif accuracy_pct >= 60.0:
        grade_level = "C"
    else:
        grade_level = "D"

    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "unknown": unknown,
        "accuracy_pct": accuracy_pct,
        "grade_level": grade_level,
        "time_str": custom_time_str,
        "items": parsed_items
    }
