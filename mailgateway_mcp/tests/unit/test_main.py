import sys
from types import ModuleType
from types import SimpleNamespace

import pytest
from omegaconf import OmegaConf

from mailgateway_mcp.config import AppConfig
from mailgateway_mcp.main import build_app, build_server


def test_build_app_accepts_hydra_config() -> None:
    cfg = OmegaConf.structured(AppConfig())

    app = build_app(cfg)

    assert app.tool_names() == ["list_accounts", "send_email"]


def test_build_app_list_accounts_uses_real_config_shape() -> None:
    cfg = OmegaConf.structured(AppConfig())

    app = build_app(cfg)

    assert app.list_accounts() == [
        {
            "name": "primary",
            "description": "Bot-owned account for automated email tasks.",
            "account_access_profile": "bot",
            "smtp_enabled": True,
            "imap_enabled": False,
        }
    ]


def test_build_server_registers_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    tools: dict[str, object] = {}
    list_accounts_calls = 0
    send_email_calls: list[dict[str, object]] = []

    class FakeApp:
        def list_accounts(self):
            nonlocal list_accounts_calls
            list_accounts_calls += 1
            return [
                {
                    "name": "primary",
                    "description": "Primary account",
                    "account_access_profile": "bot",
                    "smtp_enabled": True,
                    "imap_enabled": False,
                }
            ]

        def send_email(
            self,
            *,
            account: str,
            to: list[str],
            subject: str,
            text_body: str | None = None,
            html_body: str | None = None,
            cc: list[str] | None = None,
            bcc: list[str] | None = None,
        ):
            send_email_calls.append(
                {
                    "account": account,
                    "to": to,
                    "subject": subject,
                    "text_body": text_body,
                    "html_body": html_body,
                    "cc": cc,
                    "bcc": bcc,
                }
            )
            return SimpleNamespace(
                message_id="<message-id@example.com>",
                recipient_count=len(to) + len(cc or []) + len(bcc or []),
            )

    class FakeFastMCP:
        def __init__(
            self,
            name: str,
            *,
            stateless_http: bool,
            json_response: bool,
        ) -> None:
            self.name = name
            self.stateless_http = stateless_http
            self.json_response = json_response
            self.settings = SimpleNamespace(
                host=None,
                port=None,
                streamable_http_path=None,
            )
            self.run_transport = None

        def tool(self, **kwargs):
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        def run(self, *, transport: str) -> None:
            self.run_transport = transport

    fastmcp_module = ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP
    server_module = ModuleType("mcp.server")
    mcp_module = ModuleType("mcp")

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)
    monkeypatch.setattr("mailgateway_mcp.main.build_app", lambda cfg: FakeApp())

    cfg = OmegaConf.structured(AppConfig())

    server = build_server(cfg)

    assert server.name == "mailgateway-mcp"
    assert server.stateless_http is True
    assert server.json_response is True
    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 8000
    assert server.settings.streamable_http_path == "/mcp"
    assert "list_accounts" in tools
    assert "send_email" in tools

    list_result = tools["list_accounts"]()

    assert list_result == {
        "accounts": [
            {
                "name": "primary",
                "description": "Primary account",
                "account_access_profile": "bot",
                "smtp_enabled": True,
                "imap_enabled": False,
            }
        ]
    }
    assert list_accounts_calls == 1

    send_result = tools["send_email"](
        account="primary",
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Hello",
        text_body="Plain body",
    )

    assert send_result == {
        "ok": True,
        "message_id": "<message-id@example.com>",
        "recipient_count": 3,
    }
    assert send_email_calls == [
        {
            "account": "primary",
            "to": ["to@example.com"],
            "subject": "Hello",
            "text_body": "Plain body",
            "html_body": None,
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
        }
    ]


def test_build_server_describes_send_email_tool_schema() -> None:
    server = build_server(OmegaConf.structured(AppConfig()))

    list_accounts_tool = server._tool_manager._tools["list_accounts"]
    assert "configured accounts available to the caller" in list_accounts_tool.description
    assert list_accounts_tool.parameters["properties"] == {}

    send_email_tool = server._tool_manager._tools["send_email"]
    parameters = send_email_tool.parameters["properties"]

    assert "selected account" in send_email_tool.description
    assert parameters["account"]["type"] == "string"
    assert parameters["account"]["description"] == (
        "Configured account name returned by list_accounts. The selected account "
        "must have SMTP enabled."
    )
    assert parameters["account"]["examples"] == ["primary"]
    assert parameters["to"]["type"] == "array"
    assert parameters["to"]["description"] == "JSON array of recipient email addresses."
    assert parameters["to"]["examples"] == [["to@example.com"]]
    assert parameters["subject"]["type"] == "string"
    assert parameters["subject"]["description"] == "Email subject line."
    assert parameters["text_body"]["description"] == (
        "Optional plain-text body. Provide this or html_body."
    )
    assert parameters["html_body"]["description"] == (
        "Optional HTML body. Provide this or text_body."
    )
    assert parameters["cc"]["description"] == (
        "Optional JSON array of recipient email addresses."
    )
    assert parameters["bcc"]["description"] == (
        "Optional JSON array of recipient email addresses."
    )
