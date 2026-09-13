"""公考智能名师错题解析与提分辅导模块
支持速算练习册算式（凑整法、十字相乘、截位直除等公考秒杀思维）
与行测客观选择题（各模块考点分析、选项排除法、避坑指南）的智能点拨。
严格支持 BYOK（Bring Your Own Key）本地安全密钥机制。
"""

import os
import sys
import re
import json
import urllib.request
from urllib.error import HTTPError
from typing import Dict, Any, Optional

cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

import vision_ocr  # type: ignore


MATH_TUTOR_PROMPT = """你是一位经验丰富、深谙公考命题特点与考生痛点的《行测·资料分析与速算》顶级名师。
考生在完成速算练习时做错了以下这道题：
- 算式题目：{expression}
- 考生书写答案：{student_raw}
- 正确标准答案：{expected}
- 初步归因分类：{error_name}
- 考生具体疑问（若有）：{user_query}

请为这位考生提供针对性极强的【名师错题诊断与秒杀提分指导】：
1. 【错因透视】：精准指出考生到底在哪个计算步骤出现了漏洞（例如进位未加、借位遗忘、两数乘积错位、截位直除试商过大或过小等）；
2. 【秒杀秘籍 / 速算技巧】：给出公考行测中最实用、最省时的速算秒杀思路（如凑整拆分法 (A±x)×B、十字相乘法、截位直除前两位或三位法则、差分法、特征数字法等），列出清晰的心算步骤；
3. 【考场避坑要点】：在行测真题实战中，面对此类数据该如何快速防错，以及如何结合选项差距决定精算还是估算；
4. 【名师寄语】：一句话提气勉励。

请务必严格输出如下 JSON 格式，不要输出多余的解释或问候语：
```json
{{
  "core_cause": "详细且一针见血的错因剖析",
  "speed_tricks": "针对本题最快最巧的公考秒杀解法与心算步骤",
  "pitfall_tips": "考场实战避坑技巧与选项差距研判准则",
  "summary": "一句话名师寄语与提分要诀"
}}
```
"""


OMR_TUTOR_PROMPT = """你是一位精通公务员考试《行政职业能力测验》（行测）全模块的资深金牌名师。
考生在完成行测答题时做错了以下客观单选题：
- 题号：第 {q_num} 题
- 所属模块：{section_name}
- 考生作答选项：{student_ans}
- 试卷标准答案：{standard_ans}
{question_context}
- 考生具体疑问或追问（若有）：{user_query}

请针对该题及所属模块特点，给出【行测名师答题卡复盘与提分点拨】：
1. 【错因透视】：结合具体题干与选项（若有），深入分析考生为什么容易掉入 {student_ans} 选项的设错陷阱（如偷换概念、过于绝对、反向设错、以偏概全），以及正确答案 {standard_ans} 的命题破题逻辑；
2. 【秒杀秘籍 / 破局技巧】：传授该模块（如政治理论识记、常识矛盾项研判、言语关联词转折对应、数量特征代入/特值法、判断推理一笔画/假言命题、资料分析截位直除等）在考场上 30 秒秒杀本题的绝技；
3. 【考场避坑要点】：本题型常见的命题设坑套路及考场时间节奏分配；
4. 【名师寄语】：一句话模块复习与提分要诀。

请务必严格输出如下 JSON 格式，不要输出多余的解释或问候语：
```json
{{
  "core_cause": "深入透彻的选项设错陷阱剖析",
  "speed_tricks": "针对本题具体题干的最快秒杀破局法与快速排查策略",
  "pitfall_tips": "实战考场常见的命题陷阱与避坑准则",
  "summary": "一句话模块复习要诀"
}}
```
"""


def get_fallback_explanation(question_type: str, question_info: Dict[str, Any]) -> Dict[str, str]:
    """当网络不可用或大模型调用失败时的兜底专家解析"""
    if question_type == "math":
        expr = question_info.get("expression", "")
        err_name = question_info.get("error_name", "计算偏差")
        return {
            "core_cause": f"本题（{expr}）主要失分在【{err_name}】。多位数混合运算或速算中，考生往往由于心算负荷过大，容易忽略进位/借位状态或试商微调。",
            "speed_tricks": "【公考秒杀建议】：资料分析中建议使用『截位直除』或『拆分法』。对于乘法可化为整数倍相加减（如 98×34 = 100×34 - 2×34）；对于除法，分母保留前三位截位计算，先看首位排除 2 个选项，再看第二位直接锁定答案。",
            "pitfall_tips": "【考场避坑】：做题前先观察 4 个选项首位是否相同。若选项差距大于 10%，只保留前两位精简算；若选项差距小于 3%，再保留三位精算，切忌盲目从头硬算！",
            "summary": "行测资料分析重在『算得巧』而非『算得苦』，善用选项差距就是最大的提分捷径！"
        }
    else:
        sec = question_info.get("section_name", "行测客观题")
        std_ans = question_info.get("standard_ans", "")
        stu_ans = question_info.get("student_ans", "未作答")
        stem = question_info.get("stem", "")
        analysis = question_info.get("analysis", "")

        cause_text = f"考生错选了【{stu_ans}】，标准答案为【{std_ans}】。"
        if stem:
            cause_text += f"\n原题考点分析：{stem[:80]}...\n命题人在【{stu_ans}】选项中常暗含偷换概念、过于绝对或计算截位失误的强干扰项。"
        else:
            cause_text += f"在【{sec}】模块中，出题人常常设置看似合理但暗含偷换概念、过于绝对或计算截位失误的强干扰项。"

        trick_text = f"【{sec} 模块秒杀策略】：1. 善用『代入排除法』与『矛盾选项研判』；2. 圈画题干限定词；3. 牢记选项平衡律。"
        if analysis:
            trick_text = f"{analysis}\n" + trick_text

        return {
            "core_cause": cause_text,
            "speed_tricks": trick_text,
            "pitfall_tips": "实战中切忌在难题上纠缠超过 80 秒，第一时间标记疑难并蒙猜备选，确保资料分析等高性价比模块拿满 85% 以上分数。",
            "summary": "行测考的是『取舍的艺术』，稳住心态与模块节奏，必能取得理想成绩！"
        }


def explain_mistake(
    question_type: str,
    question_info: Dict[str, Any],
    user_query: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 45,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """调用大模型为错题生成深度名师指导。

    参数：
        - question_type: 'math' (速算练习) 或 'omr' (行测选择题)
        - question_info: 题目详细信息字典
        - user_query: 考生自定义追问或补充题干
        - model: 自定义模型名
        - timeout: 超时时间
        - base_url: BYOK Base URL
        - api_key: BYOK API Key

    返回：
        Dict 包含 core_cause, speed_tricks, pitfall_tips, summary
    """
    vision_ocr._load_dotenv()

    # 1. 解析 Base URL (必须显式传入或用户配置)
    effective_base_url = base_url.strip() if (base_url and base_url.strip()) else ""
    if not effective_base_url:
        raise ValueError(
            "未配置 Base URL，请在【设置】中填写您的 API Base URL (BYOK)。"
        )

    # 2. 解析 API Key (必须显式传入或用户配置)
    effective_api_key = api_key.strip() if (api_key and api_key.strip()) else ""
    if not effective_api_key:
        raise ValueError(
            "未配置 API Key，请在【设置】中填写您的 API Key (BYOK)。"
        )

    if model and model.strip():
        candidate_models = [model.strip()]
    else:
        env_model = os.environ.get("ANTHROPIC_DEFAULT_MODEL", "").strip()
        if env_model:
            candidate_models = [env_model]
        else:
            candidate_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-7-sonnet-20250219",
                "claude-3-5-haiku-20241022",
                "gemini-2.5-flash"
            ]

    u_query_clean = user_query.strip() if (user_query and user_query.strip()) else "无额外追问，请针对该题进行经典剖析"

    if question_type == "math":
        prompt = MATH_TUTOR_PROMPT.format(
            expression=question_info.get("expression", ""),
            student_raw=question_info.get("student_raw", ""),
            expected=question_info.get("expected", ""),
            error_name=question_info.get("error_name", "计算失误"),
            user_query=u_query_clean
        )
    else:
        # 构建完整原题题干与选项上下文
        q_context_lines = []
        material = question_info.get("material", "").strip()
        if material:
            q_context_lines.append(f"- 试卷资料/阅读材料：\n{material}")
        stem = question_info.get("stem", "").strip()
        if stem:
            q_context_lines.append(f"- 原题题干：\n{stem}")
        options = question_info.get("options")
        if isinstance(options, dict) and options:
            opts_str = "\n".join([f"  {k}. {v}" for k, v in options.items()])
            q_context_lines.append(f"- 原题选项：\n{opts_str}")
        analysis = question_info.get("analysis", "").strip()
        if analysis:
            q_context_lines.append(f"- 试卷参考答案解析：\n{analysis}")

        question_context = "\n".join(q_context_lines) if q_context_lines else "- 原题题干：暂未提供具体题干，请按该模块高频设错套路进行深度剖析。"

        prompt = OMR_TUTOR_PROMPT.format(
            q_num=question_info.get("q_num", 1),
            section_name=question_info.get("section_name", "行测"),
            student_ans=question_info.get("student_ans", "未作答"),
            standard_ans=question_info.get("standard_ans", "A"),
            question_context=question_context,
            user_query=u_query_clean
        )

    url = vision_ocr.build_messages_url(effective_base_url)
    headers = {
        "x-api-key": effective_api_key,
        "authorization": f"Bearer {effective_api_key}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    last_err = None
    for cand_model in candidate_models:
        try:
            payload = {
                "model": cand_model,
                "max_tokens": 2048,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_bytes = resp.read()
                resp_json = json.loads(resp_bytes.decode('utf-8'))

            content_text = ""
            for block in resp_json.get("content", []):
                if block.get("type") == "text":
                    content_text += block.get("text", "")

            # 提取 JSON 块
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content_text, re.DOTALL)
            text_to_parse = json_match.group(1) if json_match else content_text

            try:
                data = json.loads(text_to_parse)
                if isinstance(data, dict):
                    return {
                        "core_cause": data.get("core_cause", "错因分析详见下文秒杀秘籍。"),
                        "speed_tricks": data.get("speed_tricks", "善用截位直除与首位排除法。"),
                        "pitfall_tips": data.get("pitfall_tips", "审清题干时间节点与增长率/增长量区别。"),
                        "summary": data.get("summary", "稳扎稳打，查漏补缺！")
                    }
            except Exception:
                pass

            # 若直接解析失败，将文本分段整理
            if content_text.strip():
                return {
                    "core_cause": content_text[:300],
                    "speed_tricks": content_text[300:700] if len(content_text) > 300 else content_text,
                    "pitfall_tips": "考场谨防偷换概念与粗心失误，优先根据选项差距决定做题精度。",
                    "summary": "掌握高频题型解题套路，冲刺高分！"
                }

        except HTTPError as he:
            err_body = ""
            try:
                err_body = he.read().decode('utf-8', errors='ignore')
            except Exception:
                pass
            print(f"[AI Tutor HTTPError] URL: {url}, Model: {cand_model}, Code: {he.code}, Reason: {he.reason}, Body: {err_body[:400]}")
            msg = f"HTTP {he.code} ({he.reason})"
            if err_body:
                try:
                    err_json = json.loads(err_body)
                    if isinstance(err_json, dict) and "error" in err_json:
                        e_val = err_json["error"]
                        if isinstance(e_val, dict):
                            msg += f": {e_val.get('message') or e_val.get('type') or str(e_val)}"
                        else:
                            msg += f": {e_val}"
                    else:
                        msg += f": {err_body[:200]}"
                except Exception:
                    msg += f": {err_body[:200]}"
            last_err = msg
            continue
        except Exception as e:
            print(f"[AI Tutor Error] URL: {url}, Model: {cand_model}, Error: {str(e)}")
            last_err = e
            continue

    if last_err is not None:
        pass  # 记录异常并降级使用高质量名师规则解析

    # 若因无网或模型超时失败，返回优质的兜底名师解析
    return get_fallback_explanation(question_type, question_info)
