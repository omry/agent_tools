from mail_mcp.app import MailMcpApp
from mail_mcp.config import AppConfig, HelloConfig, ServerConfig


def test_tool_names_contains_hello() -> None:
    app = MailMcpApp(AppConfig())

    assert app.tool_names() == ["hello"]


def test_hello_uses_default_name_from_config() -> None:
    app = MailMcpApp(
        AppConfig(
            server=ServerConfig(name="mail-mcp"),
            hello=HelloConfig(greeting="Hello", default_name="world"),
        )
    )

    result = app.hello()

    assert result.tool == "hello"
    assert result.message == "Hello, world!"


def test_hello_accepts_explicit_name() -> None:
    app = MailMcpApp(AppConfig())

    result = app.hello("Omry")

    assert result.message == "Hello, Omry!"
