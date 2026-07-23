from __future__ import annotations

import hashlib
from collections.abc import Iterable


def compute_script_hash(text: str) -> str:
    """脚本文本的 sha256（用于计划核对与审计，不泄露内容）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_script(text: str, *, max_chars: int = 200) -> str:
    """生成不含完整内容的简短摘要：行数 + 首段截断。"""
    lines = text.splitlines()
    head = " ".join(text.split())
    if len(head) > max_chars:
        head = head[:max_chars] + "…"
    return f"{len(lines)} line(s); {head}" if head else f"{len(lines)} line(s); (empty)"


def scan_risk_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    """扫描命中的危险关键词（大小写不敏感）。"""
    lowered = text.lower()
    return [kw for kw in keywords if kw.lower() in lowered]


def truncate(text: str | None, max_len: int) -> str | None:
    """截断过长文本（用于日志 outMsg/errMsg）。"""
    if text is None:
        return None
    if max_len > 0 and len(text) > max_len:
        return text[:max_len] + f"…[truncated {len(text) - max_len} chars]"
    return text
