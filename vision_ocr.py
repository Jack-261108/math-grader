"""多模态视觉识别模块
调用视觉大模型（通过 Anthropic 协议兼容接口）对整张速算表格进行高精度结构化提取，
提取表格表头题型、各行题目数值 A、B 以及学生手写答案。
"""

import os
import json
import base64
import urllib.request
from typing import Dict, Any, Optional
import cv2
import numpy as np


def _load_dotenv():
    """轻量自动加载项目根目录下的 .env 文件（纯标准库实现，避免外部第三方依赖）"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(base_dir, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


_load_dotenv()


def encode_image_base64(img: np.ndarray, max_side: int = 1800, quality: int = 90) -> str:
    """将 numpy 图像等比缩放并压缩为 JPEG base64 字符串"""
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, encimg = cv2.imencode('.jpg', img, encode_param)
    if not success:
        raise ValueError("图像编码失败")
    return base64.b64encode(encimg.tobytes()).decode('utf-8')


OCR_PROMPT = """这是一张公考速算技巧练习表格（表格通常有表头和20行题目，每行包含多组计算题）。
请仔细识别表格中的每一行（第1行至第20行），提取打印的题目数值（A, B）以及学生手写填写的作答答案。

特别注意：
1. 识别每一行的题组：
   - 如果是乘法/加减混合卷：
     * 题组1：A, B, A×B (运算类型 'mul', 作答列在第3列)
     * 题组2：A, B, A×B (运算类型 'mul', 作答列在第6列)
     * 题组3加法：A, B, A+B (运算类型 'add', 作答列在第9列)
     * 题组3减法：A, B, A-B (运算类型 'sub', 作答列在第10列)
   - 如果是除法/加减卷：
     * 题组1：A, B, A+B (add, 列3) 与 A-B (sub, 列4)
     * 题组2：A, B, A÷B(首位) (div1, 列7)
     * 题组3：A, B, A÷B(首两位) (div2, 列10)
2. 仔细辨识学生手写的真实数字：
   - 负数要带上负号（如 -5, -7, -24）
   - 有修改划痕的以最终写出的数字为准
   - 若未作答则填 null
3. 请严格输出如下 JSON 格式，不要包含任何额外的问候或 markdown 标记外的解释：
```json
{
  "sheet_title": "速算技巧练习 2023 (1)",
  "detected_type": "mul_add_sub",
  "items": [
    {
      "row_num": 1,
      "col_idx": 3,
      "op_type": "mul",
      "a": 62,
      "b": 4,
      "student_ans": "248"
    }
  ]
}
```
必须完整提取全部20行中的所有作答题目（通常总共有60题或80题）。
"""


def recognize_sheet_table(
    img: np.ndarray,
    model: Optional[str] = None,
    timeout: int = 120,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """通过多模态视觉模型识别整个表格的所有题目与手写答案。

    参数优先级：
        1. 显式传入参数 (base_url, api_key) -> 用户浏览器端 localStorage 设置，内存即用即弃；
        2. 本地 .env 文件或系统环境变量 (ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN)；
        3. 若均未配置，抛出友好错误提示引导用户在前端【设置】中填写。

    返回：
        dict 包含：
            - sheet_title: 表格标题
            - items: 识别的所有题目列表
    """
    _load_dotenv()

    # 1. 解析 Base URL
    effective_base_url = (
        base_url.strip() if (base_url and base_url.strip())
        else os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    )
    if not effective_base_url:
        effective_base_url = "https://api.anthropic.com"

    # 2. 解析 API Key
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

    # 3. 解析候选模型
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

    img_b64 = encode_image_base64(img, max_side=1400)
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
                                "text": OCR_PROMPT
                            }
                        ]
                    }
                ]
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers
            )

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            text_content = ""
            for block in resp_data.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")

            if "```json" in text_content:
                json_str = text_content.split("```json")[1].split("```")[0].strip()
            elif "```" in text_content:
                json_str = text_content.split("```")[1].split("```")[0].strip()
            else:
                json_str = text_content.strip()

            try:
                data = json.loads(json_str)
                return data
            except Exception:
                start = text_content.find("{")
                end = text_content.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(text_content[start:end+1])
        except Exception as e:
            last_err = e
            continue

    raise ValueError(f"视觉识别失败，最后报错: {last_err}")
