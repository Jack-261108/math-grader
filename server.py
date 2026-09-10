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
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "uploads"), exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

app.mount("/output", StaticFiles(directory=output_dir), name="output")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
    model: Optional[str] = Form(None)
):
    """接收手机拍照图片并执行自动批改"""
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
            model=model
        )

        # 整理错题清单
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
                    "expression": f"{it.get('a')} {op_sym} {it.get('b')}"
                })

        return {
            "status": "success",
            "task_id": task_id,
            "title": result_data["title"],
            "summary": result_data["summary"],
            "wrong_items": wrong_items,
            "scan_url": f"/output/{task_id}_annotated_scan.jpg",
            "orig_url": f"/output/{task_id}_annotated_original.jpg",
            "report_url": f"/output/{task_id}_report.json",
            "items_count": len(result_data.get("items", []))
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批改处理失败: {str(e)}")


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
    local_url = f"http://127.0.0.1:{port}"
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
