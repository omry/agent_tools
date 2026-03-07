import sys
from types import ModuleType
from types import SimpleNamespace

import pytest
from omegaconf import OmegaConf

from mailgateway_mcp.config import AppConfig, HelloConfig
from mailgateway_mcp.main import build_app, build_server


def test_build_app_accepts_hydra_config() -> None:
    cfg = OmegaConf.structured(
        AppConfig(hello=HelloConfig(default_name="Hydra"))
    )

    app = build_app(cfg)

    assert app.hello().message == "Hello, Hydra!"


def test_build_server_registers_hello_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    tools: dict[str, object] = {}

    class FakeFastMCP:
        def __init__(
            self,
            name: str,
            *,
            stateless_http: bool,
            json_response: bool,
        ) -> None:
            self.name = name
            self.stateless_http = stateless_http
            self.json_response = json_response
            self.settings = SimpleNamespace(
                host=None,
                port=None,
                streamable_http_path=None,
            )
            self.run_transport = None

        def tool(self):
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        def run(self, *, transport: str) -> None:
            self.run_transport = transport

    fastmcp_module = ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = FakeFastMCP
    server_module = ModuleType("mcp.server")
    mcp_module = ModuleType("mcp")

    monkeypatch.setitem(sys.modules, "mcp", mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", server_module)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_module)

    cfg = OmegaConf.structured(
        AppConfig(hello=HelloConfig(default_name="Hydra"))
    )

    server = build_server(cfg)

    assert server.name == "mailgateway-mcp"
    assert server.stateless_http is True
    assert server.json_response is True
    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 8000
    assert server.settings.streamable_http_path == "/mcp"
    assert "hello" in tools
    assert "send_email" in tools
    assert tools["hello"]() == "Hello, Hydra!"
    assert tools["hello"]("Omry") == "Hello, Omry!"
