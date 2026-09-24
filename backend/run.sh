#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# .venv 的解释器可能来自别的机器（软链失效），跑不通时重建，避免直接报 “No such file or directory”
if [ ! -x .venv/bin/python ] || ! .venv/bin/python --version >/dev/null 2>&1; then
  rm -rf .venv
  python3 -m venv .venv
fi
# 通过 python -m pip 调用：uv 等工具创建的 venv 可能没有独立的 pip 可执行文件
if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
  .venv/bin/python -m ensurepip --upgrade
fi
.venv/bin/python -m pip install -q -r requirements.txt
# 先校验运行配置：环境变量非法时直接说明原因并退出，不启动 uvicorn
.venv/bin/python -m app.run_config check >&2
# host/port 取 APP_HOST / APP_PORT，未配置时仍是 127.0.0.1:8000
read -r HOST PORT < <(.venv/bin/python -m app.run_config listen)
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT"
