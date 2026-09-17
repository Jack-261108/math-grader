"""公考速算智能批改系统 Web/移动端服务端
提供移动端 H5 界面、摄像头拍照上传批改接口、静态标注图片资源以及局域网二维码。
"""

import os
import sys
import time
import logging
from datetime import datetime
import uuid
import socket
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import cv2
import numpy as np
import qrcode
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 初始化标准业务 Logger
logger = logging.getLogger("math-grader")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(_handler)

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
dist_dir = os.path.join(static_dir, "dist")
dist_assets_dir = os.path.join(dist_dir, "assets")
docs_dir = os.path.join(cur_dir, "docs")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "uploads"), exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(dist_dir, exist_ok=True)
os.makedirs(dist_assets_dir, exist_ok=True)
os.makedirs(docs_dir, exist_ok=True)

class OutputStaticFiles(StaticFiles):
    """继承 StaticFiles，在静态输出资产 404 缺失时记录业务告警日志，便于可观测性监控与排查"""
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                client = scope.get("client")
                client_ip = client[0] if client else "unknown"
                logger.warning(f"[Static-Output] 请求的静态标注资产不存在 (404): path=/output/{path}, client={client_ip}")
            raise


app.mount("/output", OutputStaticFiles(directory=output_dir), name="output")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/assets", StaticFiles(directory=dist_assets_dir), name="assets")
app.mount("/docs", StaticFiles(directory=docs_dir), name="docs")


@app.get("/")
@app.get("/math")
@app.get("/omr")
async def index():
    """返回移动端 H5 主页面 (优先返回 Vue3 构建产物 static/dist/index.html，设置禁用缓存响应头)"""
    dist_html_path = os.path.join(dist_dir, "index.html")
    legacy_html_path = os.path.join(static_dir, "index.html")

    target_html = dist_html_path if os.path.exists(dist_html_path) else legacy_html_path

    if not os.path.exists(target_html):
        return JSONResponse({"message": "Frontend index.html not found"})
    return FileResponse(
        target_html,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


def mask_target_url(url: Optional[str]) -> str:
    """脱敏展示 API 端点，保留协议与域名路径，防止敏感凭据泄漏"""
    if not url:
        return ""
    try:
        p = urlparse(str(url))
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return str(url)[:40]


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
    masked_url = mask_target_url(url)
    logger.info(f"[BYOK-Test] 发起模型连通性测试: target={masked_url}, model={cand_model}")
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
            logger.info(f"[BYOK-Test] 测试成功: model={cand_model}, 耗时={elapsed_ms}ms")
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
        logger.warning(f"[BYOK-Test] 测试未通过 (HTTPError): model={cand_model}, code={he.code}, reason={he.reason}, detail={detail_msg}")
        return {
            "status": "error",
            "code": he.code,
            "url": url,
            "model": cand_model,
            "detail": detail_msg
        }
    except Exception as e:
        logger.warning(f"[BYOK-Test] 测试发生异常: model={cand_model}, error={str(e)}")
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
    t_start = time.time()
    filename = getattr(file, "filename", "upload.jpg")
    task_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    logger.info(f"[Math-Grade] 收到速算批改请求: task_id={task_id}, file={filename}, time_str={time_str}, model={model or 'default'}")
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning(f"[Math-Grade] 图片解码失败: task_id={task_id}, file={filename}")
            raise HTTPException(status_code=400, detail="图片格式不正确，无法读取")

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

        elapsed_ms = int((time.time() - t_start) * 1000)
        items_count = len(result_data.get("items", []))
        summary = result_data.get("summary", {})
        accuracy = summary.get("accuracy_pct", summary.get("accuracy", "N/A"))
        grade = summary.get("grade_level", summary.get("grade", "N/A"))

        scan_file = os.path.join(output_dir, f"{task_id}_annotated_scan.jpg")
        if not os.path.exists(scan_file):
            logger.error(f"[Math-Grade] 标注图片文件缺失或写入失败: {scan_file}")
            raise HTTPException(status_code=500, detail="标注图片生成失败，磁盘文件缺失")

        logger.info(f"[Math-Grade] 批改完成: task_id={task_id}, 题数={items_count}, 正确率={accuracy}%, 等级={grade}, 错题数={len(wrong_items)}, 耗时={elapsed_ms}ms")

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
            "items_count": items_count
        }
    except ValueError as ve:
        logger.warning(f"[Math-Grade] 参数校验未通过: task_id={task_id}, error={str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Math-Grade] 批改处理异常: task_id={task_id}, error={str(e)}")
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
    t_start = time.time()
    filename = getattr(file, "filename", "answer_key.jpg")
    logger.info(f"[OMR-OCR] 收到答案截图 OCR 请求: file={filename}, model={model or 'default'}")
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning(f"[OMR-OCR] 答案图片解码失败: file={filename}")
            raise HTTPException(status_code=400, detail="答案图片格式不正确，无法读取")

        extracted = omr_engine.recognize_answer_key_image(
            img,
            model=model,
            base_url=api_base_url,
            api_key=api_key
        )
        elapsed_ms = int((time.time() - t_start) * 1000)
        total_detected = extracted.get("total_detected", 0)
        suggested_preset = extracted.get("suggested_preset", "dagang_120")
        logger.info(f"[OMR-OCR] 答案提取成功: 识别题数={total_detected}, 建议预设={suggested_preset}, 耗时={elapsed_ms}ms")
        return {
            "status": "success",
            "formatted_text": extracted.get("formatted_text", ""),
            "suggested_preset": suggested_preset,
            "total_detected": total_detected,
            "answers": extracted.get("answers", {})
        }
    except ValueError as ve:
        logger.warning(f"[OMR-OCR] 参数校验未通过: error={str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[OMR-OCR] 答案截图识别提取异常: error={str(e)}")
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
    t_start = time.time()
    task_id = f"omr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    filename = getattr(file, "filename", "card.jpg")
    logger.info(f"[OMR-Recognize] 收到答题卡填涂预审请求: task_id={task_id}, file={filename}, preset={preset_id}")
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="上传图片内容为空")

        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning(f"[OMR-Recognize] 图片格式无法解析: task_id={task_id}")
            raise HTTPException(status_code=400, detail="图片格式无法解析，请重新上传")

        raw_upload_path = os.path.join(output_dir, "uploads", f"{task_id}_raw.jpg")
        cv2.imwrite(raw_upload_path, img)

        preset = omr_judge.DEFAULT_PRESETS.get(preset_id or "guokao_135", omr_judge.DEFAULT_PRESETS["guokao_135"])
        total_questions = max((s["end_q"] for s in preset["sections"]), default=135)

        student_answers, grid_layout, hybrid_stats = omr_engine.hybrid_recognize_omr_sheet(
            img,
            expected_total_q=total_questions,
            model=model,
            base_url=api_base_url,
            api_key=api_key,
            return_layout=True,
            return_stats=True
        )

        student_answers = omr_annotator.refine_student_answers_with_cv(
            img,
            student_answers,
            grid_layout=grid_layout
        )

        elapsed_ms = int((time.time() - t_start) * 1000)
        logger.info(
            f"[OMR-Recognize] 填涂预审完成: task_id={task_id}, 识别题数={len(student_answers)}/{total_questions}, "
            f"模式={hybrid_stats.get('mode')}, 本地直出={hybrid_stats.get('local_resolved')}题, "
            f"靶向审验={hybrid_stats.get('reviewed_count')}题, Token节约率={hybrid_stats.get('token_saved_pct')}%, "
            f"耗时={elapsed_ms}ms"
        )
        return {
            "status": "success",
            "raw_task_id": task_id,
            "student_answers": student_answers,
            "total_detected": len(student_answers),
            "hybrid_stats": hybrid_stats,
            "message": f"成功识别 {len(student_answers)} 道题目的填涂作答 (Token节约 {hybrid_stats.get('token_saved_pct', 0)}%)！"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[OMR-Recognize] 答题卡填涂预审异常: task_id={task_id}, error={str(e)}")
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
    time_data_json: Optional[str] = Form(None),
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
    t_start = time.time()
    raw_task_id_str = raw_task_id if isinstance(raw_task_id, str) else None
    effective_raw_task_id = raw_task_id_str.strip() if (raw_task_id_str and raw_task_id_str.strip()) else None
    task_id = f"omr_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # 参数兼容性处理
    sections_str = sections_json if isinstance(sections_json, str) else None
    stu_ans_str = student_answers_json if isinstance(student_answers_json, str) else None
    preset_id_str = preset_id if isinstance(preset_id, str) else "guokao_135"
    exam_title_str = exam_title if isinstance(exam_title, str) else None
    time_str_val = time_str if isinstance(time_str, str) else "110分00秒"
    ans_key_str = answer_key if isinstance(answer_key, str) else str(getattr(answer_key, "default", ""))

    time_data_dict: Optional[Dict[str, Any]] = None
    if time_data_json and isinstance(time_data_json, str) and time_data_json.strip():
        try:
            time_data_dict = json.loads(time_data_json)
        except Exception as tde:
            logger.warning(f"[OMR-Grade] time_data_json 解析失败: task_id={task_id}, error={tde}")

    mode = "图片识别" if (file is not None and getattr(file, "filename", None)) else ("在线作答" if (stu_ans_str and stu_ans_str.strip()) else ("Mock模拟" if mock == 1 else "重判纠错"))
    hybrid_stats: Optional[Dict[str, Any]] = None
    grid_layout: Optional[Dict[str, Any]] = None
    logger.info(f"[OMR-Grade] 收到答题卡判分请求: task_id={task_id}, mode={mode}, preset={preset_id_str or 'guokao_135'}, raw_task_id={effective_raw_task_id or 'none'}")
    try:
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

        if not stu_ans_str and img is None and mock != 1:
            logger.warning(f"[OMR-Grade] 缺少答题数据或图片: task_id={task_id}")
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
            logger.warning(f"[OMR-Grade] 未能解析出标准答案: task_id={task_id}")
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
                logger.warning(f"[OMR-Grade] 在线作答解析错误: task_id={task_id}, error={parse_e}")
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
            student_answers, grid_layout, hybrid_stats = omr_engine.hybrid_recognize_omr_sheet(
                img,
                expected_total_q=total_questions,
                model=model,
                base_url=api_base_url,
                api_key=api_key,
                return_layout=True,
                return_stats=True
            )

        # 结合物理石墨反差与网格坐标自适应校准（最后一道物理双保险）
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
            custom_time_str=time_str_val,
            time_data=time_data_dict
        )
        if hybrid_stats:
            judged_data.setdefault("summary", {})["hybrid_stats"] = hybrid_stats

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
            "timing_analysis": judged_data.get("timing_analysis"),
            "student_answers": student_answers,
            "items": judged_data["items"],
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json"
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, ensure_ascii=False, indent=2)

        elapsed_ms = int((time.time() - t_start) * 1000)
        smry = judged_data.get("summary", {})
        earned_score = smry.get("total_earned_score", 0)
        full_score = smry.get("total_full_score", 100)
        score_ratio = smry.get("score_ratio_pct", 0)
        grade_badge = smry.get("grade_badge", "B")
        tot_correct = smry.get("total_correct", 0)
        tot_wrong = smry.get("total_wrong", 0)
        tot_unans = smry.get("total_unanswered", 0)
        logger.info(f"[OMR-Grade] 判分与批注完成: task_id={task_id}, 试卷={exam_title_str}, 得分={earned_score}/{full_score}分 ({score_ratio}%), 等级={grade_badge}, 对/错/空={tot_correct}/{tot_wrong}/{tot_unans}, 耗时={elapsed_ms}ms")

        return {
            "status": "success",
            "task_id": task_id,
            "raw_task_id": effective_raw_task_id or task_id,
            "exam_title": exam_title_str,
            "summary": judged_data["summary"],
            "section_results": judged_data["section_results"],
            "diagnosis": judged_data["diagnosis"],
            "timing_analysis": judged_data.get("timing_analysis"),
            "card_url": f"/output/{task_id}_card.jpg",
            "report_url": f"/output/{task_id}_report.json",
            "student_answers": student_answers,
            "items": judged_data["items"]
        }

    except ValueError as ve:
        logger.warning(f"[OMR-Grade] 参数校验未通过: task_id={task_id}, error={str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[OMR-Grade] 答题卡批改异常: task_id={task_id}, error={str(e)}")
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
    t_start = time.time()
    logger.info(f"[AI-Tutor] 收到名师秒杀解析请求: type={question_type}, model={model or 'default'}")
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
        elapsed_ms = int((time.time() - t_start) * 1000)
        logger.info(f"[AI-Tutor] 名师解析生成成功: type={question_type}, 耗时={elapsed_ms}ms")
        return {
            "status": "success",
            "explanation": explanation
        }
    except ValueError as ve:
        logger.warning(f"[AI-Tutor] 参数校验未通过: error={str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[AI-Tutor] 名师解析生成异常: error={str(e)}")
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
                    correct_q = summary.get("correct", 0)
                    wrong_q = summary.get("wrong", 0)
                    unans_q = summary.get("unknown", 0)
                    total_q = summary.get("total", len(data.get("items", [])))

                    raw_acc = summary.get("accuracy_pct", summary.get("accuracy"))
                    if raw_acc is not None:
                        score_str = f"正确率 {raw_acc}%" if "%" not in str(raw_acc) else f"正确率 {raw_acc}"
                    else:
                        answered = correct_q + wrong_q
                        calc_acc = round(correct_q / answered * 100.0, 1) if answered > 0 else 0.0
                        score_str = f"正确率 {calc_acc}%"

                    grade = summary.get("grade_level") or summary.get("grade") or summary.get("grade_badge") or "B"
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

        logger.info(f"[History] 查询判题历史: type={type}, limit={limit}, 返回条数={len(results)}/{len(records)}")
        return {
            "status": "success",
            "total_count": len(records),
            "records": results
        }
    except Exception as e:
        logger.exception(f"[History] 获取历史记录失败: error={str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@app.get("/api/history/{task_id}")
async def api_get_history_detail(task_id: str):
    """获取指定判题任务的完整报告数据"""
    if "/" in task_id or "\\" in task_id or ".." in task_id:
        logger.warning(f"[History] 非法任务ID请求: task_id={task_id}")
        raise HTTPException(status_code=400, detail="非法的任务ID")

    report_file = os.path.join(output_dir, f"{task_id}_report.json")
    if not os.path.exists(report_file):
        logger.warning(f"[History] 报告文件不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="未找到该历史判题报告")
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 补齐 task_id 与资源静态访问 URL，确保前端从历史记录回溯还原时大图与错题正常展示
        data["task_id"] = task_id
        if str(task_id).startswith("omr_") or "section_results" in data:
            data.setdefault("card_url", f"/output/{task_id}_card.jpg")
            data.setdefault("report_url", f"/output/{task_id}_report.json")
        else:
            data.setdefault("scan_url", f"/output/{task_id}_annotated_scan.jpg")
            data.setdefault("orig_url", f"/output/{task_id}_annotated_original.jpg")
            data.setdefault("report_url", f"/output/{task_id}_report.json")
            if "wrong_items" not in data and "items" in data:
                wrong_items = []
                for it in data.get("items", []):
                    if it.get("status") == "wrong":
                        op_type = it.get("op_type", "add")
                        op_sym = "×" if op_type == "mul" else ("÷" if "div" in op_type else ("+" if op_type == "add" else "-"))
                        wrong_items.append({
                            "row_num": it.get("row_num"),
                            "col_idx": it.get("col_idx"),
                            "op_type": op_type,
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
                data["wrong_items"] = wrong_items

        logger.info(f"[History] 获取历史报告详情成功: task_id={task_id}")
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        logger.exception(f"[History] 读取报告失败: task_id={task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"读取报告失败: {str(e)}")


@app.delete("/api/history/{task_id}")
async def api_delete_history(task_id: str):
    """删除指定的判题历史记录及相关图片"""
    if "/" in task_id or "\\" in task_id or ".." in task_id:
        logger.warning(f"[History] 非法任务ID删除请求: task_id={task_id}")
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

    logger.info(f"[History] 成功删除历史记录: task_id={task_id}, 清理关联文件数={deleted_count}")
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
    print("=" * 60)

    # 仅在交互式控制台输出 ASCII 二维码，避免重定向到日志文件时产生大面积乱码
    if sys.stdout.isatty():
        print(" 📱 用手机微信/浏览器直接扫描下方二维码打开相机拍照批改:")
        print("-" * 60)
        try:
            qr = qrcode.QRCode(box_size=1, border=1)
            qr.add_data(lan_url)
            qr.print_ascii(invert=True)
        except Exception:
            pass
        print("-" * 60 + "\n")
    else:
        print("\n")


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
        "stdout": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
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
        "math-grader": {"handlers": ["stdout"], "level": "INFO", "propagate": False},
    },
}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print_server_banner("0.0.0.0", port)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False, log_config=UVICORN_LOG_CONFIG)
