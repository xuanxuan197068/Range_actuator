from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 危险命令关键词（沿用旧项目清单）；prepare 阶段命中只告警，不阻断。
RISK_KEYWORDS: tuple[str, ...] = (
    "xuan",
)


class Settings(BaseSettings):
    """全部配置走环境变量，前缀 TOPO_（第一版通过 env 注入 Cookie）。"""

    model_config = SettingsConfigDict(
        env_prefix="TOPO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "http://172.23.215.103/api/topo"
    cookie: str = ""

    allow_execute: bool = True
    project_allowlist: str = ""

    max_devices_per_exec: int = 20
    max_script_bytes: int = 65536

    api_page_size: int = 200
    max_items: int = 500

    http_timeout: float = 30.0
    get_retries: int = 2

    log_msg_maxlen: int = 4000

    @property
    def allowlist(self) -> set[str]:
        return {item.strip() for item in self.project_allowlist.split(",") if item.strip()}

    @property
    def risk_keywords(self) -> tuple[str, ...]:
        return RISK_KEYWORDS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
