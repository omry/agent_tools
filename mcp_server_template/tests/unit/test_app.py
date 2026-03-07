from mcp_server.app import McpApp
from mcp_server.config import AppConfig, HelloConfig, ServerConfig


def test_tool_names_contains_hello() -> None:
    app = McpApp(AppConfig())

    assert app.tool_names() == ["hello"]


def test_hello_uses_default_name_from_config() -> None:
    app = McpApp(
        AppConfig(
            server=ServerConfig(name="mcp-server"),
            hello=HelloConfig(greeting="Hello", default_name="world"),
        )
    )

    result = app.hello()

    assert result.tool == "hello"
    assert result.message == "Hello, world!"


def test_hello_accepts_explicit_name() -> None:
    app = McpApp(AppConfig())

    result = app.hello("Omry")

    assert result.message == "Hello, Omry!"
