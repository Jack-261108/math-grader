"""公考速算精准数学核算、智能错因归因与学情诊断引擎
提供各种公考速算题型的理论标准答案计算、学生手写答案与标准答案的比对判分、
细粒度智能错因归因（漏写负号、进退位失误、试商偏大偏小、末位算错等）、
以及全卷学情画像与提分建议生成。
"""

from typing import Dict, Any, List, Optional
import re


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


def diagnose_item_error(op_type: str, a: int, b: int, expected: int, student_val: Optional[int], student_raw: Optional[str] = None) -> Dict[str, str]:
    """智能分析单个题目的错因，返回结构化归因标签、诊断说明与速算建议"""
    if student_val is None:
        raw_hint = f"（原识别内容: '{student_raw}'）" if student_raw and str(student_raw).strip() else ""
        return {
            "error_type": "unanswered",
            "error_name": "未作答/留空",
            "diagnosis": f"此题未检测到有效数字作答{raw_hint}。",
            "advice": "遇到卡顿题目应快速估算或合理跳过，保持整体答题节奏。"
        }

    if student_val == expected:
        return {
            "error_type": "none",
            "error_name": "正确",
            "diagnosis": "作答完全正确。",
            "advice": ""
        }

    op = op_type.lower().strip()
    diff = student_val - expected
    abs_diff = abs(diff)

    # 1. 减法专项错因归因
    if "sub" in op or "-" in op or "减" in op:
        # 漏写负号 (小减大只写了绝对值)
        if expected < 0 and student_val == abs(expected):
            return {
                "error_type": "missing_negative",
                "error_name": "漏写负号",
                "diagnosis": f"未注意小减大，结果应为负数 ({expected})，误写为正数 ({student_val})。",
                "advice": "做减法先审题视大小：被减数小于减数时，心算先定负号再做大减小。"
            }
        # 颠倒减法 (算成 b - a)
        if student_val == (b - a):
            return {
                "error_type": "reversed_subtraction",
                "error_name": "减数颠倒",
                "diagnosis": f"减数与被减数位置混淆，误算成 {b} - {a} = {b - a}。",
                "advice": "注意算式左向右的先后次序，避免看成逆向或下减上。"
            }
        # 退位借位失误 (差刚好是 10 或 100)
        if diff in (10, 100):
            return {
                "error_type": "borrow_error",
                "error_name": "退位借位遗漏",
                "diagnosis": f"十位或百位借位后忘记扣减 1，导致结果偏大 {diff}。",
                "advice": "减法退位时可在前位上方微点记号，或使用‘基准数补数法’从高位直减。"
            }
        elif diff in (-10, -100):
            return {
                "error_type": "borrow_error",
                "error_name": "重复退位扣减",
                "diagnosis": f"十位未借位却错误扣减，导致计算结果偏小 {abs_diff}。",
                "advice": "看清个位是否需要退位再决定高位是否减 1。"
            }

    # 2. 加法专项错因归因
    elif "add" in op or "+" in op or "加" in op:
        # 进位漏加
        if diff in (-10, -100):
            return {
                "error_type": "carry_error",
                "error_name": "加法漏进位",
                "diagnosis": f"个位或十位相加满十后漏向前一位进 1，导致结果偏小 {abs_diff}。",
                "advice": "加法推荐从高位向低位相加：如 68+45，先算 60+40=100，再加 8+5=13 得 113。"
            }
        elif diff in (10, 100):
            return {
                "error_type": "carry_error",
                "error_name": "加法多进位",
                "diagnosis": f"未满十却错误向前进位，导致计算结果偏大 {diff}。",
                "advice": "先瞄一眼个位数字相加是否超过 10，形成前置进位预判反射。"
            }
        # 个位数算错但十位百位相符
        if (a + b) % 10 != student_val % 10 and abs_diff < 10:
            return {
                "error_type": "unit_digit_error",
                "error_name": "个位口算失误",
                "diagnosis": f"个位应为 {(a + b) % 10}，误算为 {abs(student_val) % 10} (相差 {diff:+d})。",
                "advice": "加法尾数最容易核对，交卷前快速扫一遍尾数即可排查 80% 的粗心。"
            }

    # 3. 乘法专项错因归因
    elif "mul" in op or "×" in op or "*" in op or "乘" in op:
        # 数量级错误 (位数多写或少写一位，差 10 倍)
        if student_val == expected * 10 or (expected % 10 == 0 and student_val == expected // 10):
            return {
                "error_type": "order_of_magnitude",
                "error_name": "乘法数量级看错",
                "diagnosis": "计算结果位数多写或少写一位（相差 10 倍）。",
                "advice": "先粗估数量级：如两位数乘个位数必为两位或三位数，防止末尾误添 0。"
            }
        # 乘法末位口诀失误
        if (a * b) % 10 != student_val % 10:
            return {
                "error_type": "multiplication_unit_error",
                "error_name": "乘法尾数算错",
                "diagnosis": f"乘法末位口诀失误：{a % 10} × {b % 10} 尾数必为 {(a * b) % 10}，但写成了 {abs(student_val) % 10}。",
                "advice": "牢记九九乘法口诀，乘法作答完毕务必以‘尾数法’复核末尾一位。"
            }
        # 尾数对了，十位/百位算错 (进位或错位相加失误)
        else:
            return {
                "error_type": "multiplication_carry_error",
                "error_name": "乘法进位相加偏差",
                "diagnosis": f"尾数计算正确，但在十位相乘叠加进位时出现偏差 (相差 {diff:+d})。",
                "advice": "两位数乘法拆分心算：例如 62×4 拆为 60×4 + 2×4 = 240 + 8 = 248。"
            }

    # 4. 除法截位商首位/首两位错因归因
    elif "div" in op or "商" in op or "除" in op:
        if diff == 1:
            return {
                "error_type": "division_high",
                "error_name": "截位试商偏大",
                "diagnosis": f"估算试商偏大 1（正解应为 {expected}，误估为 {student_val}）。",
                "advice": "除数截位四舍五入若变大，商会相应微偏小；若余数不足除数则商偏大，试商应留有余地。"
            }
        elif diff == -1:
            return {
                "error_type": "division_low",
                "error_name": "截位试商偏小",
                "diagnosis": f"估算试商偏小 1（正解应为 {expected}，误估为 {student_val}）。",
                "advice": "截位直除时若余数大于或等于除数，说明商还可以再大 1。"
            }
        elif len(str(student_val)) != len(str(expected)):
            return {
                "error_type": "division_digits",
                "error_name": "除法截取位数不符",
                "diagnosis": f"题型要求提取 {len(str(expected))} 位商，作答填写了 {len(str(student_val))} 位。",
                "advice": "审题注意区分是【商首位】（只需 1 位）还是【商前两位】（需 2 位）。"
            }

    # 5. 通用形态错因归因
    # 数字顺序颠倒 (如 48 误写为 84)
    s_exp = str(abs(expected))
    s_stu = str(abs(student_val))
    if len(s_exp) == len(s_stu) and sorted(s_exp) == sorted(s_stu) and len(s_exp) >= 2:
        return {
            "error_type": "digit_transposition",
            "error_name": "数字位置颠倒",
            "diagnosis": f"疑似手写笔误：数字顺序颠倒（正解为 {expected}，手写写成了 {student_val}）。",
            "advice": "下笔书写时保持与脑中心算节奏同步，落笔后顺带瞟一眼位数顺序。"
        }

    # 邻数微小偏差 (+-1 或 +-2)
    if abs_diff <= 2:
        return {
            "error_type": "off_by_one",
            "error_name": "邻位微小偏差",
            "diagnosis": f"与标准答案仅相差 {abs_diff}（正解为 {expected}，作答为 {student_val}），多为临时口算粗心。",
            "advice": "差额极小，属于单纯粗心。平时练习时强化心算注意力即可避免。"
        }

    # 兜底：常规计算偏差
    return {
        "error_type": "calculation_error",
        "error_name": "计算偏差",
        "diagnosis": f"计算结果偏差 {diff:+d}（正解为 {expected}，作答为 {student_val}）。",
        "advice": "建议采用拆分速算法，将复杂多位数分解为整十数与个位数分别计算后再合并。"
    }


def judge_item(op_type: str, a: int, b: int, student_raw: Optional[str]) -> Dict[str, Any]:
    """判定单个题目的作答情况，并给出细粒度错因归因。

    返回：
        dict 包含：
            - expected: 标准答案
            - student_val: 解析出的学生答案数值 (int 或 None)
            - is_correct: True / False / None (None 表示未作答或无法识别)
            - status: "correct" / "wrong" / "unknown"
            - error_type: 错因类别代号
            - error_name: 错因中文名称（如"漏写负号"、"加法进位失误"）
            - diagnosis: 针对该题的深度分析
            - advice: 针对该题型的提分点拨
    """
    expected = calculate_expected(op_type, a, b)
    student_val = clean_student_answer(student_raw)

    if student_val is None:
        diag = diagnose_item_error(op_type, a, b, expected, None, student_raw)
        return {
            "expected": expected,
            "student_raw": student_raw,
            "student_val": None,
            "is_correct": None,
            "status": "unknown",
            **diag
        }

    # 精确匹配
    is_correct = (student_val == expected)

    diag = diagnose_item_error(op_type, a, b, expected, student_val, student_raw)

    return {
        "expected": expected,
        "student_raw": student_raw,
        "student_val": student_val,
        "is_correct": is_correct,
        "status": "correct" if is_correct else "wrong",
        **diag
    }


def parse_time_to_seconds(time_str: str) -> int:
    """解析如 '23分18秒' 或 '15:30' 为总秒数"""
    if not time_str:
        return 0
    # 匹配 "23分18秒" / "23m18s"
    m = re.search(r'(\d+)\s*[分m:]\s*(\d+)?', time_str)
    if m:
        mins = int(m.group(1))
        secs = int(m.group(2)) if m.group(2) else 0
        return mins * 60 + secs
    # 纯数字视作秒
    m_sec = re.search(r'(\d+)\s*秒?', time_str)
    if m_sec:
        return int(m_sec.group(1))
    return 0


def generate_diagnosis_summary(parsed_items: List[Dict[str, Any]], custom_time_str: str = "23分18秒") -> Dict[str, Any]:
    """汇总整卷错因分布、生成学情画像与综合提分策略"""
    total = len(parsed_items)
    wrong_items = [it for it in parsed_items if it.get("is_correct") is False and it.get("status") != "unknown"]
    unknown_items = [it for it in parsed_items if it.get("status") == "unknown"]

    # 1. 统计错因分布
    error_counts: Dict[str, int] = {}
    for it in wrong_items:
        name = it.get("error_name", "计算偏差")
        error_counts[name] = error_counts.get(name, 0) + 1

    # 按错误数量倒序排列
    sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
    error_breakdown = [{"name": k, "count": v} for k, v in sorted_errors]

    # 2. 判定核心薄弱环节
    if not sorted_errors:
        if unknown_items:
            primary_weakness = f"全卷无计算错误，但有 {len(unknown_items)} 题留空未答"
        else:
            primary_weakness = "全卷无明显计算薄弱项，发挥极为出色！"
    else:
        top_err_name, top_err_cnt = sorted_errors[0]
        primary_weakness = f"主要失分点为【{top_err_name}】（共 {top_err_cnt} 题），占错题的 {round(top_err_cnt / len(wrong_items) * 100)}%"

    # 3. 速度与节奏学情评估
    total_seconds = parse_time_to_seconds(custom_time_str)
    answered_count = total - len(unknown_items)
    sec_per_item = round(total_seconds / answered_count, 1) if answered_count > 0 and total_seconds > 0 else 0.0

    if sec_per_item == 0:
        speed_level = "标准"
        speed_advice = "保持当前做题节奏，注重各题型的计算稳定性。"
    elif sec_per_item <= 8.0:
        speed_level = "极速"
        speed_advice = f"平均每题仅耗时 {sec_per_item} 秒，答题速度极快！但需防范急躁导致的进借位或漏负号失误。"
    elif sec_per_item <= 15.0:
        speed_level = "良好"
        speed_advice = f"平均每题耗时 {sec_per_item} 秒，符合公考行测标准作答节奏，重点在于减少细小粗心。"
    else:
        speed_level = "偏慢"
        speed_advice = f"平均每题耗时 {sec_per_item} 秒，答题节奏偏稳健。建议加强两位数乘法拆分法与截位直除，提升速度。"

    # 4. 针对性提分建议
    actionable_tips = []
    has_neg_err = any(it.get("error_type") == "missing_negative" for it in wrong_items)
    has_borrow_err = any(it.get("error_type") == "borrow_error" for it in wrong_items)
    has_carry_err = any(it.get("error_type") == "carry_error" for it in wrong_items)
    has_mul_unit_err = any(it.get("error_type") == "multiplication_unit_error" for it in wrong_items)
    has_div_err = any("division" in it.get("error_type", "") for it in wrong_items)

    if has_neg_err:
        actionable_tips.append("【减法负号防漏】：看到小减大算式时，养成下笔前在脑中或卷面上先预置负号的条件反射。")
    if has_carry_err or has_borrow_err:
        actionable_tips.append("【进退位防错】：高位直加直减比逐位借位更稳定（如 63-28 转化为 63-20-8=35，避免传统竖式反复借位）。")
    if has_mul_unit_err:
        actionable_tips.append("【乘法尾数校验法】：做完两位数乘法后，花 0.5 秒心算两数的个位乘积末位，可瞬间拦截错解。")
    if has_div_err:
        actionable_tips.append("【截位直除留余】：截位除法重点看余数与除数关系，余数若大于除数及时补商 1，防止估小。")

    if not actionable_tips:
        if wrong_items:
            actionable_tips.append("【拆分心算法】：两位数运算尽量拆解为整十数与个位数组合（如 47×6 = 40×6 + 7×6 = 240+42 = 282）。")
        else:
            actionable_tips.append("【冲刺保持】：当前计算功底扎实，建议尝试进阶极限压缩用时，挑战每题 6 秒以内的极限速算！")

    return {
        "primary_weakness": primary_weakness,
        "error_breakdown": error_breakdown,
        "speed_level": speed_level,
        "sec_per_item": sec_per_item,
        "speed_advice": speed_advice,
        "actionable_tips": actionable_tips
    }


def grade_sheet(parsed_items: List[Dict[str, Any]], custom_time_str: str = "23分18秒") -> Dict[str, Any]:
    """汇总整张练习卷的批改成绩与智能诊断报告。

    返回：
        dict 包含：
            - total: 总题数
            - correct: 正确题数
            - wrong: 错误题数
            - unknown: 待确认数
            - accuracy_pct: 正确率百分比（如 93.3）
            - grade_level: 等级（A+ / A / B / C / D）
            - time_str: 用时描述
            - diagnosis: 全卷智能学情与错因归因报告
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

    # 生成宏观错因归因与学情诊断报告
    diagnosis_report = generate_diagnosis_summary(parsed_items, custom_time_str=custom_time_str)

    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "unknown": unknown,
        "accuracy_pct": accuracy_pct,
        "grade_level": grade_level,
        "time_str": custom_time_str,
        "diagnosis": diagnosis_report,
        "items": parsed_items
    }

