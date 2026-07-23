from __future__ import annotations

from typing import Any, Callable

from topo_mcp.settings import Settings


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = dict(
        base_url="http://test/api/topo",
        cookie="",
        allow_execute=True,
        project_allowlist="",
        max_devices_per_exec=20,
        max_script_bytes=65536,
        api_page_size=200,
        max_items=500,
        http_timeout=5.0,
        get_retries=0,
        log_msg_maxlen=100,
    )
    base.update(overrides)
    # _env_file=None 禁止读取真实 .env，保证测试隔离
    return Settings(_env_file=None, **base)


class FakeTransport:
    """替身 transport：直接返回「已解信封」的 data，并记录所有调用。"""

    def __init__(self, handler: Callable[[str, str, dict, Any], Any]) -> None:
        self._handler = handler
        self.calls: list[dict[str, Any]] = []

    async def request(self, method: str, path: str, *, params: dict | None = None, json_obj: Any = None) -> Any:
        self.calls.append(
            {"method": method.upper(), "path": path, "params": dict(params or {}), "json": json_obj}
        )
        return self._handler(method.upper(), path, dict(params or {}), json_obj)

    async def aclose(self) -> None:
        pass

    def calls_to(self, method: str, path: str) -> list[dict[str, Any]]:
        return [c for c in self.calls if c["method"] == method.upper() and c["path"] == path]


def paginate(items: list[dict], params: dict) -> dict:
    page = int(params.get("pageIndex", 1))
    size = int(params.get("pageSize", len(items) or 1))
    start = (page - 1) * size
    return {"items": items[start : start + size], "total": len(items)}
