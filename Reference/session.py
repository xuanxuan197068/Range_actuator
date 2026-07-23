from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import time

import keyring
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

from backend.topo_automation.schemas import SessionStatus
from backend.topo_automation.settings import AppSettings
from backend.topo_automation.topo_adapter import TopoApiAdapter


class SessionManager:
    def __init__(self, settings: AppSettings, adapter: TopoApiAdapter) -> None:
        self._settings = settings
        self._adapter = adapter
        self._last_source: str | None = None
        self._last_validated_at: str | None = None

    def get_cookie(self) -> str | None:
        return keyring.get_password(self._settings.keyring_service, self._settings.keyring_username)

    def import_cookie(self, cookie: str, *, source: str = "manual") -> SessionStatus:
        normalized = cookie.strip()
        if not normalized:
            raise ValueError("Cookie is empty.")
        if not self._adapter.validate_cookie(normalized):
            raise ValueError("Cookie is invalid or expired.")
        keyring.set_password(self._settings.keyring_service, self._settings.keyring_username, normalized)
        self._last_source = source
        self._last_validated_at = self._utc_now()
        return self.status(detail="Session imported successfully.")

    def status(self, *, detail: str | None = None) -> SessionStatus:
        cookie = self.get_cookie()
        authenticated = bool(cookie and self._adapter.validate_cookie(cookie))
        if authenticated:
            self._last_validated_at = self._utc_now()
        return SessionStatus(
            authenticated=authenticated,
            source=self._last_source,
            topoBaseUrl=self._settings.topo_base_url,
            loginUrl=self._settings.login_url,
            validatedAt=self._last_validated_at,
            detail=detail,
        )

    def require_cookie(self) -> str:
        cookie = self.get_cookie()
        if not cookie:
            raise ValueError("No saved session cookie. Log in or import a cookie first.")
        if not self._adapter.validate_cookie(cookie):
            raise ValueError("Saved session cookie is expired. Log in again.")
        self._last_validated_at = self._utc_now()
        return cookie

    def login_with_browser(self, login_url: str | None = None) -> SessionStatus:
        target_url = login_url or self._settings.login_url
        options = EdgeOptions()
        binary_location = self._resolve_edge_binary()
        if binary_location:
            options.binary_location = binary_location
        driver = webdriver.Edge(options=options)
        driver.get(target_url)
        try:
            deadline = time.monotonic() + self._settings.session_timeout_seconds
            while time.monotonic() < deadline:
                cookies = driver.get_cookies()
                if cookies:
                    cookie_text = "; ".join(f"{item['name']}={item['value']}" for item in cookies if item.get("name"))
                    if cookie_text and self._adapter.validate_cookie(cookie_text):
                        keyring.set_password(self._settings.keyring_service, self._settings.keyring_username, cookie_text)
                        self._last_source = "browser"
                        self._last_validated_at = self._utc_now()
                        return self.status(detail="Browser login completed successfully.")
                if not driver.window_handles:
                    break
                time.sleep(1)
            raise TimeoutError("Browser login did not produce a valid session before timeout.")
        finally:
            driver.quit()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _resolve_edge_binary() -> str | None:
        candidates = (
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        )
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None
