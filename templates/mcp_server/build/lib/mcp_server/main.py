from __future__ import annotations

from typing import TYPE_CHECKING

import hydra

from .app import McpApp
from .config import AppConfigLike, register_configs

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def build_app(cfg: AppConfigLike) -> McpApp:
    return McpApp(cfg)


def build_server(cfg: AppConfigLike) -> "FastMCP":
    from mcp.server.fastmcp import FastMCP

    app = build_app(cfg)
    server = FastMCP(
        cfg.server.name,
        stateless_http=cfg.server.stateless_http,
        json_response=cfg.server.json_response,
    )
    server.settings.host = cfg.server.host
    server.settings.port = cfg.server.port
    server.settings.streamable_http_path = cfg.server.path

    @server.tool()
    def hello(name: str | None = None) -> str:
        return app.hello(name).message

    return server


register_configs()


@hydra.main(version_base=None, config_path="conf", config_name="config")
def _main(cfg: AppConfigLike) -> None:
    server = build_server(cfg)
    server.run(transport=cfg.server.transport)


def main() -> None:
    _main()
