import pytest

from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import (
    AccountAccessProfileConfig,
    AccountConfig,
    ImapConfig,
    ImapFolderConfig,
    MailConfig,
    SmtpConfig,
)


class FakeSmtpClient:
    def __init__(self) -> None:
        self.message = None
        self.sender = None
        self.recipients = None

    def send(self, message, sender: str, recipients: list[str]) -> None:
        self.message = message
        self.sender = sender
        self.recipients = recipients


def _mail_config() -> MailConfig:
    return MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary SMTP account",
                account_access_profile="bot",
                smtp=SmtpConfig(),
            ),
            "owner": AccountConfig(
                description="Owner IMAP account",
                account_access_profile="owner",
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            ),
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
            "owner": AccountAccessProfileConfig(read_only=True),
        },
    )


def test_tool_names_contains_list_accounts_and_send_email() -> None:
    app = MailGatewayApp(_mail_config(), SmtpConfig(), smtp_client=FakeSmtpClient())

    assert app.tool_names() == ["list_accounts", "send_email"]


def test_list_accounts_returns_normalized_account_summaries() -> None:
    app = MailGatewayApp(_mail_config(), SmtpConfig(), smtp_client=FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "owner",
            "description": "Owner IMAP account",
            "account_access_profile": "owner",
            "smtp_enabled": False,
            "imap_enabled": True,
            "imap_read_only": True,
        },
        {
            "name": "primary",
            "description": "Primary SMTP account",
            "account_access_profile": "bot",
            "smtp_enabled": True,
            "imap_enabled": False,
        },
    ]


def test_list_accounts_reports_writable_imap_account() -> None:
    mail_config = MailConfig(
        accounts={
            "alerts": AccountConfig(
                description="Alerts account",
                account_access_profile="bot",
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            )
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
        },
    )
    app = MailGatewayApp(mail_config, SmtpConfig(), smtp_client=FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "alerts",
            "description": "Alerts account",
            "account_access_profile": "bot",
            "smtp_enabled": False,
            "imap_enabled": True,
            "imap_read_only": False,
        }
    ]


def test_list_accounts_reports_account_with_both_protocols() -> None:
    mail_config = MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary full account",
                account_access_profile="bot",
                smtp=SmtpConfig(),
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            )
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
        },
    )
    app = MailGatewayApp(mail_config, SmtpConfig(), smtp_client=FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "primary",
            "description": "Primary full account",
            "account_access_profile": "bot",
            "smtp_enabled": True,
            "imap_enabled": True,
            "imap_read_only": False,
        }
    ]


def test_send_email_submits_message_and_excludes_bcc_header() -> None:
    smtp_client = FakeSmtpClient()
    app = MailGatewayApp(
        _mail_config(),
        SmtpConfig(
            from_email="agent@example.com",
            from_name="Agent MailGateway",
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
    app = MailGatewayApp(_mail_config(), SmtpConfig(), smtp_client=FakeSmtpClient())

    with pytest.raises(ValueError, match="text_body or html_body"):
        app.send_email(
            to=["to@example.com"],
            subject="Missing body",
        )


def test_send_email_supports_html_only_body() -> None:
    smtp_client = FakeSmtpClient()
    app = MailGatewayApp(
        _mail_config(),
        SmtpConfig(
            from_email="agent@example.com",
            from_name="Agent MailGateway",
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


def test_send_email_preserves_non_ascii_subject_and_display_name() -> None:
    smtp_client = FakeSmtpClient()
    app = MailGatewayApp(
        _mail_config(),
        SmtpConfig(
            from_email="agent@example.com",
            from_name="Jöhn Döe",
        ),
        smtp_client=smtp_client,
    )

    app.send_email(
        to=["to@example.com"],
        subject="Héllo ✓",
        text_body="Plain text body",
    )

    assert smtp_client.message["From"] == "Jöhn Döe <agent@example.com>"
    assert smtp_client.message["Subject"] == "Héllo ✓"
