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

    assert module.build_arguments(Args()) == {
        "to": ["a@example.com", "b@example.com"],
        "subject": "Hello",
        "text_body": "Body",
        "cc": ["cc@example.com"],
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
    ) == {
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
        module.build_payload(template, {"title": "Disk Full", "summary": "bad"})


def test_shared_parse_json_argument_requires_object() -> None:
    module = _load_module(SHARED_PATH, "shared_skill_client")

    with pytest.raises(ValueError, match="decode to an object"):
        module.parse_json_argument('["not-an-object"]')
