from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Callable, Protocol

from .config import (
    AccountConfig,
    ImapAccessPolicyConfig,
    ImapFlagMode,
    MailConfig,
    SmtpConfigLike,
)


@dataclass(frozen=True)
class SendEmailResult:
    tool: str
    message_id: str
    recipient_count: int


class SmtpClientLike(Protocol):
    def send(
        self, message: EmailMessage, sender: str, recipients: list[str]
    ) -> None: ...


SmtpClientFactory = Callable[[SmtpConfigLike], SmtpClientLike]


class MailGatewayApp:
    """Minimal application surface before wiring a concrete MCP SDK."""

    def __init__(
        self,
        mail_config: MailConfig,
        smtp_client_factory: SmtpClientFactory,
    ) -> None:
        self._mail_config = mail_config
        self._smtp_client_factory = smtp_client_factory

    def tool_names(self) -> list[str]:
        return ["list_accounts", "send_email"]

    def list_accounts(self) -> list[dict[str, object]]:
        summaries: list[dict[str, object]] = []
        for account_name in sorted(self._mail_config.accounts):
            account = self._mail_config.accounts[account_name]
            profile = self._mail_config.account_access_profiles[
                account.account_access_profile
            ]
            smtp_send_state = self._smtp_send_state(account, profile.allow_smtp_send)
            imap_enabled = account.imap is not None
            smtp_summary: dict[str, object] = {
                "send": smtp_send_state,
            }
            imap_summary: dict[str, object] = {
                "enabled": imap_enabled,
            }
            summary: dict[str, object] = {
                "name": account_name,
                "description": account.description,
                "account_access_profile": account.account_access_profile,
                "sensitivity_tier": account.sensitivity_tier.value,
                "smtp": smtp_summary,
                "imap": imap_summary,
            }
            if imap_enabled:
                imap_summary["message"] = self._imap_message_summary(profile.imap)
            summaries.append(summary)
        return summaries

    def send_email(
        self,
        account: str,
        to: list[str],
        subject: str,
        text_body: str | None = None,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> SendEmailResult:
        smtp_config = self._resolve_smtp_config(account)
        recipients_to = self._normalize_recipients("to", to)
        recipients_cc = self._normalize_recipients("cc", cc or [])
        recipients_bcc = self._normalize_recipients("bcc", bcc or [])

        if not text_body and not html_body:
            raise ValueError("send_email requires text_body or html_body")

        normalized_subject = subject.strip()
        if not normalized_subject:
            raise ValueError("send_email requires a non-empty subject")

        sender = formataddr((smtp_config.from_name, smtp_config.from_email))
        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipients_to)
        if recipients_cc:
            message["Cc"] = ", ".join(recipients_cc)
        message["Subject"] = normalized_subject
        message["Message-ID"] = make_msgid(domain=self._sender_domain(smtp_config))

        if text_body:
            message.set_content(text_body)
            if html_body:
                message.add_alternative(html_body, subtype="html")
        else:
            message.set_content(html_body or "", subtype="html")

        envelope_recipients = recipients_to + recipients_cc + recipients_bcc
        smtp_client = self._smtp_client_factory(smtp_config)
        smtp_client.send(
            message,
            sender=smtp_config.from_email,
            recipients=envelope_recipients,
        )

        return SendEmailResult(
            tool="send_email",
            message_id=str(message["Message-ID"]),
            recipient_count=len(envelope_recipients),
        )

    def _normalize_recipients(
        self, field_name: str, recipients: list[str]
    ) -> list[str]:
        normalized = [
            recipient.strip() for recipient in recipients if recipient.strip()
        ]
        if field_name == "to" and not normalized:
            raise ValueError("send_email requires at least one recipient in to")

        for recipient in normalized:
            if "@" not in recipient:
                raise ValueError(f"send_email received an invalid {field_name} address")

        return normalized

    def _sender_domain(self, smtp_config: SmtpConfigLike) -> str:
        _, _, domain = smtp_config.from_email.partition("@")
        return domain or "localhost"

    def _resolve_smtp_config(self, account_name: str) -> SmtpConfigLike:
        account = self._mail_config.accounts.get(account_name)
        if account is None:
            raise ValueError(f"send_email received an unknown account: {account_name}")

        if account.smtp is None:
            raise ValueError(
                f"send_email requires an SMTP-enabled account: {account_name}"
            )

        profile = self._mail_config.account_access_profiles[
            account.account_access_profile
        ]
        if not profile.allow_smtp_send:
            raise ValueError(f"send_email is not allowed for account: {account_name}")

        return account.smtp

    def _smtp_send_state(self, account: AccountConfig, allow_smtp_send: bool) -> str:
        if account.smtp is None:
            return "unavailable"
        if allow_smtp_send:
            return "allowed"
        return "disabled"

    def _imap_message_summary(
        self, imap_policy: ImapAccessPolicyConfig
    ) -> dict[str, object]:
        flags = self._imap_flag_summary(imap_policy)
        return {
            "read_allowed": imap_policy.allow_read,
            "move_allowed": imap_policy.allow_move,
            "delete_allowed": imap_policy.allow_delete,
            "flags": flags,
        }

    def _imap_flag_summary(
        self, imap_policy: ImapAccessPolicyConfig
    ) -> dict[str, object]:
        system_flags = {
            "seen": imap_policy.system_flags.seen,
            "flagged": imap_policy.system_flags.flagged,
            "answered": imap_policy.system_flags.answered,
            "deleted": imap_policy.system_flags.deleted,
            "draft": imap_policy.system_flags.draft,
        }
        flags: dict[str, object] = {
            flag_name: mode.value for flag_name, mode in system_flags.items()
        }

        user_flags = {
            flag_name: mode.value
            for flag_name, mode in sorted(imap_policy.user_flags.items())
            if mode is not ImapFlagMode.hidden
        }
        if user_flags:
            flags["user"] = user_flags

        return flags
