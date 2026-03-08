from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path("/home/omry/dev/agent-tools")
INTERACTIVE_PATH = (
    REPO_ROOT
    / "mailgateway_mcp/openclaw_skills/send-email-interactive/scripts/send_email_interactive.py"
)
PREDEFINED_PATH = (
    REPO_ROOT
    / "mailgateway_mcp/openclaw_skills/send-email-predefined/scripts/send_email_predefined.py"
)
SHARED_PATH = (
    REPO_ROOT
    / "mailgateway_mcp/openclaw_skills/_shared/scripts/mailgateway_mcp_client.py"
)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_interactive_build_arguments_normalizes_optional_lists() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script")

    class Args:
        to = "a@example.com, b@example.com"
        subject = "Hello"
        text_body = "Body"
        html_body = None
        cc = "cc@example.com"
        bcc = None

    assert module.build_arguments_with_bodies(
        Args(),
        account="primary",
        text_body="Body",
        html_body=None,
    ) == {
        "account": "primary",
        "to": ["a@example.com", "b@example.com"],
        "subject": "Hello",
        "text_body": "Body",
        "cc": ["cc@example.com"],
    }


def test_interactive_resolve_bodies_uses_stdin_for_text_body() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_stdin_text")

    class Args:
        text_body = None
        html_body = None
        text_stdin = True
        html_stdin = False

    text_body, html_body = module.resolve_bodies(
        Args(),
        stdin_text="Hello\n\nWorld",
        stdin_is_tty=False,
    )

    assert text_body == "Hello\n\nWorld"
    assert html_body is None


def test_interactive_resolve_bodies_uses_stdin_for_html_body() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_stdin_html")

    class Args:
        text_body = None
        html_body = None
        text_stdin = False
        html_stdin = True

    text_body, html_body = module.resolve_bodies(
        Args(),
        stdin_text="<p>Hello</p>",
        stdin_is_tty=False,
    )

    assert text_body is None
    assert html_body == "<p>Hello</p>"


def test_interactive_resolve_bodies_rejects_combining_stdin_with_body_args() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_conflict")

    class Args:
        text_body = "Body"
        html_body = None
        text_stdin = True
        html_stdin = False

    with pytest.raises(ValueError, match="cannot combine stdin body input"):
        module.resolve_bodies(
            Args(),
            stdin_text="Hello",
            stdin_is_tty=False,
        )


def test_interactive_resolve_bodies_requires_explicit_stdin_flag_when_stdin_is_used() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_missing_stdin_flag")

    class Args:
        text_body = None
        html_body = None
        text_stdin = False
        html_stdin = False

    with pytest.raises(ValueError, match="pass exactly one of --text-stdin or --html-stdin"):
        module.resolve_bodies(
            Args(),
            stdin_text="Hello",
            stdin_is_tty=False,
        )


def test_interactive_resolve_bodies_rejects_both_stdin_flags() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_both_stdin_flags")

    class Args:
        text_body = None
        html_body = None
        text_stdin = True
        html_stdin = True

    with pytest.raises(ValueError, match="cannot use both --text-stdin and --html-stdin"):
        module.resolve_bodies(
            Args(),
            stdin_text="Hello",
            stdin_is_tty=False,
        )


def test_interactive_resolve_bodies_requires_body_when_no_stdin_or_args() -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_missing_body")

    class Args:
        text_body = None
        html_body = None
        text_stdin = False
        html_stdin = False

    with pytest.raises(ValueError, match="at least one of --text-body or --html-body is required"):
        module.resolve_bodies(
            Args(),
            stdin_text=None,
            stdin_is_tty=True,
        )


def test_interactive_run_passes_configured_account(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module(INTERACTIVE_PATH, "interactive_skill_script_run_account")

    class Args:
        to = "a@example.com"
        subject = "Hello"
        text_body = "Body"
        html_body = None
        text_stdin = False
        html_stdin = False
        cc = None
        bcc = None

    captured: dict[str, object] = {}

    monkeypatch.setattr(module, "config_from_env", lambda: object())
    monkeypatch.setattr(module, "account_from_env", lambda: "primary")

    def fake_call_tool_sync(config, tool_name, arguments):
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        return {"ok": True}

    monkeypatch.setattr(module, "call_tool_sync", fake_call_tool_sync)

    result = module.run(
        Args(),
        stdin_reader=lambda: "",
        stdin_is_tty=True,
    )

    assert captured == {
        "tool_name": "send_email",
        "arguments": {
            "account": "primary",
            "to": ["a@example.com"],
            "subject": "Hello",
            "text_body": "Body",
        },
    }
    assert result == {
        "ok": True,
        "account": "primary",
    }


def test_predefined_build_payload_renders_template_values() -> None:
    module = _load_module(PREDEFINED_PATH, "predefined_skill_script")

    template = {
        "subject": "Alert: {title}",
        "text_body": "Severity: {severity}",
        "to": ["ops+{severity}@example.com"],
        "cc": ["audit@example.com"],
    }

    assert module.build_payload(
        template,
        {"title": "Disk Full", "severity": "critical"},
        account="primary",
    ) == {
        "account": "primary",
        "to": ["ops+critical@example.com"],
        "cc": ["audit@example.com"],
        "subject": "Alert: Disk Full",
        "text_body": "Severity: critical",
    }


def test_predefined_build_payload_rejects_unexpected_params() -> None:
    module = _load_module(PREDEFINED_PATH, "predefined_skill_script_unexpected")

    template = {
        "subject": "Alert: {title}",
        "text_body": "{summary}",
        "to": ["ops@example.com"],
        "allowed_params": ["title"],
    }

    with pytest.raises(ValueError, match="unexpected template parameters"):
        module.build_payload(
            template,
            {"title": "Disk Full", "summary": "bad"},
            account="primary",
        )


def test_shared_account_from_env_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module(SHARED_PATH, "shared_skill_client_account")
    monkeypatch.delenv("MAILGATEWAY_ACCOUNT", raising=False)

    with pytest.raises(ValueError, match="MAILGATEWAY_ACCOUNT is required"):
        module.account_from_env()


def test_shared_account_from_env_reads_value(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module(SHARED_PATH, "shared_skill_client_account_ok")
    monkeypatch.setenv("MAILGATEWAY_ACCOUNT", "primary")

    assert module.account_from_env() == "primary"


def test_shared_parse_json_argument_requires_object() -> None:
    module = _load_module(SHARED_PATH, "shared_skill_client")

    with pytest.raises(ValueError, match="decode to an object"):
        module.parse_json_argument('["not-an-object"]')
