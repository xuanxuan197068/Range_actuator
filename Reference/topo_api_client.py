#!/usr/bin/env python3
"""Small HTTP client for the topo API.

Examples:
  python topo_api_client.py get --base-url http://172.23.215.103/topo --path /projects --param pageIndex=1 --param pageSize=10
  python topo_api_client.py get --url http://172.23.215.103/topo/device_scripts/devices/deployed?projectId=xxx --cookie-file cookie.txt
  python topo_api_client.py post --base-url http://172.23.215.103/topo --path /device_scripts/run/private --cookie-file cookie.txt --json '{"deviceIds":["id-1"]}'
  python topo_api_client.py delete --base-url http://172.23.215.103/topo --path /device_scripts/script-id --cookie-file cookie.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional
from urllib import error, parse, request


def parse_key_value(raw: str, separator: str = "=") -> tuple[str, str]:
    if separator not in raw:
        raise ValueError(f"Expected '{separator}' in: {raw}")
    key, value = raw.split(separator, 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise ValueError(f"Empty key in: {raw}")
    return key, value


def parse_header(raw: str) -> tuple[str, str]:
    return parse_key_value(raw, separator=":")


def load_cookie_text(cookie: Optional[str], cookie_file: Optional[str]) -> Optional[str]:
    if cookie:
        return cookie.strip()
    if cookie_file:
        text = Path(cookie_file).read_text(encoding="utf-8").strip()
        return text or None
    return None


def join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{base}{suffix}"


def add_query_params(url: str, params: Iterable[str]) -> str:
    if not params:
        return url
    parsed = parse.urlsplit(url)
    current = parse.parse_qsl(parsed.query, keep_blank_values=True)
    for raw in params:
        current.append(parse_key_value(raw))
    query = parse.urlencode(current, doseq=True)
    return parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def build_headers(header_args: Iterable[str], cookie: Optional[str], body: Optional[bytes], content_type: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "User-Agent": "topo-api-client/1.0",
        "Accept": "application/json, text/plain, */*",
    }
    for raw in header_args:
        key, value = parse_header(raw)
        headers[key] = value
    if cookie:
        headers["Cookie"] = cookie
    if body is not None and content_type:
        headers["Content-Type"] = content_type
    return headers


def build_request_body(
    method: str,
    *,
    json_text: Optional[str] = None,
    json_file: Optional[str] = None,
    raw_body: Optional[str] = None,
    content_type: Optional[str] = None,
) -> tuple[Optional[bytes], Optional[str]]:
    if method == "get":
        return None, None

    if json_text and json_file:
        raise ValueError("Use either --json or --json-file, not both.")
    if raw_body and (json_text or json_file):
        raise ValueError("Use either raw body or JSON body, not both.")

    if json_file:
        data = Path(json_file).read_text(encoding="utf-8")
        obj = json.loads(data)
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        return payload, "application/json; charset=utf-8"
    if json_text:
        obj = json.loads(json_text)
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        return payload, "application/json; charset=utf-8"
    if raw_body is not None:
        return raw_body.encode("utf-8"), content_type or "text/plain; charset=utf-8"
    return None, None


def build_body(args: argparse.Namespace) -> tuple[Optional[bytes], Optional[str]]:
    return build_request_body(
        args.method,
        json_text=args.json_text,
        json_file=args.json_file,
        raw_body=args.raw_body,
        content_type=args.content_type,
    )


def pretty_print_response(status: int, headers, body_text: str, show_headers: bool) -> None:
    print(f"HTTP {status}")
    if show_headers:
        print("--- headers ---")
        for key, value in headers.items():
            print(f"{key}: {value}")
    print("--- body ---")
    body = body_text.strip()
    if not body:
        print("(empty)")
        return
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return
    print(json.dumps(parsed, ensure_ascii=False, indent=2))


def mask_header_value(key: str, value: str) -> str:
    lower = key.lower()
    if lower in {"cookie", "authorization"}:
        if len(value) <= 12:
            return "*" * len(value)
        return value[:6] + "..." + value[-6:]
    return value


@dataclass
class ClientResponse:
    method: str
    url: str
    status: int
    headers: dict[str, str]
    body_text: str


def send_request(
    method: str,
    *,
    base_url: str = "http://172.23.215.103/api/topo",
    path: str = "/",
    url: Optional[str] = None,
    params: Optional[Iterable[str]] = None,
    header_args: Optional[Iterable[str]] = None,
    cookie: Optional[str] = None,
    cookie_file: Optional[str] = None,
    json_text: Optional[str] = None,
    json_file: Optional[str] = None,
    raw_body: Optional[str] = None,
    content_type: Optional[str] = None,
    timeout: int = 15,
    output: Optional[str] = None,
) -> ClientResponse:
    normalized_method = method.lower()
    body, default_content_type = build_request_body(
        normalized_method,
        json_text=json_text,
        json_file=json_file,
        raw_body=raw_body,
        content_type=content_type,
    )
    cookie_text = load_cookie_text(cookie, cookie_file)
    target_url = url if url else join_url(base_url, path)
    target_url = add_query_params(target_url, params or [])
    headers = build_headers(header_args or [], cookie_text, body, default_content_type)
    req = request.Request(url=target_url, data=body, method=normalized_method.upper(), headers=headers)

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
            resp_headers = dict(resp.headers.items())
    except error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        resp_headers = dict(exc.headers.items())

    body_text = raw.decode("utf-8", errors="replace")
    if output:
        Path(output).write_text(body_text, encoding="utf-8")
    return ClientResponse(
        method=normalized_method.upper(),
        url=target_url,
        status=status,
        headers=resp_headers,
        body_text=body_text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Call topo API endpoints with GET, POST, or DELETE.")
    parser.add_argument("method", choices=["get", "post", "delete"], help="HTTP method")
    parser.add_argument("--base-url", default="http://172.23.215.103/api/topo", help="Base URL, e.g. http://172.23.215.103/api/topo")
    parser.add_argument("--path", default="/", help="API path, e.g. /projects")
    parser.add_argument("--url", help="Full request URL. Overrides --base-url and --path.")
    parser.add_argument("--param", action="append", default=[], help="Query parameter in key=value form. Can be repeated.")
    parser.add_argument("--header", action="append", default=[], help="HTTP header in 'Name: Value' form. Can be repeated.")
    parser.add_argument("--cookie", help="Raw Cookie header value.")
    parser.add_argument("--cookie-file", help="Path to a file containing the raw Cookie header value.")
    parser.add_argument("--json", dest="json_text", help="Inline JSON request body for non-GET requests.")
    parser.add_argument("--json-file", help="Path to a JSON file used as non-GET request body.")
    parser.add_argument("--raw-body", help="Raw request body for non-GET requests.")
    parser.add_argument("--content-type", help="Content-Type for --raw-body.")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout in seconds.")
    parser.add_argument("--show-headers", action="store_true", help="Print response headers.")
    parser.add_argument("--output", help="Optional file path to save the response body.")
    parser.add_argument("--dry-run", action="store_true", help="Print the final request without sending it.")
    args = parser.parse_args()

    try:
        body, default_content_type = build_body(args)
        cookie_text = load_cookie_text(args.cookie, args.cookie_file)
        url = args.url if args.url else join_url(args.base_url, args.path)
        url = add_query_params(url, args.param)
        headers = build_headers(args.header, cookie_text, body, default_content_type)

        if args.dry_run:
            print(f"METHOD {args.method.upper()}")
            print(f"URL {url}")
            print("--- headers ---")
            for key, value in headers.items():
                print(f"{key}: {mask_header_value(key, value)}")
            print("--- body ---")
            if body is None:
                print("(empty)")
            else:
                body_text = body.decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(body_text)
                    print(json.dumps(parsed, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print(body_text)
            return 0

        response = send_request(
            args.method,
            base_url=args.base_url,
            path=args.path,
            url=args.url,
            params=args.param,
            header_args=args.header,
            cookie=args.cookie,
            cookie_file=args.cookie_file,
            json_text=args.json_text,
            json_file=args.json_file,
            raw_body=args.raw_body,
            content_type=args.content_type,
            timeout=args.timeout,
            output=args.output,
        )
        pretty_print_response(response.status, response.headers, response.body_text, args.show_headers)
        return 0
    except Exception as exc:  # pragma: no cover - simple CLI tool
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
