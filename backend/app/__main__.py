"""`python -m app`：按生效配置启动服务。

本地（run.sh）与容器（Dockerfile）共用这一个入口，监听地址与端口只从
Settings 取，保证启动日志里的生效值和实际监听值一致。
"""
from __future__ import annotations

import uvicorn

from app.config import settings


def main() -> None:
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
