import pytest
from email.message import EmailMessage

from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import (
    AccountAccessProfileConfig,
    AccountConfig,
    AccountSensitivityTier,
    ImapAccessPolicyConfig,
    ImapConfig,
    ImapFlagMode,
    ImapFolderConfig,
    ImapSystemFlagsPolicyConfig,
    MailConfig,
    SmtpConfigLike,
    SmtpConfig,
)


class FakeSmtpClient:
    def __init__(self) -> None:
        self.message: EmailMessage | None = None
        self.sender: str | None = None
        self.recipients: list[str] | None = None

    def send(
        self,
        message: EmailMessage,
        sender: str,
        recipients: list[str],
    ) -> None:
        self.message = message
        self.sender = sender
        self.recipients = recipients


class RecordingSmtpClientFactory:
    def __init__(self) -> None:
        self.configs: list[SmtpConfigLike] = []
        self.clients: list[FakeSmtpClient] = []

    def __call__(self, config: SmtpConfigLike) -> FakeSmtpClient:
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
            "bot": AccountAccessProfileConfig(),
            "personal": AccountAccessProfileConfig(
                imap=ImapAccessPolicyConfig(
                    allow_move=False,
                    allow_delete=False,
                )
            ),
        },
    )


def test_tool_names_contains_list_accounts_and_send_email() -> None:
    app = MailGatewayApp(
        _mail_config(), smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.tool_names() == ["list_accounts", "send_email"]


def test_list_accounts_returns_normalized_account_summaries() -> None:
    app = MailGatewayApp(
        _mail_config(), smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "personal",
            "description": "Personal IMAP account",
            "account_access_profile": "personal",
            "sensitivity_tier": "sensitive",
            "smtp": {
                "send": "unavailable",
            },
            "imap": {
                "enabled": True,
                "message": {
                    "read_allowed": True,
                    "move_allowed": False,
                    "delete_allowed": False,
                    "flags": {
                        "seen": "read_only",
                        "flagged": "read_only",
                        "answered": "read_only",
                        "deleted": "read_only",
                        "draft": "read_only",
                    },
                },
            },
        },
        {
            "name": "primary",
            "description": "Primary SMTP account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
            "smtp": {
                "send": "allowed",
            },
            "imap": {
                "enabled": False,
            },
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
            "bot": AccountAccessProfileConfig(),
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "alerts",
            "description": "Alerts account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
            "smtp": {
                "send": "unavailable",
            },
            "imap": {
                "enabled": True,
                "message": {
                    "read_allowed": True,
                    "move_allowed": True,
                    "delete_allowed": True,
                    "flags": {
                        "seen": "read_only",
                        "flagged": "read_only",
                        "answered": "read_only",
                        "deleted": "read_only",
                        "draft": "read_only",
                    },
                },
            },
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
            "bot": AccountAccessProfileConfig(),
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "primary",
            "description": "Primary full account",
            "account_access_profile": "bot",
            "sensitivity_tier": "standard",
            "smtp": {
                "send": "allowed",
            },
            "imap": {
                "enabled": True,
                "message": {
                    "read_allowed": True,
                    "move_allowed": True,
                    "delete_allowed": True,
                    "flags": {
                        "seen": "read_only",
                        "flagged": "read_only",
                        "answered": "read_only",
                        "deleted": "read_only",
                        "draft": "read_only",
                    },
                },
            },
        }
    ]


def test_list_accounts_reports_configured_user_flag_access() -> None:
    mail_config = MailConfig(
        accounts={
            "personal": AccountConfig(
                description="Personal account",
                account_access_profile="personal",
                sensitivity_tier=AccountSensitivityTier.sensitive,
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            )
        },
        account_access_profiles={
            "personal": AccountAccessProfileConfig(
                imap=ImapAccessPolicyConfig(
                    allow_move=False,
                    allow_delete=False,
                    user_flags={
                        "bot.followed_up": ImapFlagMode.read_write,
                        "triaged": ImapFlagMode.read_only,
                        "internal_only": ImapFlagMode.hidden,
                    },
                )
            ),
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "personal",
            "description": "Personal account",
            "account_access_profile": "personal",
            "sensitivity_tier": "sensitive",
            "smtp": {
                "send": "unavailable",
            },
            "imap": {
                "enabled": True,
                "message": {
                    "read_allowed": True,
                    "move_allowed": False,
                    "delete_allowed": False,
                    "flags": {
                        "seen": "read_only",
                        "flagged": "read_only",
                        "answered": "read_only",
                        "deleted": "read_only",
                        "draft": "read_only",
                        "user": {
                            "bot.followed_up": "read_write",
                            "triaged": "read_only",
                        },
                    },
                },
            },
        }
    ]


def test_list_accounts_reports_all_system_flags() -> None:
    mail_config = MailConfig(
        accounts={
            "personal": AccountConfig(
                description="Personal account",
                account_access_profile="personal",
                sensitivity_tier=AccountSensitivityTier.sensitive,
                imap=ImapConfig(
                    default_folder="INBOX",
                    folders={"INBOX": ImapFolderConfig(description="Inbox")},
                ),
            )
        },
        account_access_profiles={
            "personal": AccountAccessProfileConfig(
                imap=ImapAccessPolicyConfig(
                    allow_move=False,
                    allow_delete=False,
                    system_flags=ImapSystemFlagsPolicyConfig(
                        seen=ImapFlagMode.read_write,
                        flagged=ImapFlagMode.read_write,
                        deleted=ImapFlagMode.hidden,
                    ),
                )
            ),
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "personal",
            "description": "Personal account",
            "account_access_profile": "personal",
            "sensitivity_tier": "sensitive",
            "smtp": {
                "send": "unavailable",
            },
            "imap": {
                "enabled": True,
                "message": {
                    "read_allowed": True,
                    "move_allowed": False,
                    "delete_allowed": False,
                    "flags": {
                        "seen": "read_write",
                        "flagged": "read_write",
                        "answered": "read_only",
                        "deleted": "hidden",
                        "draft": "read_only",
                    },
                },
            },
        }
    ]


def test_list_accounts_reports_disabled_smtp_account() -> None:
    mail_config = MailConfig(
        accounts={
            "secondary": AccountConfig(
                description="Secondary SMTP account",
                account_access_profile="personal",
                smtp=SmtpConfig(),
            )
        },
        account_access_profiles={
            "personal": AccountAccessProfileConfig(allow_smtp_send=False),
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    assert app.list_accounts() == [
        {
            "name": "secondary",
            "description": "Secondary SMTP account",
            "account_access_profile": "personal",
            "sensitivity_tier": "standard",
            "smtp": {
                "send": "disabled",
            },
            "imap": {
                "enabled": False,
            },
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
    assert smtp_client.message is not None
    assert smtp_client.sender is not None
    assert smtp_client.recipients is not None
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
    app = MailGatewayApp(
        _mail_config(), smtp_client_factory=lambda config: FakeSmtpClient()
    )

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
    assert smtp_client.message is not None
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
            "bot": AccountAccessProfileConfig(),
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
    assert smtp_client.message is not None
    assert smtp_client.message["From"] == "Jöhn Döe <agent@example.com>"
    assert smtp_client.message["Subject"] == "Héllo ✓"


def test_send_email_rejects_unknown_account() -> None:
    app = MailGatewayApp(
        _mail_config(), smtp_client_factory=lambda config: FakeSmtpClient()
    )

    with pytest.raises(ValueError, match="unknown account: missing"):
        app.send_email(
            account="missing",
            to=["to@example.com"],
            subject="Hello",
            text_body="Plain text body",
        )


def test_send_email_rejects_imap_only_account() -> None:
    app = MailGatewayApp(
        _mail_config(), smtp_client_factory=lambda config: FakeSmtpClient()
    )

    with pytest.raises(ValueError, match="SMTP-enabled account: personal"):
        app.send_email(
            account="personal",
            to=["to@example.com"],
            subject="Hello",
            text_body="Plain text body",
        )


def test_send_email_rejects_account_with_disabled_send_policy() -> None:
    mail_config = MailConfig(
        accounts={
            "primary": AccountConfig(
                description="Primary SMTP account",
                account_access_profile="bot",
                smtp=SmtpConfig(),
            )
        },
        account_access_profiles={
            "bot": AccountAccessProfileConfig(allow_smtp_send=False)
        },
    )
    app = MailGatewayApp(
        mail_config, smtp_client_factory=lambda config: FakeSmtpClient()
    )

    with pytest.raises(ValueError, match="not allowed for account: primary"):
        app.send_email(
            account="primary",
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
            "bot": AccountAccessProfileConfig(),
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
    assert smtp_client.message is not None
    assert smtp_factory.configs[-1].from_email == "alerts@example.com"
    assert smtp_client.sender == "alerts@example.com"
    assert smtp_client.message["From"] == "Alerts Sender <alerts@example.com>"
