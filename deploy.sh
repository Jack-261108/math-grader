#!/usr/bin/env bash
set -euo pipefail

echo '=========================================='
echo '🚀 开始在 server1 部署 math-grader...'
echo '=========================================='

APP_DIR="${APP_DIR:-/root/math-grader}"
cd "$APP_DIR"

echo '📥 拉取最新代码...'
git fetch origin main
git reset --hard origin/main

echo '🔤 检查系统中文字体环境...'
if ! fc-list :lang=zh 2>/dev/null | grep -q .; then
    echo '📦 安装中文字体支持包 (fonts-wqy-microhei)...'
    apt-get update -qq && apt-get install -y -qq fonts-wqy-microhei fonts-wqy-zenhei || true
fi

echo '🐍 检查 Python 虚拟环境与依赖...'
export PATH="/root/.pyenv/bin:$PATH"
if [ -d "/root/.pyenv/versions/math-grader" ]; then
    PIP_BIN="/root/.pyenv/versions/math-grader/bin/pip"
else
    PIP_BIN="pip"
fi

echo "📦 使用 ${PIP_BIN} 同步依赖..."
"$PIP_BIN" install -r requirements.txt

echo '⚡ 检查并编译前端工程 (Vue 3 + Pinia + Vite)...'
if [ -d "frontend" ] && command -v npm >/dev/null 2>&1; then
    cd frontend
    npm install
    npm run build
    cd "$APP_DIR"
fi

echo '🔄 重启 Supervisor 服务...'
supervisorctl restart math-grader

echo '⏳ 等待服务启动并执行健康检查...'
sleep 3
supervisorctl status math-grader

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --noproxy '*' http://127.0.0.1:8000/ || true)
if [ "$HTTP_CODE" = '200' ]; then
    echo '=========================================='
    echo "✅ 部署成功！服务运行正常 (HTTP $HTTP_CODE)"
    echo '=========================================='
else
    echo "❌ 健康检查失败，HTTP 返回码: $HTTP_CODE"
    supervisorctl tail math-grader stderr
    exit 1
fi
