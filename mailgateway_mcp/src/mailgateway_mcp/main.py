from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal, cast

import hydra
from pydantic import Field

from .app import MailGatewayApp
from .config import AppConfig, register_configs
from .smtp import SmtpSubmissionClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


TransportMode = Literal["stdio", "sse", "streamable-http"]


RecipientList = Annotated[
    list[str],
    Field(
        description="JSON array of recipient email addresses.",
        examples=[["to@example.com"]],
    ),
]

OptionalRecipientList = Annotated[
    list[str] | None,
    Field(
        description="Optional JSON array of recipient email addresses.",
        examples=[["person@example.com"]],
    ),
]

AccountName = Annotated[
    str,
    Field(
        description=(
            "Configured account name returned by list_accounts. The selected account "
            "must have SMTP enabled."
        ),
        examples=["primary"],
        min_length=1,
    ),
]

SubjectLine = Annotated[
    str,
    Field(
        description="Email subject line.",
        examples=["Hello from MCP"],
        min_length=1,
    ),
]

TextBody = Annotated[
    str | None,
    Field(
        description="Optional plain-text body. Provide this or html_body.",
        examples=["Plain text message body."],
    ),
]

HtmlBody = Annotated[
    str | None,
    Field(
        description="Optional HTML body. Provide this or text_body.",
        examples=["<p>Hello from MCP</p>"],
    ),
]


def build_app(cfg: AppConfig) -> MailGatewayApp:
    return MailGatewayApp(
        cfg.mail,
        smtp_client_factory=SmtpSubmissionClient,
    )


def build_server(cfg: AppConfig) -> "FastMCP":
    from mcp.server.fastmcp import FastMCP

    app = build_app(cfg)
    server = FastMCP(
        cfg.server.name,
        stateless_http=cfg.server.stateless_http,
        json_response=cfg.server.json_response,
    )
    server.settings.host = cfg.server.host
    server.settings.port = cfg.server.port
    server.settings.streamable_http_path = cfg.server.path

    @server.tool(
        description=(
            "Return the configured accounts available to the caller, along with "
            "lightweight metadata needed to choose an account for later SMTP or "
            "future IMAP operations."
        )
    )
    def list_accounts() -> dict[str, object]:
        return {
            "accounts": app.list_accounts(),
        }

    @server.tool(
        description=(
            "Send a single email message through the configured SMTP submission "
            "server for the selected account. Use an account name returned by "
            "list_accounts, JSON arrays for to, cc, and bcc, at least one "
            "recipient in to, and at least one of text_body or html_body."
        )
    )
    def send_email(
        account: AccountName,
        to: RecipientList,
        subject: SubjectLine,
        text_body: TextBody = None,
        html_body: HtmlBody = None,
        cc: OptionalRecipientList = None,
        bcc: OptionalRecipientList = None,
    ) -> dict[str, object]:
        result = app.send_email(
            account=account,
            to=to,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            cc=cc,
            bcc=bcc,
        )
        return {
            "ok": True,
            "message_id": result.message_id,
            "recipient_count": result.recipient_count,
        }

    return server


register_configs()


@hydra.main(version_base=None, config_path="conf", config_name="config")
def _main(cfg: AppConfig) -> None:
    server = build_server(cfg)
    server.run(transport=cast(TransportMode, cfg.server.transport))


def main() -> None:
    _main()
