from __future__ import annotations

from email import policy
from email.parser import BytesParser

import pytest

from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import AppConfig, SmtpConfig
from mailgateway_mcp.smtp import SmtpSubmissionClient

from aiosmtpd.controller import Controller


class CapturingHandler:
    def __init__(self) -> None:
        self.envelopes = []

    async def handle_DATA(self, server, session, envelope) -> str:
        self.envelopes.append(envelope)
        return "250 Message accepted for delivery"


@pytest.fixture
def smtp_server(free_tcp_port: int):
    handler = CapturingHandler()
    controller = Controller(handler, hostname="127.0.0.1", port=free_tcp_port)
    controller.start()
    try:
        yield handler, controller
    finally:
        controller.stop()


def test_send_email_submits_to_aiosmtpd(smtp_server) -> None:
    handler, controller = smtp_server
    smtp_config = SmtpConfig(
        host=controller.hostname,
        port=controller.port,
        from_email="agent@example.com",
        from_name="Agent MailGateway",
        starttls=False,
        use_ssl=False,
    )
    app = MailGatewayApp(
        AppConfig(smtp=smtp_config),
        smtp_client=SmtpSubmissionClient(smtp_config),
    )

    result = app.send_email(
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Integration Hello",
        text_body="Plain body",
        html_body="<p>HTML body</p>",
    )

    assert result.tool == "send_email"
    assert result.recipient_count == 3
    assert len(handler.envelopes) == 1

    envelope = handler.envelopes[0]
    parsed_message = BytesParser(policy=policy.default).parsebytes(envelope.content)

    assert envelope.mail_from == "agent@example.com"
    assert envelope.rcpt_tos == [
        "to@example.com",
        "cc@example.com",
        "bcc@example.com",
    ]
    assert parsed_message["From"] == "Agent MailGateway <agent@example.com>"
    assert parsed_message["To"] == "to@example.com"
    assert parsed_message["Cc"] == "cc@example.com"
    assert parsed_message["Subject"] == "Integration Hello"
    assert parsed_message["Bcc"] is None
