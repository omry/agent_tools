#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "_shared" / "scripts"
sys.path.insert(0, str(_SHARED_SCRIPTS))

from mailgateway_mcp_client import call_tool_sync, config_from_env  # noqa: E402


def _csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_arguments(args: argparse.Namespace) -> dict[str, object]:
    arguments: dict[str, object] = {
        "to": _csv_list(args.to),
        "subject": args.subject,
    }

    if args.cc:
        arguments["cc"] = _csv_list(args.cc)
    if args.bcc:
        arguments["bcc"] = _csv_list(args.bcc)
    if args.text_body is not None:
        arguments["text_body"] = args.text_body
    if args.html_body is not None:
        arguments["html_body"] = args.html_body

    return arguments


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Submit an interactive MailGateway send_email request.")
    parser.add_argument("--to", required=True, help="Comma-separated recipient list.")
    parser.add_argument("--subject", required=True, help="Email subject.")
    parser.add_argument("--text-body", help="Plain-text body.")
    parser.add_argument("--html-body", help="HTML body.")
    parser.add_argument("--cc", help="Optional comma-separated CC recipient list.")
    parser.add_argument("--bcc", help="Optional comma-separated BCC recipient list.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.text_body and not args.html_body:
        parser.error("at least one of --text-body or --html-body is required")

    config = config_from_env()
    result = call_tool_sync(config, "send_email", build_arguments(args))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
