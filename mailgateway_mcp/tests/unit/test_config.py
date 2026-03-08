import pytest
from hydra import compose, initialize_config_module
from omegaconf import DictConfig

from mailgateway_mcp.config import (
    AccountConfig,
    AccountAccessProfileConfig,
    AppConfig,
    ImapConfig,
    ImapFolderConfig,
    MailConfig,
    SmtpConfig,
    validate_app_config,
    register_configs,
)


def _compose_config(overrides: list[str] | None = None) -> DictConfig:
    register_configs()
    with initialize_config_module(version_base=None, config_module="mailgateway_mcp.conf"):
        return compose(config_name="config", overrides=overrides or [])


def test_compose_config_returns_hydra_config() -> None:
    cfg = _compose_config()

    assert isinstance(cfg, DictConfig)
    assert cfg.server.name == "mailgateway-mcp"
    assert cfg.server.transport == "streamable-http"
    assert cfg.server.host == "127.0.0.1"
    assert cfg.server.port == 8000
    assert cfg.server.path == "/mcp"
    assert cfg.mail.accounts.primary.smtp.host == "localhost"
    assert cfg.mail.accounts.primary.smtp.port == 587
    assert cfg.mail.accounts.primary.smtp.from_email == "agent@example.com"
    assert cfg.mail.accounts.primary.smtp.verify_peer is True
    assert cfg.mail.account_access_profiles.bot.read_only is False


def test_compose_config_applies_overrides() -> None:
    cfg = _compose_config(
        [
            "server.transport=stdio",
            "server.port=9000",
            "mail.accounts.primary.smtp.host=smtp.example.com",
            "mail.accounts.primary.smtp.port=2525",
            "mail.accounts.primary.smtp.from_name=Agent Team",
            "mail.accounts.primary.smtp.verify_peer=false",
        ]
    )

    assert cfg.server.transport == "stdio"
    assert cfg.server.port == 9000
    assert cfg.mail.accounts.primary.smtp.host == "smtp.example.com"
    assert cfg.mail.accounts.primary.smtp.port == 2525
    assert cfg.mail.accounts.primary.smtp.from_name == "Agent Team"
    assert cfg.mail.accounts.primary.smtp.verify_peer is False


def test_hydra_config_preserves_lazy_interpolations() -> None:
    app_config = _compose_config(["mail.accounts.primary.smtp.from_name=${server.name}"])

    assert app_config.server.name == "mailgateway-mcp"
    assert app_config.mail.accounts.primary.smtp.from_name == "mailgateway-mcp"


def test_app_config_rejects_unknown_account_access_profile() -> None:
    with pytest.raises(ValueError, match="unknown account_access_profile"):
        AppConfig(
            mail=MailConfig(
                accounts={
                    "primary": AccountConfig(
                        description="Primary account",
                        account_access_profile="missing",
                        smtp=SmtpConfig(),
                    )
                },
                account_access_profiles={"bot": AccountAccessProfileConfig()},
            )
        )


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("user", ""),
        ("", "secret"),
    ],
)
def test_smtp_config_requires_username_and_password_together_when_auth_enabled(
    username: str,
    password: str,
) -> None:
    with pytest.raises(ValueError, match="username and password together"):
        SmtpConfig(authenticate=True, username=username, password=password)


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("user", ""),
        ("", "secret"),
    ],
)
def test_smtp_config_rejects_credentials_when_auth_is_disabled(
    username: str,
    password: str,
) -> None:
    with pytest.raises(ValueError, match="authenticate is false"):
        SmtpConfig(authenticate=False, username=username, password=password)


def test_smtp_config_rejects_unknown_tls_mode() -> None:
    with pytest.raises(ValueError, match="smtp config tls"):
        SmtpConfig(tls="bogus")


def test_imap_config_requires_default_folder_to_exist() -> None:
    with pytest.raises(ValueError, match="default_folder"):
        ImapConfig(
            default_folder="INBOX",
            folders={"Archive": ImapFolderConfig(description="Archive")},
        )


def test_app_config_rejects_account_without_any_protocols() -> None:
    with pytest.raises(ValueError, match="must enable smtp, imap, or both"):
        AppConfig(
            mail=MailConfig(
                accounts={
                    "primary": AccountConfig(
                        description="Primary account",
                        account_access_profile="bot",
                    )
                },
                account_access_profiles={"bot": AccountAccessProfileConfig()},
            )
        )


def test_app_config_accepts_smtp_only_account() -> None:
    validate_app_config(
        AppConfig(
            mail=MailConfig(
                accounts={
                    "primary": AccountConfig(
                        description="SMTP account",
                        account_access_profile="bot",
                        smtp=SmtpConfig(),
                    )
                },
                account_access_profiles={"bot": AccountAccessProfileConfig()},
            )
        )
    )


def test_app_config_accepts_imap_only_account() -> None:
    validate_app_config(
        AppConfig(
            mail=MailConfig(
                accounts={
                    "primary": AccountConfig(
                        description="IMAP account",
                        account_access_profile="bot",
                        imap=ImapConfig(
                            default_folder="INBOX",
                            folders={"INBOX": ImapFolderConfig(description="Inbox")},
                        ),
                    )
                },
                account_access_profiles={"bot": AccountAccessProfileConfig()},
            )
        )
    )


def test_app_config_accepts_account_with_both_protocols() -> None:
    validate_app_config(
        AppConfig(
            mail=MailConfig(
                accounts={
                    "primary": AccountConfig(
                        description="Full account",
                        account_access_profile="bot",
                        smtp=SmtpConfig(),
                        imap=ImapConfig(
                            default_folder="INBOX",
                            folders={"INBOX": ImapFolderConfig(description="Inbox")},
                        ),
                    )
                },
                account_access_profiles={"bot": AccountAccessProfileConfig()},
            )
        )
    )
