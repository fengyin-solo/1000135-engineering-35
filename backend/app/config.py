"""运行配置：端口、跨域、运行环境、分页条数。

配置来源只有一处：环境变量（本地开发可写在 backend/.env 里，容器用 -e 或
compose 的 environment 传入），没设置的项回落到本文件里的默认值。取值不合法时
启动直接失败并说明原因，避免带着错误配置跑起来。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv 未装时也能跑，只是不读 .env 文件
    load_dotenv = None

# backend/.env：本地开发的配置文件，环境变量优先级更高
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if load_dotenv is not None and _ENV_FILE.is_file():
    load_dotenv(_ENV_FILE)


class ConfigError(Exception):
    """配置校验失败：消息里写明是哪一项、取到了什么值、期望什么。"""


@dataclass(frozen=True)
class Settings:
    app_name: str = "冷链物流温控运营平台"
    env: str = "local"
    host: str = "127.0.0.1"
    port: int = 8000
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )
    page_size_default: int = 20
    page_size_max: int = 200


def _read_int(name: str, default: int, errors: list[str]) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        errors.append(f"配置项 {name} 取值 {raw!r} 无效：需要整数")
        return default


def load_settings() -> Settings:
    """从环境变量构建 Settings 并校验必填项；任一取值无效就抛出 ConfigError。"""
    defaults = Settings()
    errors: list[str] = []

    app_name = (os.environ.get("APP_NAME") or "").strip() or defaults.app_name
    env = (os.environ.get("APP_ENV") or "").strip()
    if not env:
        env = defaults.env
    host = (os.environ.get("HOST") or "").strip()
    if not host:
        host = defaults.host

    port = _read_int("PORT", defaults.port, errors)
    if not 1 <= port <= 65535:
        errors.append(f"配置项 PORT 取值 {port} 无效：端口需要在 1-65535 之间")

    page_size_default = _read_int("PAGE_SIZE_DEFAULT", defaults.page_size_default, errors)
    if page_size_default < 1:
        errors.append(f"配置项 PAGE_SIZE_DEFAULT 取值 {page_size_default} 无效：至少为 1")
    page_size_max = _read_int("PAGE_SIZE_MAX", defaults.page_size_max, errors)
    if page_size_max < page_size_default:
        errors.append(
            f"配置项 PAGE_SIZE_MAX 取值 {page_size_max} 无效：不能小于 PAGE_SIZE_DEFAULT（{page_size_default}）"
        )

    raw_origins = os.environ.get("ALLOWED_ORIGINS")
    if raw_origins is None or not raw_origins.strip():
        allowed_origins = list(defaults.allowed_origins)
    else:
        allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        if not allowed_origins:
            errors.append("配置项 ALLOWED_ORIGINS 无效：逗号分隔后没有可用来源")

    if errors:
        raise ConfigError("运行配置校验失败：\n" + "\n".join(f"- {error}" for error in errors))

    return Settings(
        app_name=app_name,
        env=env,
        host=host,
        port=port,
        allowed_origins=allowed_origins,
        page_size_default=page_size_default,
        page_size_max=page_size_max,
    )


settings = load_settings()
