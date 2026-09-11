"""公考选择题答题卡 / 填涂卡 (OMR) 多模态视觉识别引擎
支持对标准 2B 答题卡、ABCD 选项填涂纸、手写选择题作答卷进行高精度结构化提取。
识别每道题的填涂选项（A, B, C, D），智能区分未作答（null）与多涂（multiple）。
"""

import os
import sys
import re
import json
import urllib.request
from typing import Dict, Optional, Any
import numpy as np

cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

import vision_ocr  # type: ignore
import omr_judge   # type: ignore


OMR_PROMPT_TEMPLATE = """你是一个高精度的选择题答题卡/填涂卡(OMR)识别专家。
这是一张公考《行政职业能力测验》（行测）或其他考试的选择题答题卡照片。
当前答题卡预计题数范围为：第 1 题至第 {total_questions} 题。

请仔细按题号顺序逐题识别学生的作答填涂情况：
1. 每题选项通常为 A、B、C、D 四个单选题选项；
2. 填涂判断准则：
   - 正常清晰填涂：提取填涂的选项字母，如 "A", "B", "C", "D"；
   - 包含手写字母（如写了 A、B、C、D）而非填涂块的答题纸：同样识别其手写的最终字母；
   - 空白未填涂/未作答：输出 null；
   - 多涂（同时涂了两个或以上选项且未擦干净划掉）：输出 "multiple"；
   - 有涂改痕迹的（如用橡皮擦淡或划叉重涂），以最终确认加深的涂墨选项为准。

请务必按题号顺序完整输出所有题目的填涂结果。
请严格输出如下 JSON 格式，不要包含任何额外的问候语或解释：
```json
{{
  "sheet_type": "omr_standard",
  "total_detected": {total_questions},
  "answers": [
    {{"q": 1, "ans": "A"}},
    {{"q": 2, "ans": "B"}},
    {{"q": 3, "ans": null}},
    {{"q": 4, "ans": "multiple"}},
    {{"q": 5, "ans": "D"}}
  ]
}}
```
"""


def recognize_omr_sheet(
    img: np.ndarray,
    expected_total_q: int = 135,
    model: Optional[str] = None,
    timeout: int = 120,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[int, Optional[str]]:
    """调用多模态视觉模型识别填涂卡照片，返回 {题号: 选项} 映射字典。

    参数：
        - img: 手机拍摄的答题卡图像 (cv2 / numpy ndarray)
        - expected_total_q: 预期题数 (如 135, 120, 30, 20)
        - model: 可选指定的模型名称
        - timeout: 请求超时秒数
        - base_url: 客户端自定义 Base URL (BYOK)
        - api_key: 客户端自定义 API Key (BYOK)

    返回：
        Dict[int, Optional[str]]: 如 {1: 'A', 2: 'C', 3: None, 4: 'multiple'}
    """
    vision_ocr._load_dotenv()

    effective_base_url = (
        base_url.strip() if (base_url and base_url.strip())
        else os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    )
    if not effective_base_url:
        effective_base_url = "https://api.anthropic.com"

    effective_api_key = (
        api_key.strip() if (api_key and api_key.strip())
        else os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    )
    if not effective_api_key:
        raise ValueError(
            "未配置 API Key！\n"
            "• 手机/网页端使用：请点击页面右上角【⚙️ 设置】填入您的 API Key（仅保存在您的手机本地浏览器，不上传服务器）；\n"
            "• 服务器命令行使用：请在项目根目录配置 .env 文件或设置环境变量 ANTHROPIC_AUTH_TOKEN。"
        )

    if model and model.strip():
        candidate_models = [model.strip()]
    else:
        env_model = os.environ.get("ANTHROPIC_DEFAULT_MODEL", "").strip()
        if env_model:
            candidate_models = [env_model]
        else:
            candidate_models = [
                "claude-fable-5-dd-hgih-hsalf-8.3-inimeg",
                os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6"),
                "claude-3-5-sonnet-20241022",
                "gemini-2.5-flash"
            ]

    img_b64 = vision_ocr.encode_image_base64(img, max_side=1600)
    prompt = OMR_PROMPT_TEMPLATE.format(total_questions=expected_total_q)

    url = f"{effective_base_url.rstrip('/')}/v1/messages"
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
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": img_b64
                                }
                            },
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

            # 提取结构化数据
            result_map = parse_omr_response_text(content_text)
            if result_map:
                return result_map

        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise RuntimeError(f"答题卡多模态视觉识别请求全部失败: {str(last_err)}")
    return {}


def parse_omr_response_text(raw_text: str) -> Dict[int, Optional[str]]:
    """从模型返回文本中提取结构化答题卡选项映射"""
    if not raw_text:
        return {}

    # 1. 尝试从 markdown json 代码块中提取
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    text_to_parse = json_match.group(1) if json_match else raw_text

    answers_map: Dict[int, Optional[str]] = {}
    try:
        data = json.loads(text_to_parse)
        if isinstance(data, dict):
            # 形式: {"answers": [{"q": 1, "ans": "A"}, ...]}
            ans_list = data.get("answers", [])
            for item in ans_list:
                if isinstance(item, dict):
                    q_num = item.get("q")
                    ans_val = item.get("ans")
                    if q_num is not None:
                        try:
                            qid = int(q_num)
                            if ans_val is None or ans_val == "" or ans_val == "null":
                                answers_map[qid] = None
                            elif str(ans_val).lower() == "multiple":
                                answers_map[qid] = "multiple"
                            else:
                                val_str = str(ans_val).strip().upper()
                                answers_map[qid] = val_str if val_str in "ABCD" else val_str
                        except ValueError:
                            pass
            if answers_map:
                return answers_map
    except Exception:
        pass

    # 2. 正则回退提取: "1: A", "1. B", "1 A"
    line_matches = re.findall(r'(?:第\s*)?(\d+)\s*(?:题)?[\s.:、-]+([A-Da-d]|null|multiple)\b', raw_text)
    for q_str, ans_str in line_matches:
        qid = int(q_str)
        if ans_str.lower() == "null":
            answers_map[qid] = None
        elif ans_str.lower() == "multiple":
            answers_map[qid] = "multiple"
        else:
            answers_map[qid] = ans_str.upper()

    return answers_map


ANSWER_KEY_PROMPT = """你是一个高精度的试卷/模考标准答案提取专家。
这是一张机构（如四海公考、粉笔、华图、中公等）发布的公考《行测》标准参考答案截图。
图中通常包含科目或模块名称（如政治理论、常识判断、言语理解、数量关系、判断推理、资料分析），
以及按题号区间排版的答案，例如：
1--5 CBADC  6--10 DBACA  11--15 DBADC
或
1-5 A B C D A
或
1.A 2.B 3.C ...

请仔细识别图中的所有题号和标准答案：
1. 完整提取所有题目对应的正确选项字母（A、B、C、D）；
2. 保持原图中优雅的模块名称与分段题号区间排版，生成 formatted_text；
3. 统计总题数（如 120 题、135 题等）；
4. 如果检测到包含政治理论模块且共 120 题，推荐预设为 "dagang_120"；若共 135 题推荐 "guokao_135"；共 120 题无政治理论推荐 "shengkao_120"。

请严格输出如下 JSON 格式，不要包含任何多余的问候语或解释：
```json
{
  "total_detected": 120,
  "suggested_preset": "dagang_120",
  "formatted_text": "政治理论(1--15)\\n1--5 CBADC  6--10 DBACA  11--15 DBADC\\n常识判断(16--25)\\n16--20 BBADD  21--25 AACCD\\n言语理解与表达(26--55)\\n26--30 BBACC  31--35 BABDA  36--40 BCDAD\\n41--45 BACAD  46--50 ABDCD  51--55 ABACD\\n数量关系(56--70)\\n56--60 BBCDA  61--65 DBCAA  66--70 CBDAA\\n判断推理(71--100)\\n71--75 DBCAC  76--80 CBCDA  81--85 ADBDD\\n86--90 DCBAB  91--95 ABDCA  96--100 CBADB\\n资料分析(101--120)\\n101--105 CBADC  106--110 DBACA  111--115 DBADC\\n116--120 CABCD",
  "answers": [
    {"q": 1, "ans": "C"},
    {"q": 2, "ans": "B"}
  ]
}
```
"""


def recognize_answer_key_image(
    img: np.ndarray,
    model: Optional[str] = None,
    timeout: int = 120,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """从标准答案照片/截图中自动识别并结构化提取答案文本与选项字典。

    参数：
        - img: 答案截图 (numpy ndarray)
        - model: 可选多模态模型名
        - timeout: 超时秒数
        - base_url: 客户端自定义 Base URL (BYOK)
        - api_key: 客户端自定义 API Key (BYOK)

    返回：
        Dict 包含 formatted_text, total_detected, suggested_preset, answers 字典
    """
    vision_ocr._load_dotenv()

    effective_base_url = (
        base_url.strip() if (base_url and base_url.strip())
        else os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    )
    if not effective_base_url:
        effective_base_url = "https://api.anthropic.com"

    effective_api_key = (
        api_key.strip() if (api_key and api_key.strip())
        else os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    )
    if not effective_api_key:
        raise ValueError(
            "未配置 API Key！\n"
            "• 手机/网页端使用：请点击页面右上角【⚙️ 设置】填入您的 API Key（仅保存在您的手机本地浏览器，不上传服务器）；\n"
            "• 服务器命令行使用：请在项目根目录配置 .env 文件或设置环境变量 ANTHROPIC_AUTH_TOKEN。"
        )

    if model and model.strip():
        candidate_models = [model.strip()]
    else:
        env_model = os.environ.get("ANTHROPIC_DEFAULT_MODEL", "").strip()
        if env_model:
            candidate_models = [env_model]
        else:
            candidate_models = [
                "claude-fable-5-dd-hgih-hsalf-8.3-inimeg",
                os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6"),
                "claude-3-5-sonnet-20241022",
                "gemini-2.5-flash"
            ]

    img_b64 = vision_ocr.encode_image_base64(img, max_side=1600)

    url = f"{effective_base_url.rstrip('/')}/v1/messages"
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
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": img_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": ANSWER_KEY_PROMPT
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

            # 提取结构化数据
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content_text, re.DOTALL)
            text_to_parse = json_match.group(1) if json_match else content_text

            try:
                data = json.loads(text_to_parse)
                if isinstance(data, dict):
                    formatted_text = data.get("formatted_text", "")
                    suggested_preset = data.get("suggested_preset", "dagang_120")
                    ans_list = data.get("answers", [])
                    answers_dict = {}
                    for it in ans_list:
                        if isinstance(it, dict) and "q" in it and "ans" in it:
                            try:
                                answers_dict[int(it["q"])] = str(it["ans"]).upper()
                            except Exception:
                                pass

                    if not formatted_text and answers_dict:
                        # 自动拼装 formatted_text
                        lines = []
                        items_sorted = sorted(answers_dict.items())
                        for i in range(0, len(items_sorted), 5):
                            chunk = items_sorted[i:i+5]
                            s_q = chunk[0][0]
                            e_q = chunk[-1][0]
                            letters = "".join(val for _, val in chunk)
                            lines.append(f"{s_q}--{e_q} {letters}")
                        formatted_text = "\n".join(lines)

                    return {
                        "formatted_text": formatted_text,
                        "suggested_preset": suggested_preset,
                        "total_detected": len(answers_dict),
                        "answers": answers_dict
                    }
            except Exception:
                pass

            # 若直接解析失败，使用通用文本正则解析器
            parsed_fallback = omr_judge.parse_answer_key(content_text)
            if parsed_fallback:
                return {
                    "formatted_text": content_text.strip(),
                    "suggested_preset": "dagang_120" if len(parsed_fallback) == 120 else "guokao_135",
                    "total_detected": len(parsed_fallback),
                    "answers": parsed_fallback
                }

        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise RuntimeError(f"标准答案图片识别失败: {str(last_err)}")
    return {
        "formatted_text": "",
        "suggested_preset": "dagang_120",
        "total_detected": 0,
        "answers": {}
    }
