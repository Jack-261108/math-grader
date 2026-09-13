#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PORT=${PORT:-8000}

if [ -f "/root/.pyenv/versions/math-grader/bin/python" ]; then
    exec /root/.pyenv/versions/math-grader/bin/python server.py
else
    exec python server.py
fi
