import pytest

from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import AppConfig, HelloConfig, ServerConfig, SmtpConfig


class FakeSmtpClient:
    def __init__(self) -> None:
        self.message = None
        self.sender = None
        self.recipients = None

    def send(self, message, sender: str, recipients: list[str]) -> None:
        self.message = message
        self.sender = sender
        self.recipients = recipients


def test_tool_names_contains_hello() -> None:
    app = MailGatewayApp(AppConfig(), smtp_client=FakeSmtpClient())

    assert app.tool_names() == ["hello", "send_email"]


def test_hello_uses_default_name_from_config() -> None:
    app = MailGatewayApp(
        AppConfig(
            server=ServerConfig(name="mailgateway-mcp"),
            hello=HelloConfig(greeting="Hello", default_name="world"),
            smtp=SmtpConfig(from_email="agent@example.com"),
        ),
        smtp_client=FakeSmtpClient(),
    )

    result = app.hello()

    assert result.tool == "hello"
    assert result.message == "Hello, world!"


def test_hello_accepts_explicit_name() -> None:
    app = MailGatewayApp(AppConfig(), smtp_client=FakeSmtpClient())

    result = app.hello("Omry")

    assert result.message == "Hello, Omry!"


def test_send_email_submits_message_and_excludes_bcc_header() -> None:
    smtp_client = FakeSmtpClient()
    app = MailGatewayApp(
        AppConfig(
            smtp=SmtpConfig(
                from_email="agent@example.com",
                from_name="Agent MailGateway",
            )
        ),
        smtp_client=smtp_client,
    )

    result = app.send_email(
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Hello",
        text_body="Plain text body",
        html_body="<p>HTML body</p>",
    )

    assert result.tool == "send_email"
    assert result.recipient_count == 3
    assert smtp_client.sender == "agent@example.com"
    assert smtp_client.recipients == [
        "to@example.com",
        "cc@example.com",
        "bcc@example.com",
    ]
    assert smtp_client.message["From"] == "Agent MailGateway <agent@example.com>"
    assert smtp_client.message["To"] == "to@example.com"
    assert smtp_client.message["Cc"] == "cc@example.com"
    assert smtp_client.message["Subject"] == "Hello"
    assert smtp_client.message["Bcc"] is None


def test_send_email_requires_body_content() -> None:
    app = MailGatewayApp(AppConfig(), smtp_client=FakeSmtpClient())

    with pytest.raises(ValueError, match="text_body or html_body"):
        app.send_email(
            to=["to@example.com"],
            subject="Missing body",
        )


def test_send_email_supports_html_only_body() -> None:
    smtp_client = FakeSmtpClient()
    app = MailGatewayApp(
        AppConfig(
            smtp=SmtpConfig(
                from_email="agent@example.com",
                from_name="Agent MailGateway",
            )
        ),
        smtp_client=smtp_client,
    )

    app.send_email(
        to=["to@example.com"],
        subject="Hello",
        html_body="<p>HTML only</p>",
    )

    assert smtp_client.message.get_content_type() == "text/html"
    assert smtp_client.message.is_multipart() is False
    assert "<p>HTML only</p>" in smtp_client.message.get_content()
