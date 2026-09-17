"""速算自适应强化题生成规则引擎 (Adaptive Math Generator).

针对公考行测速算诊断中的高频薄弱短板（如三位数退位借位减法、四位数除以三位数首两位截位直除、两位数拆分乘法、进位加法等），
纯 Python 原生数学规则引擎动态、毫秒级即时生成 20 道高拟真度同型变式算式，
实现“诊断发现薄弱 -> 即刻针对刷题 -> 彻底攻克”的即时提分闭环。
"""

import random
from typing import Any, Dict, List


def generate_targeted_exercises(
    weakness_type: str,
    count: int = 20,
    weakness_name: str = ""
) -> Dict[str, Any]:
    """根据薄弱短板类型，精准动态生成 count 道（默认 20 道）同型专项强化算式。"""
    w_type = (weakness_type or "").lower()
    exercises: List[Dict[str, Any]] = []

    # 1. 三位数退位借位减法专项 (Borrow Error)
    if any(k in w_type for k in ["borrow", "退位", "借位", "sub", "减法"]):
        category_title = "三位数减法退位借位专项强化练"
        target_description = "针对个位、十位连续退位借位偏差，训练高位直减心算手感与准确率"
        core_tip = "【高位直减法】：先减百位十位，再处理个位退位。如 624-389 转化为 624-300-80-9 = 324-80-9 = 244-9 = 235。"

        seen = set()
        while len(exercises) < count:
            a = random.randint(220, 980)
            # 保证个位必定需要退位借位
            a_unit = a % 10
            if a_unit >= 8:
                a -= 2
                a_unit = a % 10

            b_unit = random.randint(a_unit + 1, 9)
            b_tens = random.randint(1, 8)
            b_hundreds = random.randint(1, (a // 100))
            b = b_hundreds * 100 + b_tens * 10 + b_unit

            if b >= a or (a, b) in seen:
                continue

            # 确保至少有一位发生借位
            if (a % 10 < b % 10) or ((a // 10) % 10 < (b // 10) % 10):
                seen.add((a, b))
                expected = a - b
                idx = len(exercises) + 1
                exercises.append({
                    "q_num": idx,
                    "expression": f"{a} - {b}",
                    "a": a,
                    "b": b,
                    "op_type": "sub",
                    "op_symbol": "-",
                    "expected": expected,
                    "tip": "先算整百整十差，再扣除个位借位"
                })

    # 2. 四位数除以三位数首两位截位直除专项 (Division Truncate / High / Low)
    elif any(k in w_type for k in ["div", "截位", "除法", "商", "直除"]):
        category_title = "四位数除以三位数首两位截位直除专项练"
        target_description = "针对资料分析高频截位直除试商偏差，强化‘除数留三位，先定首位再定次位’的能力"
        core_tip = "【截位直除口诀】：除数保留前三位直除，先定商的首位，余数若大于或等于除数则商偏小，余数不足则商偏大。"

        seen = set()
        while len(exercises) < count:
            # 除数 b: 三位数 (如 125 ~ 890)
            b = random.randint(125, 880)
            # 真实资料分析商通常为 1~50 左右 (求商的整数部分/前两位)
            quotient = random.randint(12, 65)
            remainder = random.randint(5, b - 1)
            a = b * quotient + remainder

            # 确保被除数 a 是四位数
            if a < 1000 or a > 9999 or (a, b) in seen:
                continue

            seen.add((a, b))
            idx = len(exercises) + 1
            # 预期答案为商的前两位整数
            exercises.append({
                "q_num": idx,
                "expression": f"{a} ÷ {b}",
                "a": a,
                "b": b,
                "op_type": "div",
                "op_symbol": "÷",
                "expected": quotient,
                "tip": f"首位试商估 {quotient // 10}，次位估 {quotient % 10}"
            })

    # 3. 三位数加法连续进位专项 (Carry Error)
    elif any(k in w_type for k in ["carry", "进位", "add", "加法"]):
        category_title = "三位数加法连续进位专项强化练"
        target_description = "针对满十漏进位、多进位失误，强化个位与十位进位前置预判"
        core_tip = "【高位直加法】：从高位往低位加。如 478+365，先算 400+300=700，70+60=130 得 830，最后 8+5=13 得 843。"

        seen = set()
        while len(exercises) < count:
            a = random.randint(150, 780)
            b_hundreds = random.randint(1, 8 - (a // 100))
            # 确保个位相加满十进位
            a_unit = a % 10
            b_unit = random.randint(10 - a_unit, 9) if a_unit > 0 else random.randint(5, 9)
            # 确保十位相加满十进位
            a_ten = (a // 10) % 10
            b_ten = random.randint(10 - a_ten, 9) if a_ten > 0 else random.randint(5, 9)
            b = b_hundreds * 100 + b_ten * 10 + b_unit

            if (a, b) in seen:
                continue
            seen.add((a, b))

            expected = a + b
            idx = len(exercises) + 1
            exercises.append({
                "q_num": idx,
                "expression": f"{a} + {b}",
                "a": a,
                "b": b,
                "op_type": "add",
                "op_symbol": "+",
                "expected": expected,
                "tip": "个位十位双进位，从高位直加不易漏"
            })

    # 4. 两位数乘法拆分心算专项 (Multiplication)
    elif any(k in w_type for k in ["mul", "乘", "尾数"]):
        category_title = "两位数乘法拆分与尾数法专项强化练"
        target_description = "针对两位数相乘进位偏差，掌握乘数拆分法与末位尾数校验法"
        core_tip = "【拆分乘法】：将较小乘数拆为整十与个位数。如 68×24 = 68×20 + 68×4 = 1360 + 272 = 1632。"

        seen = set()
        while len(exercises) < count:
            a = random.randint(14, 89)
            b = random.randint(12, 38)
            if (a, b) in seen:
                continue
            seen.add((a, b))

            expected = a * b
            idx = len(exercises) + 1
            exercises.append({
                "q_num": idx,
                "expression": f"{a} × {b}",
                "a": a,
                "b": b,
                "op_type": "mul",
                "op_symbol": "×",
                "expected": expected,
                "tip": f"末位必为 {(a * b) % 10}，可用尾数法瞬间复核"
            })

    # 5. 小减大负数防漏符号专项 (Missing Negative)
    elif any(k in w_type for k in ["negative", "负号", "负数"]):
        category_title = "小减大运算与负号防漏专项强化练"
        target_description = "强化小减大算式的负号条件反射，下笔前先定符号"
        core_tip = "【小减大定势】：先在脑中落定‘负号 -’，再心算大数减小数 (b - a)。"

        seen = set()
        while len(exercises) < count:
            a = random.randint(110, 480)
            b = random.randint(a + 45, 960)
            if (a, b) in seen:
                continue
            seen.add((a, b))

            expected = a - b
            idx = len(exercises) + 1
            exercises.append({
                "q_num": idx,
                "expression": f"{a} - {b}",
                "a": a,
                "b": b,
                "op_type": "sub",
                "op_symbol": "-",
                "expected": expected,
                "tip": f"必为负数，先写负号再算 {b} - {a} = {b - a}"
            })

    # 兜底：综合高频速算强化练
    else:
        category_title = f"{weakness_name or '公考速算技巧'}针对性强化练"
        target_description = "精选加减进退位与截位除法高频题型，巩固计算基本盘"
        core_tip = "【做题要诀】：兼顾速度与准确度，熟练运用凑整、拆分与直除技巧。"

        seen = set()
        ops = ["sub", "div", "add", "mul"]
        while len(exercises) < count:
            op = ops[len(exercises) % len(ops)]
            if op == "sub":
                a = random.randint(300, 950)
                b = random.randint(120, a - 20)
                exp = a - b
                sym = "-"
            elif op == "div":
                b = random.randint(120, 450)
                q = random.randint(15, 45)
                a = b * q + random.randint(1, b - 1)
                exp = q
                sym = "÷"
            elif op == "add":
                a = random.randint(180, 520)
                b = random.randint(150, 450)
                exp = a + b
                sym = "+"
            else:
                a = random.randint(15, 68)
                b = random.randint(12, 28)
                exp = a * b
                sym = "×"

            if (a, b, op) in seen:
                continue
            seen.add((a, b, op))

            idx = len(exercises) + 1
            exercises.append({
                "q_num": idx,
                "expression": f"{a} {sym} {b}",
                "a": a,
                "b": b,
                "op_type": op,
                "op_symbol": sym,
                "expected": exp,
                "tip": "心算定首尾，直加直减免借位"
            })

    return {
        "title": category_title,
        "weakness_type": weakness_type,
        "target_description": target_description,
        "core_tip": core_tip,
        "total_items": len(exercises),
        "items": exercises
    }
