#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  rm -rf .venv
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
# 端口、运行环境等取值来自环境变量 / .env（见 app/config.py 与 .env.example）
exec .venv/bin/python -m app
