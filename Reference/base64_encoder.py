#!/usr/bin/env python3
"""Encode inline text or file content to Base64."""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path


def encode_text(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def encode_file(path: str) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("ascii")


def write_output(output: str, output_file: str | None) -> None:
    if output_file:
        Path(output_file).write_text(output, encoding="ascii")
        return
    print(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert inline text or file content to Base64."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Inline text to encode as UTF-8.")
    source.add_argument(
        "--input-file",
        help="Path to a file whose raw bytes will be encoded as Base64.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional file path to save the Base64 result. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    try:
        if args.text is not None:
            encoded = encode_text(args.text)
        else:
            encoded = encode_file(args.input_file)
        write_output(encoded, args.output_file)
        return 0
    except Exception as exc:  # pragma: no cover - simple CLI tool
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
