from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import os
from urllib.parse import urlsplit, urlunsplit


@dataclass(slots=True)
class AppSettings:
    repo_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    topo_base_url: str = field(default_factory=lambda: os.getenv("TOPO_BASE_URL", "http://172.23.215.103/api/topo"))
    login_url: str = field(default_factory=str)
    state_dir: Path = field(default_factory=lambda: Path(os.getenv("TOPO_STATE_DIR", "")) if os.getenv("TOPO_STATE_DIR") else Path())
    db_path: Path = field(default_factory=Path)
    keyring_service: str = field(default_factory=lambda: os.getenv("TOPO_KEYRING_SERVICE", "topo_api_suite"))
    keyring_username: str = field(default_factory=lambda: os.getenv("TOPO_KEYRING_USERNAME", "session_cookie"))
    confirmation_phrase: str = field(default_factory=lambda: os.getenv("TOPO_CONFIRMATION_PHRASE", "I_ACCEPT_THE_RISK"))
    session_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TOPO_SESSION_TIMEOUT", "180")))
    execution_poll_interval_seconds: float = field(default_factory=lambda: float(os.getenv("TOPO_POLL_INTERVAL", "2")))
    execution_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TOPO_EXECUTION_TIMEOUT", "1800")))
    deployment_poll_interval_seconds: float = field(default_factory=lambda: float(os.getenv("TOPO_DEPLOYMENT_POLL_INTERVAL", "5")))
    deployment_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TOPO_DEPLOYMENT_TIMEOUT", "900")))
    api_page_size: int = field(default_factory=lambda: int(os.getenv("TOPO_API_PAGE_SIZE", "200")))
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:5173", "http://localhost:5173")
    risk_keywords: tuple[str, ...] = (
        "rm -rf",
        "mkfs",
        "shutdown",
        "reboot",
        "poweroff",
        "del /f",
        "format ",
        "diskpart",
        "reg delete",
        "sc delete",
        "iptables -f",
        "route delete",
        "net user ",
        "userdel ",
        "dd if=",
    )

    def __post_init__(self) -> None:
        if not self.login_url:
            self.login_url = self.derive_login_url(self.topo_base_url)
        if self.state_dir == Path():
            self.state_dir = self.repo_root / ".local_state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if self.db_path == Path():
            self.db_path = self.state_dir / "topo_automation.sqlite3"

    @staticmethod
    def derive_login_url(topo_base_url: str) -> str:
        parsed = urlsplit(topo_base_url)
        if parsed.scheme and parsed.netloc:
            return urlunsplit((parsed.scheme, parsed.netloc, "/bdesigner/", "", ""))

        normalized = topo_base_url.rstrip("/")
        if normalized.endswith("/api/topo"):
            normalized = normalized[: -len("/api/topo")]
        if normalized.endswith("/bdesigner"):
            return normalized + "/"
        return normalized + "/bdesigner/"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
