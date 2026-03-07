from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from hydra.core.config_store import ConfigStore


@dataclass
class ServerConfig:
    name: str = "mail-mcp"
    transport: str = "streamable-http"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    stateless_http: bool = True
    json_response: bool = True


@dataclass
class HelloConfig:
    greeting: str = "Hello"
    default_name: str = "world"


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    hello: HelloConfig = field(default_factory=HelloConfig)


class ServerConfigLike(Protocol):
    name: str
    transport: str
    host: str
    port: int
    path: str
    stateless_http: bool
    json_response: bool


class HelloConfigLike(Protocol):
    greeting: str
    default_name: str


class AppConfigLike(Protocol):
    server: ServerConfigLike
    hello: HelloConfigLike


_CONFIG_SCHEMA_NAME = "app_config_schema"
_CONFIG_REGISTERED = False


def register_configs() -> None:
    global _CONFIG_REGISTERED
    if _CONFIG_REGISTERED:
        return

    cs = ConfigStore.instance()
    cs.store(name=_CONFIG_SCHEMA_NAME, node=AppConfig)
    _CONFIG_REGISTERED = True
