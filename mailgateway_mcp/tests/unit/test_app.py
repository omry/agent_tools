import pytest

from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import (
    AccountAccessProfileConfig,
    AccountConfig,
    AccountSensitivityTier,
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


class RecordingSmtpClientFactory:
    def __init__(self) -> None:
        self.configs = []
        self.clients: list[FakeSmtpClient] = []

    def __call__(self, config) -> FakeSmtpClient:
        self.configs.append(config)
        client = FakeSmtpClient()
        self.clients.append(client)
        return client


def _mail_config() -> MailConfig:
    return MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary SMTP account",
                account_access_profile="bot",
                smtp=SmtpConfig(),
            ),
            "personal": AccountConfig(
                description="Personal IMAP account",
                account_access_profile="personal",
                sensitivity_tier=AccountSensitivityTier.sensitive,
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            ),
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
            "personal": AccountAccessProfileConfig(read_only=True),
        },
    )


def test_tool_names_contains_list_accounts_and_send_email() -> None:
    app = MailGatewayApp(_mail_config(), smtp_client_factory=lambda config: FakeSmtpClient())

    assert app.tool_names() == ["list_accounts", "send_email"]


def test_list_accounts_returns_normalized_account_summaries() -> None:
    app = MailGatewayApp(_mail_config(), smtp_client_factory=lambda config: FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "personal",
            "description": "Personal IMAP account",
            "account_access_profile": "personal",
            "sensitivity_tier": "sensitive",
            "smtp_enabled": False,
            "imap_enabled": True,
            "imap_read_only": True,
        },
        {
            "name": "primary",
            "description": "Primary SMTP account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
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
                sensitivity_tier=AccountSensitivityTier.standard,
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
    app = MailGatewayApp(mail_config, smtp_client_factory=lambda config: FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "alerts",
            "description": "Alerts account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
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
                sensitivity_tier=AccountSensitivityTier.standard,
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
    app = MailGatewayApp(mail_config, smtp_client_factory=lambda config: FakeSmtpClient())

    assert app.list_accounts() == [
        {
            "name": "primary",
            "description": "Primary full account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
            "smtp_enabled": True,
            "imap_enabled": True,
            "imap_read_only": False,
        }
    ]


def test_send_email_submits_message_and_excludes_bcc_header() -> None:
    smtp_factory = RecordingSmtpClientFactory()
    app = MailGatewayApp(
        _mail_config(),
        smtp_client_factory=smtp_factory,
    )

    result = app.send_email(
        account="primary",
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Hello",
        text_body="Plain text body",
        html_body="<p>HTML body</p>",
    )

    assert result.tool == "send_email"
    assert result.recipient_count == 3
    smtp_client = smtp_factory.clients[-1]
    assert smtp_client.sender == "agent@example.com"
    assert smtp_client.recipients == [
        "to@example.com",
        "cc@example.com",
        "bcc@example.com",
    ]
    assert smtp_client.message["From"] == "MailGateway <agent@example.com>"
    assert smtp_client.message["To"] == "to@example.com"
    assert smtp_client.message["Cc"] == "cc@example.com"
    assert smtp_client.message["Subject"] == "Hello"
    assert smtp_client.message["Bcc"] is None


def test_send_email_requires_body_content() -> None:
    app = MailGatewayApp(_mail_config(), smtp_client_factory=lambda config: FakeSmtpClient())

    with pytest.raises(ValueError, match="text_body or html_body"):
        app.send_email(
            account="primary",
            to=["to@example.com"],
            subject="Missing body",
        )


def test_send_email_supports_html_only_body() -> None:
    smtp_factory = RecordingSmtpClientFactory()
    app = MailGatewayApp(
        _mail_config(),
        smtp_client_factory=smtp_factory,
    )

    app.send_email(
        account="primary",
        to=["to@example.com"],
        subject="Hello",
        html_body="<p>HTML only</p>",
    )

    smtp_client = smtp_factory.clients[-1]
    assert smtp_client.message.get_content_type() == "text/html"
    assert smtp_client.message.is_multipart() is False
    assert "<p>HTML only</p>" in smtp_client.message.get_content()


def test_send_email_preserves_non_ascii_subject_and_display_name() -> None:
    smtp_factory = RecordingSmtpClientFactory()
    mail_config = MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary SMTP account",
                account_access_profile="bot",
                sensitivity_tier=AccountSensitivityTier.standard,
                smtp=SmtpConfig(
                    from_email="agent@example.com",
                    from_name="Jöhn Döe",
                ),
            ),
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
        },
    )
    app = MailGatewayApp(
        mail_config,
        smtp_client_factory=smtp_factory,
    )

    app.send_email(
        account="primary",
        to=["to@example.com"],
        subject="Héllo ✓",
        text_body="Plain text body",
    )

    smtp_client = smtp_factory.clients[-1]
    assert smtp_client.message["From"] == "Jöhn Döe <agent@example.com>"
    assert smtp_client.message["Subject"] == "Héllo ✓"


def test_send_email_rejects_unknown_account() -> None:
    app = MailGatewayApp(_mail_config(), smtp_client_factory=lambda config: FakeSmtpClient())

    with pytest.raises(ValueError, match="unknown account: missing"):
        app.send_email(
            account="missing",
            to=["to@example.com"],
            subject="Hello",
            text_body="Plain text body",
        )


def test_send_email_rejects_imap_only_account() -> None:
    app = MailGatewayApp(_mail_config(), smtp_client_factory=lambda config: FakeSmtpClient())

    with pytest.raises(ValueError, match="SMTP-enabled account: personal"):
        app.send_email(
            account="personal",
            to=["to@example.com"],
            subject="Hello",
            text_body="Plain text body",
        )


def test_send_email_uses_selected_account_smtp_config() -> None:
    smtp_factory = RecordingSmtpClientFactory()
    mail_config = MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary SMTP account",
                account_access_profile="bot",
                sensitivity_tier=AccountSensitivityTier.standard,
                smtp=SmtpConfig(
                    from_email="agent@example.com",
                    from_name="Primary Sender",
                ),
            ),
            "alerts": AccountConfig(
                description="Alerts SMTP account",
                account_access_profile="bot",
                sensitivity_tier=AccountSensitivityTier.sensitive,
                smtp=SmtpConfig(
                    from_email="alerts@example.com",
                    from_name="Alerts Sender",
                ),
            ),
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(read_only=False),
        },
    )
    app = MailGatewayApp(mail_config, smtp_client_factory=smtp_factory)

    app.send_email(
        account="alerts",
        to=["to@example.com"],
        subject="Hello",
        text_body="Plain text body",
    )

    smtp_client = smtp_factory.clients[-1]
    assert smtp_factory.configs[-1].from_email == "alerts@example.com"
    assert smtp_client.sender == "alerts@example.com"
    assert smtp_client.message["From"] == "Alerts Sender <alerts@example.com>"
