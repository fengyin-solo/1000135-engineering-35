"""启动脚本辅助入口：校验运行配置并向 shell 输出生效的 host / port。

用法：
    python -m app.run_config check     校验配置，非法时打印原因并以退出码 1 结束
    python -m app.run_config listen    输出 "host port"，供 run.sh / 容器 CMD 使用
"""
from __future__ import annotations

import sys

try:
    # config 在导入期就会读取并校验环境变量，非法时抛 ConfigError；
    # 这里必须在导入动作外拦住它，给启动脚本一个干净的失败原因而不是一整段堆栈
    from app.config import settings
except Exception as exc:  # noqa: BLE001 - 该导入路径上只有 ConfigError 会抛出
    print(f"启动失败：运行配置校验未通过：{exc}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    if command == "check":
        print(f"配置校验通过：{settings.startup_line()}")
        return 0
    if command == "listen":
        print(f"{settings.host} {settings.port}")
        return 0
    print(f"未知命令：{command}（支持 check、listen）", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
