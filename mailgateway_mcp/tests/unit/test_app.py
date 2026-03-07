from mailgateway_mcp.app import MailGatewayApp
from mailgateway_mcp.config import AppConfig, HelloConfig, ServerConfig


def test_tool_names_contains_hello() -> None:
    app = MailGatewayApp(AppConfig())

    assert app.tool_names() == ["hello"]


def test_hello_uses_default_name_from_config() -> None:
    app = MailGatewayApp(
        AppConfig(
            server=ServerConfig(name="mailgateway-mcp"),
            hello=HelloConfig(greeting="Hello", default_name="world"),
        )
    )

    result = app.hello()

    assert result.tool == "hello"
    assert result.message == "Hello, world!"


def test_hello_accepts_explicit_name() -> None:
    app = MailGatewayApp(AppConfig())

    result = app.hello("Omry")

    assert result.message == "Hello, Omry!"
