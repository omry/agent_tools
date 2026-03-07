from __future__ import annotations

from typing import TYPE_CHECKING

import hydra

from .app import MailGatewayApp
from .config import AppConfigLike, register_configs
from .smtp import SmtpSubmissionClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def build_app(cfg: AppConfigLike) -> MailGatewayApp:
    return MailGatewayApp(cfg, smtp_client=SmtpSubmissionClient(cfg.smtp))


def build_server(cfg: AppConfigLike) -> "FastMCP":
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

    @server.tool()
    def hello(name: str | None = None) -> str:
        return app.hello(name).message

    @server.tool()
    def send_email(
        to: list[str],
        subject: str,
        text_body: str | None = None,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict[str, object]:
        result = app.send_email(
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
def _main(cfg: AppConfigLike) -> None:
    server = build_server(cfg)
    server.run(transport=cfg.server.transport)


def main() -> None:
    _main()
