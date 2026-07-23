from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from .settings import Settings

_RETRIABLE_STATUS = {500, 502, 503, 504}


class TopoApiError(RuntimeError):
    """靶场 API 返回异常。异常信息只含 path/status/服务端 message，绝不含 Cookie。"""

    def __init__(self, message: str, *, status: int | None = None, path: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.path = path


class AsyncTransport:
    """封装 httpx.AsyncClient：注入 Cookie、解 {code,message,data} 信封、仅 GET 重试。"""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # httpx 的 base_url 拼接遵循 RFC3986：请求路径以 "/" 开头会覆盖 base_url 的路径部分。
        # 因此 base_url 统一补尾部 "/"，请求时去掉相对 path 的前导 "/"，保证 /api/topo 前缀不丢。
        self._base_url = settings.base_url.rstrip("/") + "/"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "topo-mcp/0.1",
        }
        if settings.cookie:
            headers["Cookie"] = settings.cookie
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.http_timeout,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_obj: Any | None = None,
    ) -> Any:
        method_up = method.upper()
        rel_path = path.lstrip("/")
        query = {k: v for k, v in (params or {}).items() if v is not None}
        # 只有 GET 重试；写请求绝不自动重试，避免重复建脚本/重复下发。
        retries = self._settings.get_retries if method_up == "GET" else 0

        attempt = 0
        while True:
            try:
                resp = await self._client.request(method_up, rel_path, params=query, json=json_obj)
            except httpx.TransportError as exc:
                if attempt < retries:
                    attempt += 1
                    await asyncio.sleep(min(0.2 * 2**attempt, 2.0))
                    continue
                raise TopoApiError(
                    f"network error calling {path}: {exc.__class__.__name__}", path=path
                ) from exc

            if resp.status_code in _RETRIABLE_STATUS and attempt < retries:
                attempt += 1
                await asyncio.sleep(min(0.2 * 2**attempt, 2.0))
                continue

            return self._unwrap(resp, path)

    @staticmethod
    def _unwrap(resp: httpx.Response, path: str) -> Any:
        status = resp.status_code
        text = resp.text.strip()
        if not text:
            if status >= 400:
                raise TopoApiError(f"HTTP {status} calling {path}", status=status, path=path)
            return None
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            if status >= 400:
                raise TopoApiError(
                    f"HTTP {status} calling {path}: non-JSON body", status=status, path=path
                ) from exc
            return text
        if status >= 400:
            message = payload.get("message") if isinstance(payload, dict) else None
            raise TopoApiError(message or f"HTTP {status} calling {path}", status=status, path=path)
        if isinstance(payload, dict) and "code" in payload:
            if payload.get("code") != 1:
                raise TopoApiError(
                    payload.get("message") or f"unexpected response code from {path}",
                    status=status,
                    path=path,
                )
            return payload.get("data")
        return payload
