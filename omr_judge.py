"""公考《行测》选择题填涂卡判题与分模块计分引擎
支持自定义各模块（常识判断、言语理解、数量关系、判断推理、资料分析）的题号范围与分值，
提供国考 135 题、省考 120 题等经典预设，精确计算各模块得分率、全卷总分与行测专属诊断。
"""

import re
from typing import Dict, Any, List, Optional


# ============================================================
# 行测主流标准考试预设模板
# ============================================================
DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "guokao_135": {
        "name": "国家公务员考试 (副省级 135题)",
        "total_questions": 135,
        "full_score": 100.0,
        "sections": [
            {
                "id": "common_sense",
                "name": "常识判断",
                "start_q": 1,
                "end_q": 20,
                "score_per_q": 0.5,
                "desc": "政治、经济、法律、人文综合常识"
            },
            {
                "id": "verbal",
                "name": "言语理解与表达",
                "start_q": 21,
                "end_q": 60,
                "score_per_q": 0.8,
                "desc": "选词填空、片段阅读、语句表达"
            },
            {
                "id": "quantity",
                "name": "数量关系",
                "start_q": 61,
                "end_q": 75,
                "score_per_q": 0.8,
                "desc": "数学运算技巧与应用题"
            },
            {
                "id": "reasoning",
                "name": "判断推理",
                "start_q": 76,
                "end_q": 115,
                "score_per_q": 0.75,
                "desc": "图形推理、定义判断、类比推理、逻辑判断"
            },
            {
                "id": "data_analysis",
                "name": "资料分析",
                "start_q": 116,
                "end_q": 135,
                "score_per_q": 0.8,
                "desc": "文字、表格、图表综合资料速算与分析"
            }
        ]
    },
    "shengkao_120": {
        "name": "省公务员考试 (多省通用 120题)",
        "total_questions": 120,
        "full_score": 100.0,
        "sections": [
            {
                "id": "common_sense",
                "name": "常识判断",
                "start_q": 1,
                "end_q": 20,
                "score_per_q": 0.5,
                "desc": "政治、法律、科技常识"
            },
            {
                "id": "verbal",
                "name": "言语理解与表达",
                "start_q": 21,
                "end_q": 55,
                "score_per_q": 0.9,
                "desc": "词语辨析、中心主旨、细节推断"
            },
            {
                "id": "quantity",
                "name": "数量关系",
                "start_q": 56,
                "end_q": 65,
                "score_per_q": 1.0,
                "desc": "行程、工程、几何、排列组合等"
            },
            {
                "id": "reasoning",
                "name": "判断推理",
                "start_q": 66,
                "end_q": 100,
                "score_per_q": 0.8,
                "desc": "图推、定义、类比、逻辑"
            },
            {
                "id": "data_analysis",
                "name": "资料分析",
                "start_q": 101,
                "end_q": 120,
                "score_per_q": 1.025,
                "desc": "增长率、比重、基期两期速算"
            }
        ]
    },
    "dagang_120": {
        "name": "公考新大纲 (政治理论+五大模块 120题)",
        "total_questions": 120,
        "full_score": 100.0,
        "sections": [
            {
                "id": "politics",
                "name": "政治理论",
                "start_q": 1,
                "end_q": 15,
                "score_per_q": 0.6,
                "desc": "党史党建、马克思主义理论、最新政策与精神"
            },
            {
                "id": "common_sense",
                "name": "常识判断",
                "start_q": 16,
                "end_q": 25,
                "score_per_q": 0.5,
                "desc": "法律、科技、文史国情综合常识"
            },
            {
                "id": "verbal",
                "name": "言语理解与表达",
                "start_q": 26,
                "end_q": 55,
                "score_per_q": 0.9,
                "desc": "逻辑填空、中心主旨、语句表达"
            },
            {
                "id": "quantity",
                "name": "数量关系",
                "start_q": 56,
                "end_q": 70,
                "score_per_q": 0.9,
                "desc": "数学运算技巧与经典模型应用题"
            },
            {
                "id": "reasoning",
                "name": "判断推理",
                "start_q": 71,
                "end_q": 100,
                "score_per_q": 0.8,
                "desc": "图形推理、定义判断、类比推理、逻辑论证"
            },
            {
                "id": "data_analysis",
                "name": "资料分析",
                "start_q": 101,
                "end_q": 120,
                "score_per_q": 1.075,
                "desc": "增长率、比重基期两期速算与综合分析"
            }
        ]
    },
    "dagang_130": {
        "name": "新大纲标准卷 (政治理论20题+五大模块 130题)",
        "total_questions": 130,
        "full_score": 100.0,
        "sections": [
            {
                "id": "politics",
                "name": "政治理论",
                "start_q": 1,
                "end_q": 20,
                "score_per_q": 0.5,
                "desc": "党史党建、新思想重大理论与精神"
            },
            {
                "id": "common_sense",
                "name": "常识判断",
                "start_q": 21,
                "end_q": 35,
                "score_per_q": 0.6,
                "desc": "法律、文史、科技与省情国情"
            },
            {
                "id": "verbal",
                "name": "言语理解与表达",
                "start_q": 36,
                "end_q": 65,
                "score_per_q": 0.9,
                "desc": "选词填空、中心主旨、语句连贯"
            },
            {
                "id": "quantity",
                "name": "数量关系",
                "start_q": 66,
                "end_q": 75,
                "score_per_q": 1.0,
                "desc": "工程、行程、几何与数学模型"
            },
            {
                "id": "reasoning",
                "name": "判断推理",
                "start_q": 76,
                "end_q": 110,
                "score_per_q": 0.7,
                "desc": "图形推理、定义判断、类比推理、逻辑论证"
            },
            {
                "id": "data_analysis",
                "name": "资料分析",
                "start_q": 111,
                "end_q": 130,
                "score_per_q": 0.975,
                "desc": "增长率、现期基期速算与综合分析"
            }
        ]
    },
    "special_practice_20": {
        "name": "模块专项突击卡 (20题 / 20分)",
        "total_questions": 20,
        "full_score": 20.0,
        "sections": [
            {
                "id": "practice",
                "name": "专项练习",
                "start_q": 1,
                "end_q": 20,
                "score_per_q": 1.0,
                "desc": "行测单模块高频错题速练"
            }
        ]
    },
    "special_practice_30": {
        "name": "小卷模考练习卡 (30题 / 30分)",
        "total_questions": 30,
        "full_score": 30.0,
        "sections": [
            {
                "id": "practice",
                "name": "微模考卷",
                "start_q": 1,
                "end_q": 30,
                "score_per_q": 1.0,
                "desc": "30题计时强化训练"
            }
        ]
    }
}


def parse_answer_key(raw_text: str, total_q: Optional[int] = None) -> Dict[int, str]:
    """多模式解析用户输入的标准答案。

    支持输入形式：
    1. 连续纯字母: "BACDDACBDD..."
    2. 带题号标号: "1-5: BACDD 6-10: ACBDD..." 或 "1.A 2.B 3.C..."
    3. 逗号/空格分隔: "B, A, C, D, D..." 或 "B A C D D..."
    4. 逐行形式: "1 A\n2 B\n3 C..."
    """
    if not raw_text:
        return {}

    text = raw_text.strip()
    result: Dict[int, str] = {}

    # 形式 A: 带明确题号的模式 (例如 1.A 或 1:A 或 1 A)
    numbered_matches = re.findall(r'(\d+)[\s.:、-]*([A-Da-d])\b', text)
    if numbered_matches and len(numbered_matches) >= 3:
        for q_str, ans in numbered_matches:
            result[int(q_str)] = ans.upper()
        return result

    # 形式 B: 题号区间模式 (例如 1-5 BACDD, 1--5 CBADC, 1 ~ 5: CBADC 等多列排版)
    range_iter = list(re.finditer(r'(\d+)\s*(?:[-~至—–]{1,2})\s*(\d+)[\s:：]*([A-Da-d]{1,10})', text))
    if range_iter:
        max_seen_q = 0
        for m in range_iter:
            start_s, _, ans_block = m.group(1), m.group(2), m.group(3)
            start_num = int(start_s)
            letters = [c.upper() for c in ans_block if c.upper() in "ABCD"]

            # 检测是否为试卷末尾的附加题/加试题，避免覆盖正题开头的 1~5 题
            prefix_text = text[max(0, m.start() - 30):m.start()]
            is_extra = any(k in prefix_text for k in ["附加", "加试", "选做", "选考"]) or (max_seen_q > 50 and start_num <= 10)

            if is_extra and max_seen_q > 0:
                # 顺延至卷尾作为附加题，不覆盖卷首正题
                for idx, letter in enumerate(letters):
                    cur_q = max_seen_q + 1 + idx
                    result[cur_q] = letter
                max_seen_q += len(letters)
            else:
                for idx, letter in enumerate(letters):
                    cur_q = start_num + idx
                    result[cur_q] = letter
                    if cur_q > max_seen_q:
                        max_seen_q = cur_q
        if result:
            return result

    # 形式 C: 纯字母序列（忽略所有标点与空白）
    pure_letters = [c.upper() for c in text if c.upper() in "ABCD"]
    for idx, letter in enumerate(pure_letters, start=1):
        if total_q and idx > total_q:
            break
        result[idx] = letter

    return result


def get_section_for_question(q_num: int, sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """根据题号查找匹配的模块配置"""
    for sec in sections:
        if sec["start_q"] <= q_num <= sec["end_q"]:
            return sec
    return None


def judge_omr_sheet(
    student_answers: Dict[int, Optional[str]],
    standard_answers: Dict[int, str],
    sections_config: Optional[List[Dict[str, Any]]] = None,
    custom_time_str: str = "25分00秒"
) -> Dict[str, Any]:
    """对填涂卡选项进行逐题核对、分模块核算与全卷学情诊断。

    参数：
        - student_answers: 识别到的学生填涂选项，格式 {题号: "A"/"B"/"C"/"D"/None/"multiple"}
        - standard_answers: 标准答案映射，格式 {题号: "A"/"B"/"C"/"D"}
        - sections_config: 模块与分值配置列表
        - custom_time_str: 作答用时

    返回：
        dict 结构：
            - summary: 全卷得分、总题数、做对数、做错数、未填数、正确率、评级
            - section_results: 各模块明细指标
            - diagnosis: 针对行测各科目的诊断与提分建议
            - items: 1~N 题的逐题判分明细
    """
    target_sections: List[Dict[str, Any]] = (
        sections_config if sections_config is not None else DEFAULT_PRESETS["guokao_135"]["sections"]  # type: ignore
    )

    # 确定总题数
    max_sec_q = max(s["end_q"] for s in target_sections) if target_sections else 0
    max_std_q = max(standard_answers.keys()) if standard_answers else 0
    max_stu_q = max(student_answers.keys()) if student_answers else 0
    total_q_count = max(max_sec_q, max_std_q, max_stu_q, 1)

    # 逐题判定
    judged_items = []
    total_earned_score = 0.0
    total_max_score = 0.0
    total_correct = 0
    total_wrong = 0
    total_unanswered = 0

    # 模块统计器初始化
    section_stats = {}
    for sec in target_sections:
        sec_id = sec.get("id", sec["name"])
        section_stats[sec_id] = {
            "id": sec_id,
            "name": sec["name"],
            "start_q": sec["start_q"],
            "end_q": sec["end_q"],
            "total_q": sec["end_q"] - sec["start_q"] + 1,
            "score_per_q": sec.get("score_per_q", 1.0),
            "correct_q": 0,
            "wrong_q": 0,
            "unanswered_q": 0,
            "earned_score": 0.0,
            "max_score": round((sec["end_q"] - sec["start_q"] + 1) * sec.get("score_per_q", 1.0), 2),
            "accuracy_pct": 0.0
        }

    for q_num in range(1, total_q_count + 1):
        sec = get_section_for_question(q_num, target_sections)
        sec_id = sec.get("id", sec["name"]) if sec else "other"
        sec_name = sec["name"] if sec else "未归类"
        score_per_q = sec.get("score_per_q", 1.0) if sec else 1.0

        stu_choice = student_answers.get(q_num)
        std_choice = standard_answers.get(q_num)

        # 状态研判
        if stu_choice is None or stu_choice == "" or stu_choice == "null":
            status = "unanswered"
            is_correct = None
            earned = 0.0
            total_unanswered += 1
            if sec_id in section_stats:
                section_stats[sec_id]["unanswered_q"] += 1
        elif stu_choice == "multiple":
            status = "multiple"
            is_correct = False
            earned = 0.0
            total_wrong += 1
            if sec_id in section_stats:
                section_stats[sec_id]["wrong_q"] += 1
        elif std_choice and stu_choice.upper() == std_choice.upper():
            status = "correct"
            is_correct = True
            earned = score_per_q
            total_correct += 1
            total_earned_score += earned
            if sec_id in section_stats:
                section_stats[sec_id]["correct_q"] += 1
                section_stats[sec_id]["earned_score"] += earned
        else:
            status = "wrong"
            is_correct = False
            earned = 0.0
            total_wrong += 1
            if sec_id in section_stats:
                section_stats[sec_id]["wrong_q"] += 1

        total_max_score += score_per_q

        judged_items.append({
            "q_num": q_num,
            "section_name": sec_name,
            "section_id": sec_id,
            "student_choice": stu_choice if stu_choice else "未涂",
            "standard_choice": std_choice if std_choice else "未设",
            "is_correct": is_correct,
            "status": status,
            "score_per_q": score_per_q,
            "earned_score": earned
        })

    # 计算各模块正确率与百分比
    section_results_list = []
    for sec_id, stat in section_stats.items():
        if stat["total_q"] > 0:
            stat["accuracy_pct"] = round(stat["correct_q"] / stat["total_q"] * 100.0, 1)
            stat["earned_score"] = round(stat["earned_score"], 2)
        section_results_list.append(stat)

    # 全卷正确率
    answered_count = total_correct + total_wrong
    overall_acc = round(total_correct / answered_count * 100.0, 1) if answered_count > 0 else 0.0
    total_earned_score = round(total_earned_score, 2)
    total_max_score = round(total_max_score, 2)

    # 评级划分（按实际得分占满分比例）
    score_ratio = (total_earned_score / total_max_score) if total_max_score > 0 else 0.0
    if score_ratio >= 0.80:
        grade_level = "卓越"
        grade_badge = "A+"
    elif score_ratio >= 0.70:
        grade_level = "优秀"
        grade_badge = "A"
    elif score_ratio >= 0.60:
        grade_level = "良好"
        grade_badge = "B"
    elif score_ratio >= 0.50:
        grade_level = "合格"
        grade_badge = "C"
    else:
        grade_level = "需强化"
        grade_badge = "D"

    # 生成行测五大模块专属学情诊断
    diagnosis = generate_omr_diagnosis(section_results_list, total_earned_score, total_max_score, custom_time_str)

    return {
        "summary": {
            "total_questions": total_q_count,
            "total_earned_score": total_earned_score,
            "total_max_score": total_max_score,
            "total_correct": total_correct,
            "total_wrong": total_wrong,
            "total_unanswered": total_unanswered,
            "accuracy_pct": overall_acc,
            "score_ratio_pct": round(score_ratio * 100, 1),
            "grade_level": grade_level,
            "grade_badge": grade_badge,
            "time_str": custom_time_str
        },
        "section_results": section_results_list,
        "diagnosis": diagnosis,
        "items": judged_items
    }


def generate_omr_diagnosis(
    section_results: List[Dict[str, Any]],
    total_earned: float,
    total_max: float,
    custom_time_str: str
) -> Dict[str, Any]:
    """基于各模块得分表现生成行测备考学情分析与策略"""
    valid_sections = [s for s in section_results if s["total_q"] > 0]
    if not valid_sections:
        return {
            "weakest_section": "无",
            "strongest_section": "无",
            "score_summary": f"得分: {total_earned} / {total_max}",
            "actionable_tips": ["请配置模块答案进行分析"]
        }

    # 按正确率排序
    sorted_by_acc = sorted(valid_sections, key=lambda s: s["accuracy_pct"])
    weakest = sorted_by_acc[0]
    strongest = sorted_by_acc[-1]

    tips = []

    # 针对最弱模块提出突破锦囊
    sec_name = weakest["name"]
    if "资料" in sec_name:
        tips.append("【资料分析提分瓶颈】：资料分析是行测提分‘基本盘’，目标正确率应在 85% 以上。重点强化截位直除与比重公式计算，提速防粗心。")
    elif "数量" in sec_name:
        tips.append("【数量关系做题策略】：数量关系切忌全盘放弃或盲目死磕。精选工程问题、利润问题、行程问题等 3~5 道常考题优先拿下，其余合理蒙猜。")
    elif "言语" in sec_name:
        tips.append("【言语理解破局点】：抓好逻辑填空的核心实词色彩搭配与片段阅读行文脉络（转折、因果、总分），防止主观过度引申。")
    elif "判断" in sec_name:
        tips.append("【判断推理重点抓牢】：图形推理优先排查‘对称、位置、笔画、点线面’四大常考考点；类比推理关注二阶对应关系。")
    elif "常识" in sec_name:
        tips.append("【常识判断作答节奏】：常识判断讲求快速过题，每题控制在 30~45 秒内，第一直觉作答，腾出宝贵时间给资料分析。")

    # 检查是否有较多留空未填
    total_unans = sum(s["unanswered_q"] for s in valid_sections)
    if total_unans > 5:
        tips.append(f"【填涂提醒】：全卷共有 {total_unans} 题漏填或空白。行测考试所有选择题务必全部填涂，最后 5 分钟必须留足时间涂卡。")

    if strongest["accuracy_pct"] >= 80:
        tips.append(f"【优势保持】：【{strongest['name']}】正确率达到 {strongest['accuracy_pct']}%，表现优秀！可作为稳定拿分的主力阵地。")

    # 计算作答速度与节奏画像
    total_seconds = 0
    m_match = re.search(r'(\d+)\s*分', custom_time_str)
    s_match = re.search(r'(\d+)\s*秒', custom_time_str)
    if m_match:
        total_seconds += int(m_match.group(1)) * 60
    if s_match:
        total_seconds += int(s_match.group(1))

    speed_advice = None
    total_questions = sum(s["total_q"] for s in valid_sections)
    if total_seconds > 0 and total_questions > 0:
        sec_per_q = round(total_seconds / total_questions, 1)
        if sec_per_q <= 50:
            speed_advice = f"做题配速 {sec_per_q}秒/题 (属于极快节奏，需注意细心审题，防范陷阱)"
        elif sec_per_q <= 60:
            speed_advice = f"做题配速 {sec_per_q}秒/题 (符合行测实战标准考场黄金配速，非常优秀)"
        else:
            speed_advice = f"做题配速 {sec_per_q}秒/题 (略偏慢，考场建议每题控制在 50~55 秒内并留足涂卡时间)"
        tips.append(f"【作答速度】：用时 {custom_time_str}，平均每题约 {sec_per_q} 秒。{speed_advice}")

    return {
        "weakest_section": f"{weakest['name']} (正确率 {weakest['accuracy_pct']}%)",
        "strongest_section": f"{strongest['name']} (正确率 {strongest['accuracy_pct']}%)",
        "score_summary": f"总分 {total_earned} 分 / 满分 {total_max} 分 (得分率 {round(total_earned / total_max * 100, 1) if total_max else 0}%)",
        "speed_advice": speed_advice,
        "actionable_tips": tips
    }
