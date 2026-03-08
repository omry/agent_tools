from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Protocol

from .config import MailConfigLike, SmtpConfigLike


@dataclass(frozen=True)
class SendEmailResult:
    tool: str
    message_id: str
    recipient_count: int


class SmtpClientLike(Protocol):
    def send(self, message: EmailMessage, sender: str, recipients: list[str]) -> None:
        ...


class MailGatewayApp:
    """Minimal application surface before wiring a concrete MCP SDK."""

    def __init__(
        self,
        mail_config: MailConfigLike,
        smtp_config: SmtpConfigLike,
        smtp_client: SmtpClientLike,
    ) -> None:
        self._mail_config = mail_config
        self._smtp_config = smtp_config
        self._smtp_client = smtp_client

    def tool_names(self) -> list[str]:
        return ["list_accounts", "send_email"]

    def list_accounts(self) -> list[dict[str, object]]:
        summaries: list[dict[str, object]] = []
        for account_name in sorted(self._mail_config.accounts):
            account = self._mail_config.accounts[account_name]
            imap_enabled = account.imap is not None
            profile = self._mail_config.account_access_profiles[
                account.account_access_profile
            ]
            summary: dict[str, object] = {
                "name": account_name,
                "description": account.description,
                "account_access_profile": account.account_access_profile,
                "smtp_enabled": account.smtp is not None,
                "imap_enabled": imap_enabled,
            }
            if imap_enabled:
                summary["imap_read_only"] = profile.read_only
            summaries.append(summary)
        return summaries

    def send_email(
        self,
        to: list[str],
        subject: str,
        text_body: str | None = None,
        html_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> SendEmailResult:
        recipients_to = self._normalize_recipients("to", to)
        recipients_cc = self._normalize_recipients("cc", cc or [])
        recipients_bcc = self._normalize_recipients("bcc", bcc or [])

        if not text_body and not html_body:
            raise ValueError("send_email requires text_body or html_body")

        normalized_subject = subject.strip()
        if not normalized_subject:
            raise ValueError("send_email requires a non-empty subject")

        sender = formataddr((self._smtp_config.from_name, self._smtp_config.from_email))
        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipients_to)
        if recipients_cc:
            message["Cc"] = ", ".join(recipients_cc)
        message["Subject"] = normalized_subject
        message["Message-ID"] = make_msgid(domain=self._sender_domain())

        if text_body:
            message.set_content(text_body)
            if html_body:
                message.add_alternative(html_body, subtype="html")
        else:
            message.set_content(html_body or "", subtype="html")

        envelope_recipients = recipients_to + recipients_cc + recipients_bcc
        self._smtp_client.send(
            message,
            sender=self._smtp_config.from_email,
            recipients=envelope_recipients,
        )

        return SendEmailResult(
            tool="send_email",
            message_id=str(message["Message-ID"]),
            recipient_count=len(envelope_recipients),
        )

    def _normalize_recipients(self, field_name: str, recipients: list[str]) -> list[str]:
        normalized = [recipient.strip() for recipient in recipients if recipient.strip()]
        if field_name == "to" and not normalized:
            raise ValueError("send_email requires at least one recipient in to")

        for recipient in normalized:
            if "@" not in recipient:
                raise ValueError(f"send_email received an invalid {field_name} address")

        return normalized

    def _sender_domain(self) -> str:
        _, _, domain = self._smtp_config.from_email.partition("@")
        return domain or "localhost"
