"""公考速算智能批改系统 Web/移动端服务端
提供移动端 H5 界面、摄像头拍照上传批改接口、静态标注图片资源以及局域网二维码。
"""

import os
import sys
import time
from datetime import datetime
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
import omr_annotator # type: ignore
import ai_tutor      # type: ignore
import vision_ocr     # type: ignore
import json
import urllib.request
from urllib.error import HTTPError

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
    """返回移动端 H5 主页面 (设置禁用缓存响应头，确保移动端即时获取最新代码与图文排版)"""
    html_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(html_path):
        return JSONResponse({"message": "Frontend static/index.html not found"})
    return FileResponse(
        html_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


def check_user_byok_config(api_base_url: Optional[str], api_key: Optional[str]):
    """校验用户个人 Base URL 与 API Key (必须由客户端自行配置)"""
    if not api_base_url or not str(api_base_url).strip() or not api_key or not str(api_key).strip():
        raise HTTPException(
            status_code=400,
            detail="未配置 Base URL 或 API Key，请点击右上角【设置】配置您个人的 Base URL 和 API Key (BYOK)。"
        )


@app.post("/api/test_config")
async def api_test_config(
    api_base_url: str = Form(...),
    api_key: str = Form(...),
    model: Optional[str] = Form(None)
):
    """测试客户端配置的 Base URL 与 API Key 是否能够正常连通模型 API"""
    check_user_byok_config(api_base_url, api_key)
    cand_model = model.strip() if (model and model.strip()) else "claude-3-5-sonnet-20241022"
    url = vision_ocr.build_messages_url(api_base_url)
    headers = {
        "x-api-key": api_key.strip(),
        "authorization": f"Bearer {api_key.strip()}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": cand_model,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "hi"}]
    }
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            elapsed_ms = int((time.time() - t0) * 1000)
            return {
                "status": "success",
                "message": f"连接成功！模型 [{cand_model}] 响应正常 (耗时 {elapsed_ms}ms)",
                "url": url,
                "model": cand_model,
                "elapsed_ms": elapsed_ms
            }
    except HTTPError as he:
        err_body = ""
        try:
            err_body = he.read().decode('utf-8', errors='ignore')
        except Exception:
            pass
        print(f"[Test Config HTTPError] URL: {url}, Model: {cand_model}, Code: {he.code}, Reason: {he.reason}, Body: {err_body[:300]}")
        detail_msg = f"HTTP {he.code} ({he.reason})"
        if err_body:
            try:
                err_json = json.loads(err_body)
                if isinstance(err_json, dict) and "error" in err_json:
                    e_val = err_json["error"]
                    if isinstance(e_val, dict):
                        detail_msg += f": {e_val.get('message') or e_val.get('type') or str(e_val)}"
                    else:
                        detail_msg += f": {e_val}"
                else:
                    detail_msg += f": {err_body[:200]}"
            except Exception:
                detail_msg += f": {err_body[:200]}"
        return {
            "status": "error",
            "code": he.code,
            "url": url,
            "model": cand_model,
            "detail": detail_msg
        }
    except Exception as e:
        print(f"[Test Config Error] URL: {url}, Model: {cand_model}, Error: {str(e)}")
        return {
            "status": "error",
            "url": url,
            "model": cand_model,
            "detail": f"连接异常: {str(e)}"
        }


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
    check_user_byok_config(api_base_url, api_key)
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
    check_user_byok_config(api_base_url, api_key)
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"答案截图识别提取失败: {str(e)}")


@app.post("/api/omr/recognize")
async def api_omr_recognize(
    file: UploadFile = File(...),
    preset_id: Optional[str] = Form("guokao_135"),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """仅执行答题卡视觉识别与物理灰度校准，返回识别出的每题作答，方便用户提前核对与纠正"""
    check_user_byok_config(api_base_url, api_key)
    try:
        task_id = f"omr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="上传图片内容为空")

        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="图片格式无法解析，请重新上传")

        raw_upload_path = os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg")
        cv2.imwrite(raw_upload_path, img)

        preset = omr_judge.DEFAULT_PRESETS.get(preset_id or "guokao_135", omr_judge.DEFAULT_PRESETS["guokao_135"])
        total_questions = max((s["end_q"] for s in preset["sections"]), default=135)

        student_answers, grid_layout = omr_engine.recognize_omr_sheet(
            img,
            expected_total_q=total_questions,
            model=model,
            base_url=api_base_url,
            api_key=api_key,
            return_layout=True
        )

        student_answers = omr_annotator.refine_student_answers_with_cv(
            img,
            student_answers,
            grid_layout=grid_layout
        )

        return {
            "status": "success",
            "raw_task_id": task_id,
            "student_answers": student_answers,
            "total_detected": len(student_answers),
            "message": f"成功识别 {len(student_answers)} 道题目的填涂作答！"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"答题卡填涂识别失败: {str(e)}")


@app.post("/api/grade/omr")
async def api_grade_omr(
    file: Optional[UploadFile] = File(None),
    answer_key: Optional[str] = Form(None),
    student_answers_json: Optional[str] = Form(None),
    raw_task_id: Optional[str] = Form(None),
    preset_id: Optional[str] = Form("guokao_135"),
    sections_json: Optional[str] = Form(None),
    exam_title: Optional[str] = Form(None),
    time_str: str = Form("110分00秒"),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    mock: Optional[int] = Form(0)
):
    """接收公考行测选择题答题卡照片或在线作答数据并执行自动判分、分模块计分与答题卡批注。

    核心能力支持：
      1. 答题卡照片扫描识别 (file: 上传答题卡照片进行多模态 OMR 识别)；
      2. 在线填涂作答输入 (student_answers_json: {"1": "A", "2": "B", ...})；
      3. 基于原图重判纠错 (raw_task_id: 引用原上传答题卡照片，配合已纠正的 student_answers_json 重算重绘)；
      4. 电子答题卡还原与答题卡全景图红笔批注（在实体答题卡照片或高保真仿真卡上绘制绿勾对号、红叉与正解）。
    """
    try:
        effective_raw_task_id = raw_task_id.strip() if (raw_task_id and raw_task_id.strip()) else None
        task_id = f"omr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        img = None
        if file is not None and hasattr(file, "read") and getattr(file, "filename", None):
            try:
                content = await file.read()
                if content:
                    nparr = np.frombuffer(content, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is not None:
                        effective_raw_task_id = task_id
                        raw_upload_path = os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg")
                        cv2.imwrite(raw_upload_path, img)
            except Exception:
                pass
        elif effective_raw_task_id:
            # 加载原上传的答题卡底图用于纠错后重新批注
            cached_raw = os.path.join(output_dir, "uploads", f"{effective_raw_task_id}_raw.jpg")
            if os.path.exists(cached_raw):
                img = cv2.imread(cached_raw)

        # 参数兼容性处理
        sections_str = sections_json if isinstance(sections_json, str) else None
        stu_ans_str = student_answers_json if isinstance(student_answers_json, str) else None
        preset_id_str = preset_id if isinstance(preset_id, str) else "guokao_135"
        exam_title_str = exam_title if isinstance(exam_title, str) else None
        time_str_val = time_str if isinstance(time_str, str) else "110分00秒"
        ans_key_str = answer_key if isinstance(answer_key, str) else str(getattr(answer_key, "default", ""))

        if not stu_ans_str and img is None and mock != 1:
            raise HTTPException(status_code=400, detail="请上传答题卡照片或提供在线填涂作答数据")

        # 1. 解析模块配置
        sections_config = None
        if sections_str and sections_str.strip():
            try:
                sections_config = json.loads(sections_str)
            except Exception:
                pass

        if not sections_config:
            preset = omr_judge.DEFAULT_PRESETS.get(preset_id_str or "guokao_135", omr_judge.DEFAULT_PRESETS["guokao_135"])
            sections_config = preset["sections"]
            if not exam_title_str:
                exam_title_str = preset["name"]

        if not exam_title_str:
            exam_title_str = "公考《行测》选择题答题卡诊断报告"

        # 计算整卷预期题数
        total_questions = max((s["end_q"] for s in sections_config), default=135)

        # 2. 解析标准答案
        parsed_std_answers = omr_judge.parse_answer_key(ans_key_str, total_questions)
        if not parsed_std_answers:
            raise HTTPException(status_code=400, detail="未能解析出有效的标准答案，请输入正确答案（例如 BACDDACBDD 或 1-5: BACDD）")

        # 3. 获取学生填涂答案 (在线交互作答、照片视觉识别或 mock 模拟)
        grid_layout = None
        if stu_ans_str and stu_ans_str.strip():
            try:
                raw_ans = json.loads(stu_ans_str)
                student_answers = {}
                for q_i in range(1, total_questions + 1):
                    val = raw_ans.get(str(q_i)) if str(q_i) in raw_ans else raw_ans.get(q_i)
                    if val and str(val).strip():
                        student_answers[q_i] = str(val).strip().upper()
                    else:
                        student_answers[q_i] = None  # 漏涂/未作答
            except Exception as parse_e:
                raise HTTPException(status_code=400, detail=f"在线作答数据解析错误: {str(parse_e)}")
        elif mock == 1:
            student_answers = {}
            for q_i in range(1, total_questions + 1):
                std = parsed_std_answers.get(q_i, "A")
                if q_i % 18 == 0:
                    student_answers[q_i] = None  # 漏涂
                elif q_i % 23 == 0:
                    student_answers[q_i] = "multiple"  # 多涂
                elif q_i % 4 == 0:
                    options = [o for o in ["A", "B", "C", "D"] if o != std]
                    student_answers[q_i] = options[q_i % len(options)]
                else:
                    student_answers[q_i] = std  # 选对
        else:
            if img is None:
                raise HTTPException(status_code=400, detail="答题卡图片格式不正确，无法读取")
            check_user_byok_config(api_base_url, api_key)
            student_answers, grid_layout = omr_engine.recognize_omr_sheet(
                img,
                expected_total_q=total_questions,
                model=model,
                base_url=api_base_url,
                api_key=api_key,
                return_layout=True
            )

        # 结合物理石墨反差与网格坐标自适应校准
        if img is not None and student_answers and not (stu_ans_str and stu_ans_str.strip()):
            student_answers = omr_annotator.refine_student_answers_with_cv(
                img,
                student_answers,
                grid_layout=grid_layout
            )

        # 4. 严格行测分模块规则判题与学情诊断
        judged_data = omr_judge.judge_omr_sheet(
            student_answers,
            parsed_std_answers,
            sections_config=sections_config,
            custom_time_str=time_str_val
        )

        # 5. 渲染批注答题卡全景图（在用户上传的真实答题卡原图上红绿批改对错；若纯在线做题未传图，则生成高保真仿真批注卡）
        if img is not None:
            card_bgr = omr_annotator.annotate_user_omr_sheet(
                img,
                judged_data,
                grid_layout=grid_layout
            )
        else:
            card_bgr = omr_annotator.generate_annotated_synthetic_omr_sheet(
                judged_data,
                preset_id=preset_id_str or "guokao_135"
            )
        card_path = os.path.join(output_dir, f"{task_id}_card.jpg")
        cv2.imwrite(card_path, card_bgr)

        # 6. 持久化数据报告
        report_path = os.path.join(output_dir, f"{task_id}_report.json")
        result_payload = {
            "task_id": task_id,
            "raw_task_id": effective_raw_task_id or task_id,
            "exam_title": exam_title_str,
            "summary": judged_data["summary"],
            "section_results": judged_data["section_results"],
            "diagnosis": judged_data["diagnosis"],
            "student_answers": student_answers,
            "items": judged_data["items"],
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json"
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "task_id": task_id,
            "raw_task_id": effective_raw_task_id or task_id,
            "exam_title": exam_title_str,
            "summary": judged_data["summary"],
            "section_results": judged_data["section_results"],
            "diagnosis": judged_data["diagnosis"],
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json",
            "student_answers": student_answers,
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


@app.post("/api/ai/explain")
async def api_ai_explain(
    question_type: str = Form("math"),
    question_info: str = Form(...),
    user_query: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    api_base_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """为做错的题目生成名师秒杀解法、考因透视与避坑指南。
    支持客户端 BYOK 本地密钥隔离，调用多模态/大语言模型提供深度点拨。
    """
    check_user_byok_config(api_base_url, api_key)
    try:
        q_data = json.loads(question_info) if isinstance(question_info, str) else {}
        explanation = ai_tutor.explain_mistake(
            question_type=question_type,
            question_info=q_data,
            user_query=user_query,
            model=model,
            base_url=api_base_url,
            api_key=api_key
        )
        return {
            "status": "success",
            "explanation": explanation
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"名师解析生成失败: {str(e)}")


@app.get("/api/history")
async def api_get_history(
    type: Optional[str] = "all",  # 'all' | 'omr' | 'math'
    limit: int = 50
):
    """获取所有历史判题记录摘要列表，按创建时间倒序排列"""
    try:
        records = []
        if not os.path.exists(output_dir):
            return {"status": "success", "records": [], "total_count": 0}

        filenames = [f for f in os.listdir(output_dir) if f.endswith("_report.json")]
        for fname in filenames:
            file_path = os.path.join(output_dir, fname)
            try:
                mtime = os.path.getmtime(file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                task_id = data.get("task_id") or fname[:-12]
                is_omr = str(task_id).startswith("omr_") or "card_url" in data or "section_results" in data
                rec_type = "omr" if is_omr else "math"

                if type != "all" and rec_type != type:
                    continue

                if is_omr:
                    summary = data.get("summary", {})
                    title = data.get("exam_title") or "行测答题卡诊断"
                    earned = summary.get("total_earned_score", 0)
                    pct = summary.get("score_ratio_pct", 0)
                    score_str = f"{earned}分 ({pct}%)"
                    grade = summary.get("grade_badge", "B")
                    total_q = summary.get("total_questions", len(data.get("items", [])))
                    correct_q = summary.get("total_correct", 0)
                    wrong_q = summary.get("total_wrong", 0)
                    unans_q = summary.get("total_unanswered", 0)
                    img_url = data.get("card_url") or f"/output/{task_id}_card.jpg"
                else:
                    summary = data.get("summary", {})
                    title = data.get("title") or "速算技巧练习"
                    acc = summary.get("accuracy", "0%")
                    score_str = f"正确率 {acc}"
                    grade = summary.get("grade", "B")
                    total_q = summary.get("total", len(data.get("items", [])))
                    correct_q = summary.get("correct", 0)
                    wrong_q = summary.get("wrong", 0)
                    unans_q = summary.get("unknown", 0)
                    img_url = data.get("scan_url") or f"/output/{task_id}_annotated_scan.jpg"

                created_at = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                records.append({
                    "task_id": task_id,
                    "type": rec_type,
                    "title": title,
                    "score_str": score_str,
                    "grade": grade,
                    "total_q": total_q,
                    "correct_q": correct_q,
                    "wrong_q": wrong_q,
                    "unans_q": unans_q,
                    "created_at": created_at,
                    "mtime": mtime,
                    "img_url": img_url
                })
            except Exception:
                continue

        # 按时间倒序
        records.sort(key=lambda x: x["mtime"], reverse=True)
        results = []
        for r in records[:limit]:
            item = dict(r)
            item.pop("mtime", None)
            results.append(item)

        return {
            "status": "success",
            "total_count": len(records),
            "records": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@app.get("/api/history/{task_id}")
async def api_get_history_detail(task_id: str):
    """获取指定判题任务的完整报告数据"""
    if "/" in task_id or "\\" in task_id or ".." in task_id:
        raise HTTPException(status_code=400, detail="非法的任务ID")

    report_file = os.path.join(output_dir, f"{task_id}_report.json")
    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail="未找到该历史判题报告")
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取报告失败: {str(e)}")


@app.delete("/api/history/{task_id}")
async def api_delete_history(task_id: str):
    """删除指定的判题历史记录及相关图片"""
    if "/" in task_id or "\\" in task_id or ".." in task_id:
        raise HTTPException(status_code=400, detail="非法的任务ID")

    files_to_remove = [
        os.path.join(output_dir, f"{task_id}_report.json"),
        os.path.join(output_dir, f"{task_id}_card.jpg"),
        os.path.join(output_dir, f"{task_id}_annotated_scan.jpg"),
        os.path.join(output_dir, f"{task_id}_annotated_original.jpg"),
        os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg"),
    ]
    deleted_count = 0
    for fp in files_to_remove:
        if os.path.exists(fp):
            try:
                os.remove(fp)
                deleted_count += 1
            except Exception:
                pass

    return {
        "status": "success",
        "message": f"已删除历史记录及关联资源 ({deleted_count} 个文件)"
    }



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


UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s [%(levelname)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print_server_banner("0.0.0.0", port)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False, log_config=UVICORN_LOG_CONFIG)
