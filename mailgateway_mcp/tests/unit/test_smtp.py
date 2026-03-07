from __future__ import annotations

import ssl
from email.message import EmailMessage

from mailgateway_mcp.config import SmtpConfig
from mailgateway_mcp.smtp import SmtpSubmissionClient


class FakeServer:
    def __init__(self) -> None:
        self.starttls_context = None
        self.sent_message = None
        self.sent_from = None
        self.sent_to = None
        self.login_args = None
        self.ehlo_calls = 0

    def __enter__(self) -> "FakeServer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def ehlo(self) -> None:
        self.ehlo_calls += 1

    def starttls(self, *, context: ssl.SSLContext) -> None:
        self.starttls_context = context

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def send_message(self, message: EmailMessage, from_addr: str, to_addrs: list[str]) -> None:
        self.sent_message = message
        self.sent_from = from_addr
        self.sent_to = to_addrs


def test_build_ssl_context_disables_verification_when_verify_peer_is_false() -> None:
    client = SmtpSubmissionClient(
        SmtpConfig(verify_peer=False)
    )

    context = client._build_ssl_context()

    assert context.check_hostname is False
    assert context.verify_mode == ssl.CERT_NONE


def test_send_uses_unverified_context_for_starttls(monkeypatch) -> None:
    fake_server = FakeServer()

    def fake_smtp(host: str, port: int, timeout: float) -> FakeServer:
        assert host == "smtp.example.com"
        assert port == 587
        assert timeout == 30.0
        return fake_server

    monkeypatch.setattr("mailgateway_mcp.smtp.smtplib.SMTP", fake_smtp)

    client = SmtpSubmissionClient(
        SmtpConfig(
            host="smtp.example.com",
            verify_peer=False,
            username="user",
            password="secret",
        )
    )

    message = EmailMessage()
    message["Subject"] = "Hello"

    client.send(message, sender="agent@example.com", recipients=["to@example.com"])

    assert fake_server.starttls_context is not None
    assert fake_server.starttls_context.check_hostname is False
    assert fake_server.starttls_context.verify_mode == ssl.CERT_NONE
    assert fake_server.login_args == ("user", "secret")
    assert fake_server.sent_from == "agent@example.com"
    assert fake_server.sent_to == ["to@example.com"]
