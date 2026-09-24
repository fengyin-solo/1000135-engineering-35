"""运行配置：启动时从 .env 文件与环境变量读取，读取失败即中止启动并说明原因。

读取顺序：仓库根目录 / backend/ 下的 .env 文件 -> 进程环境变量（环境变量优先）。
所有变量都不设置时，沿用改造前写死在代码里的默认值（local / 8000 / 5173 跨域 / 20 / 200），
因此原来的启动命令行为不变。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# 改造前写死在代码里的默认值：环境变量缺省时继续沿用
DEFAULT_APP_NAME = "冷链物流温控运营平台"
DEFAULT_ENV = "local"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
DEFAULT_PAGE_SIZE_DEFAULT = 20
DEFAULT_PAGE_SIZE_MAX = 200

# 数值型配置的合法区间，超出区间直接判定为配置错误
PORT_RANGE = (1, 65535)
PAGE_SIZE_RANGE = (1, 10000)


class ConfigError(ValueError):
    """环境变量缺失或格式非法导致无法启动时抛出，消息里写明原因与对应的默认值。"""


def _load_env_files() -> list[str]:
    """加载仓库根目录与 backend/ 下的 .env；真实环境变量优先，不会被文件覆盖。"""
    backend_dir = Path(__file__).resolve().parent.parent
    loaded: list[str] = []
    for path in (backend_dir / ".env", backend_dir.parent / ".env"):
        if path.is_file():
            load_dotenv(path, override=False)
            loaded.append(str(path))
    return loaded


def _read_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        raise ConfigError(f"环境变量 {name} 不能为空；不设置它时默认值为 {default!r}")
    return value


def _read_int(name: str, default: int, bounds: tuple[int, int]) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        raise ConfigError(f"环境变量 {name} 不能为空；不设置它时默认值为 {default}")
    try:
        parsed = int(value)
    except ValueError:
        raise ConfigError(
            f"环境变量 {name}={value!r} 不是整数；不设置它时默认值为 {default}"
        ) from None
    low, high = bounds
    if not low <= parsed <= high:
        raise ConfigError(
            f"环境变量 {name}={parsed} 超出允许范围（{low}~{high}）；"
            f"不设置它时默认值为 {default}"
        )
    return parsed


def _read_origins(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return list(default)
    value = raw.strip()
    if not value:
        raise ConfigError(
            f"环境变量 {name} 不能为空；不设置它时默认值为 {'、'.join(default)}"
        )
    origins = [item.strip() for item in value.split(",") if item.strip()]
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ConfigError(
                f"环境变量 {name} 中的 {origin!r} 不是合法的跨域来源"
                f"（形如 http://localhost:5173，多个来源用英文逗号分隔）；"
                f"不设置它时默认值为 {'、'.join(default)}"
            )
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ConfigError(
                f"环境变量 {name} 中的 {origin!r} 只能写协议、主机与端口，"
                f"不要带路径或查询参数"
            )
    return origins


@dataclass(frozen=True)
class Settings:
    app_name: str = DEFAULT_APP_NAME
    env: str = DEFAULT_ENV
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    allowed_origins: list[str] = field(
        default_factory=lambda: list(DEFAULT_ALLOWED_ORIGINS)
    )
    page_size_default: int = DEFAULT_PAGE_SIZE_DEFAULT
    page_size_max: int = DEFAULT_PAGE_SIZE_MAX
    env_files: list[str] = field(default_factory=list)

    def startup_line(self) -> str:
        """启动日志里打印的一行生效配置，本地和容器里能直接看出差异。"""
        sources = "、".join(self.env_files) if self.env_files else "未提供 .env（仅环境变量/默认值）"
        return (
            f"{self.app_name} 启动：运行环境={self.env}，"
            f"监听 http://{self.host}:{self.port}，"
            f"允许跨域来源 {len(self.allowed_origins)} 个（{'、'.join(self.allowed_origins)}），"
            f"分页默认 {self.page_size_default} 条/上限 {self.page_size_max} 条，"
            f"配置来源={sources}"
        )


def load_settings() -> Settings:
    """读取并校验全部环境变量；任一配置非法时抛 ConfigError，由启动入口负责说明并退出。"""
    env_files = _load_env_files()
    page_size_default = _read_int(
        "PAGE_SIZE_DEFAULT", DEFAULT_PAGE_SIZE_DEFAULT, PAGE_SIZE_RANGE
    )
    page_size_max = _read_int(
        "PAGE_SIZE_MAX", DEFAULT_PAGE_SIZE_MAX, PAGE_SIZE_RANGE
    )
    if page_size_default > page_size_max:
        raise ConfigError(
            f"PAGE_SIZE_DEFAULT={page_size_default} 不能大于 PAGE_SIZE_MAX={page_size_max}；"
            "两者都不设置时默认值分别为 20 和 200"
        )
    return Settings(
        app_name=_read_str("APP_NAME", DEFAULT_APP_NAME),
        env=_read_str("APP_ENV", DEFAULT_ENV),
        host=_read_str("APP_HOST", DEFAULT_HOST),
        port=_read_int("APP_PORT", DEFAULT_PORT, PORT_RANGE),
        allowed_origins=_read_origins(
            "APP_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS
        ),
        page_size_default=page_size_default,
        page_size_max=page_size_max,
        env_files=env_files,
    )


# uvicorn / 测试导入本模块时立即完成读取与校验，配置非法会在启动阶段直接失败
settings = load_settings()
