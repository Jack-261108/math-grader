"""公考速算智能批改系统 Web/移动端服务端
提供移动端 H5 界面、摄像头拍照上传批改接口、静态标注图片资源以及局域网二维码。
"""

import os
import sys
import time
import uuid
import socket
from typing import Optional
import cv2
import numpy as np
import qrcode
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 保证本目录在 sys.path
cur_dir = os.path.dirname(os.path.abspath(__file__))
if cur_dir not in sys.path:
    sys.path.insert(0, cur_dir)

import main
import omr_judge     # type: ignore
import omr_engine    # type: ignore
import omr_renderer  # type: ignore
import json

app = FastAPI(title="公考速算智能批改系统")

# 启用跨域允许局域网设备请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = os.path.join(cur_dir, "output")
static_dir = os.path.join(cur_dir, "static")
docs_dir = os.path.join(cur_dir, "docs")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "uploads"), exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)

app.mount("/output", StaticFiles(directory=output_dir), name="output")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/docs", StaticFiles(directory=docs_dir), name="docs")


@app.get("/")
async def index():
    """返回移动端 H5 主页面"""
    html_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(html_path):
        return JSONResponse({"message": "Frontend static/index.html not found"})
    return FileResponse(html_path)


@app.post("/api/grade")
async def api_grade(
    file: UploadFile = File(...),
    time_str: str = Form("23分18秒"),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """接收手机拍照图片并执行自动批改。
    支持客户端 Bring-Your-Own-Key (BYOK) 模式：
    传入的 api_base_url 与 api_key 仅在当前请求内存中临时用于调用多模态模型，
    绝不进行磁盘持久化或写入日志，保证多用户部署下的安全与隔离。
    """
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="图片格式不正确，无法读取")

        task_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        raw_upload_path = os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg")
        cv2.imwrite(raw_upload_path, img)

        # 执行批改流水线
        result_data = main.process_sheet(
            img,
            task_id,
            output_dir=output_dir,
            time_str=time_str,
            model=model,
            api_base_url=api_base_url,
            api_key=api_key
        )

        # 整理错题清单与归因分析
        wrong_items = []
        for it in result_data.get("items", []):
            if it.get("is_correct") is False and it.get("status") != "unknown":
                op_map = {"mul": "×", "add": "+", "sub": "-", "div1": "÷", "div2": "÷"}
                op_sym = op_map.get(it.get("op_type"), it.get("op_type"))
                wrong_items.append({
                    "row_num": it.get("row_num"),
                    "col_idx": it.get("col_idx"),
                    "op_type": it.get("op_type"),
                    "op_symbol": op_sym,
                    "a": it.get("a"),
                    "b": it.get("b"),
                    "expected": it.get("expected"),
                    "student_raw": it.get("student_raw"),
                    "expression": f"{it.get('a')} {op_sym} {it.get('b')}",
                    "error_type": it.get("error_type", "calculation_error"),
                    "error_name": it.get("error_name", "计算偏差"),
                    "diagnosis": it.get("diagnosis", ""),
                    "advice": it.get("advice", "")
                })

        return {
            "status": "success",
            "task_id": task_id,
            "title": result_data["title"],
            "summary": result_data["summary"],
            "diagnosis": result_data.get("diagnosis", {}),
            "wrong_items": wrong_items,
            "scan_url": f"/output/{task_id}_annotated_scan.jpg",
            "orig_url": f"/output/{task_id}_annotated_original.jpg",
            "report_url": f"/output/{task_id}_report.json",
            "items_count": len(result_data.get("items", []))
        }
    except ValueError as ve:
        # 友好的配置或参数校验异常（如未设置 API Key）
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批改处理失败: {str(e)}")


@app.get("/api/omr/presets")
async def api_omr_presets():
    """获取所有内置的行测考试预设模板及模块配置"""
    return {
        "status": "success",
        "presets": omr_judge.DEFAULT_PRESETS
    }


@app.post("/api/omr/parse_answer_image")
async def api_parse_answer_image(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """接收机构标准答案截图（如四海/粉笔新大纲答案表），通过多模态视觉模型智能提取标准答案并结构化返回。"""
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="答案图片格式不正确，无法读取")

        extracted = omr_engine.recognize_answer_key_image(
            img,
            model=model,
            base_url=api_base_url,
            api_key=api_key
        )
        return {
            "status": "success",
            "formatted_text": extracted.get("formatted_text", ""),
            "suggested_preset": extracted.get("suggested_preset", "dagang_120"),
            "total_detected": extracted.get("total_detected", 0),
            "answers": extracted.get("answers", {})
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"答案截图识别提取失败: {str(e)}")


@app.post("/api/grade/omr")
async def api_grade_omr(
    file: UploadFile = File(...),
    answer_key: str = Form(...),
    preset_id: Optional[str] = Form("guokao_135"),
    sections_json: Optional[str] = Form(None),
    exam_title: Optional[str] = Form(None),
    time_str: str = Form("110分00秒"),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    mock: Optional[int] = Form(0)
):
    """接收公考行测选择题填涂卡/答题纸照片并执行自动识别、分模块计分与电子答题卡生成。

    支持多模块配置与每题分值自定义（常识、言语、数量、判断、资料）；
    标准答案支持连续字母（如 BACDD...）或题号段落（如 1-5: BACDD...）；
    返回全卷总分、各模块实得分率、做错/漏填分布及高保真电子答题卡报告图。
    """
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="答题卡图片格式不正确，无法读取")

        task_id = f"omr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        raw_upload_path = os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg")
        cv2.imwrite(raw_upload_path, img)

        # 1. 解析模块配置
        sections_config = None
        if sections_json and sections_json.strip():
            try:
                sections_config = json.loads(sections_json)
            except Exception:
                pass

        if not sections_config:
            preset = omr_judge.DEFAULT_PRESETS.get(preset_id or "guokao_135", omr_judge.DEFAULT_PRESETS["guokao_135"])
            sections_config = preset["sections"]
            if not exam_title:
                exam_title = preset["name"]

        if not exam_title:
            exam_title = "公考《行测》选择题答题卡诊断报告"

        # 计算整卷预期题数
        total_questions = max((s["end_q"] for s in sections_config), default=135)

        # 2. 解析用户输入的标准答案
        parsed_std_answers = omr_judge.parse_answer_key(answer_key, total_questions)
        if not parsed_std_answers:
            raise HTTPException(status_code=400, detail="未能解析出有效的标准答案，请输入正确答案（例如 BACDDACBDD 或 1-5: BACDD）")

        # 3. 获取学生填涂答案 (真实调用或 mock 模拟)
        if mock == 1:
            student_answers = {}
            for q_i in range(1, total_questions + 1):
                std = parsed_std_answers.get(q_i, "A")
                if q_i % 18 == 0:
                    student_answers[q_i] = None  # 漏涂
                elif q_i % 23 == 0:
                    student_answers[q_i] = "multiple"  # 多涂
                elif q_i % 4 == 0:
                    # 错选
                    options = [o for o in ["A", "B", "C", "D"] if o != std]
                    student_answers[q_i] = options[q_i % len(options)]
                else:
                    student_answers[q_i] = std  # 选对
        else:
            student_answers = omr_engine.recognize_omr_sheet(
                img,
                expected_total_q=total_questions,
                model=model,
                base_url=api_base_url,
                api_key=api_key
            )

        # 4. 严格行测分模块规则判题与学情诊断
        judged_data = omr_judge.judge_omr_sheet(
            student_answers,
            parsed_std_answers,
            sections_config=sections_config,
            custom_time_str=time_str
        )

        # 5. 渲染专业电子答题卡报告大图
        card_bgr = omr_renderer.render_omr_report_card(judged_data, exam_title=exam_title)
        card_path = os.path.join(output_dir, f"{task_id}_card.jpg")
        cv2.imwrite(card_path, card_bgr)

        # 6. 持久化数据报告
        report_path = os.path.join(output_dir, f"{task_id}_report.json")
        result_payload = {
            "exam_title": exam_title,
            "summary": judged_data["summary"],
            "section_results": judged_data["section_results"],
            "diagnosis": judged_data["diagnosis"],
            "items": judged_data["items"],
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json"
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "task_id": task_id,
            "exam_title": exam_title,
            "summary": judged_data["summary"],
            "section_results": judged_data["section_results"],
            "diagnosis": judged_data["diagnosis"],
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json",
            "items": judged_data["items"]
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"答题卡批改失败: {str(e)}")


def get_local_ip() -> str:
    """获取本机局域网 IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def print_server_banner(host: str, port: int):
    """在终端打印友好的局域网访问地址和二维码"""
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{port}" if host in ("0.0.0.0", "127.0.0.1") else f"http://{host}:{port}"
    lan_url = f"http://{local_ip}:{port}"

    print("\n" + "=" * 60)
    print(" 🚀 公考速算智能批改系统移动端服务已就绪！")
    print("=" * 60)
    print(f" • 本地访问地址   : {local_url}")
    print(f" • 手机端访问地址 : {lan_url} (需连接同一局域网/WiFi)")
    print("-" * 60)
    print(" 📱 用手机微信/浏览器直接扫描下方二维码打开相机拍照批改:")
    print("-" * 60)

    try:
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(lan_url)
        qr.print_ascii(invert=True)
    except Exception:
        pass

    print("=" * 60 + "\n")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print_server_banner("0.0.0.0", port)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
