#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable


_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "_shared" / "scripts"
sys.path.insert(0, str(_SHARED_SCRIPTS))

from mailgateway_mcp_client import account_from_env, call_tool_sync, config_from_env  # noqa: E402


def _csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_bodies(
    args: argparse.Namespace,
    *,
    stdin_text: str | None,
    stdin_is_tty: bool,
) -> tuple[str | None, str | None]:
    text_body = args.text_body
    html_body = args.html_body
    text_stdin = args.text_stdin
    html_stdin = args.html_stdin

    if text_stdin and html_stdin:
        raise ValueError("cannot use both --text-stdin and --html-stdin")

    if text_stdin or html_stdin:
        if stdin_is_tty:
            raise ValueError("stdin body flag was provided but stdin is not available")
        if text_body is not None or html_body is not None:
            raise ValueError("cannot combine stdin body input with --text-body or --html-body")

        body_from_stdin = stdin_text if stdin_text is not None else ""
        if not body_from_stdin:
            raise ValueError("stdin body input was empty")

        if html_stdin:
            return None, body_from_stdin
        return body_from_stdin, None

    if not stdin_is_tty:
        raise ValueError("when using stdin body input, pass exactly one of --text-stdin or --html-stdin")

    if text_body is None and html_body is None:
        raise ValueError("at least one of --text-body or --html-body is required when stdin is not provided")

    return text_body, html_body


def build_arguments(args: argparse.Namespace) -> dict[str, object]:
    return build_arguments_with_bodies(
        args,
        account="primary",
        text_body=args.text_body,
        html_body=args.html_body,
    )


def build_arguments_with_bodies(
    args: argparse.Namespace,
    *,
    account: str,
    text_body: str | None,
    html_body: str | None,
) -> dict[str, object]:
    arguments: dict[str, object] = {
        "account": account,
        "to": _csv_list(args.to),
        "subject": args.subject,
    }

    if args.cc:
        arguments["cc"] = _csv_list(args.cc)
    if args.bcc:
        arguments["bcc"] = _csv_list(args.bcc)
    if text_body is not None:
        arguments["text_body"] = text_body
    if html_body is not None:
        arguments["html_body"] = html_body

    return arguments


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Submit an interactive MailGateway send_email request.")
    parser.add_argument("--to", required=True, help="Comma-separated recipient list.")
    parser.add_argument("--subject", required=True, help="Email subject.")
    parser.add_argument("--text-body", help="Plain-text body.")
    parser.add_argument("--html-body", help="HTML body.")
    parser.add_argument(
        "--text-stdin",
        action="store_true",
        help="Read the plain-text body from stdin.",
    )
    parser.add_argument(
        "--html-stdin",
        action="store_true",
        help="Read the HTML body from stdin.",
    )
    parser.add_argument("--cc", help="Optional comma-separated CC recipient list.")
    parser.add_argument("--bcc", help="Optional comma-separated BCC recipient list.")
    return parser


def run(
    args: argparse.Namespace,
    *,
    stdin_reader: Callable[[], str],
    stdin_is_tty: bool,
) -> dict[str, object]:
    stdin_text = stdin_reader() if not stdin_is_tty else None
    text_body, html_body = resolve_bodies(
        args,
        stdin_text=stdin_text,
        stdin_is_tty=stdin_is_tty,
    )

    config = config_from_env()
    account = account_from_env()
    result = call_tool_sync(
        config,
        "send_email",
        build_arguments_with_bodies(
            args,
            account=account,
            text_body=text_body,
            html_body=html_body,
        ),
    )
    result.setdefault("account", account)
    return result


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = run(
            args,
            stdin_reader=sys.stdin.read,
            stdin_is_tty=sys.stdin.isatty(),
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
