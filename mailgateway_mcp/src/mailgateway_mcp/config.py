from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from hydra.core.config_store import ConfigStore


@dataclass
class ServerConfig:
    name: str = "mailgateway-mcp"
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
class SmtpConfig:
    host: str = "localhost"
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = "agent@example.com"
    from_name: str = "MailGateway"
    starttls: bool = True
    use_ssl: bool = False
    verify_peer: bool = True
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        validate_smtp_config(self)


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    hello: HelloConfig = field(default_factory=HelloConfig)
    smtp: SmtpConfig = field(default_factory=SmtpConfig)


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


class SmtpConfigLike(Protocol):
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    starttls: bool
    use_ssl: bool
    verify_peer: bool
    timeout_seconds: float


class AppConfigLike(Protocol):
    server: ServerConfigLike
    hello: HelloConfigLike
    smtp: SmtpConfigLike


def validate_smtp_config(config: SmtpConfigLike) -> None:
    if config.use_ssl and config.starttls:
        raise ValueError("smtp config cannot enable both use_ssl and starttls")

    has_username = bool(config.username)
    has_password = bool(config.password)
    if has_username != has_password:
        raise ValueError("smtp config requires username and password together")


_CONFIG_SCHEMA_NAME = "mailgateway_app_config_schema"
_CONFIG_REGISTERED = False


def register_configs() -> None:
    global _CONFIG_REGISTERED
    if _CONFIG_REGISTERED:
        return

    cs = ConfigStore.instance()
    cs.store(name=_CONFIG_SCHEMA_NAME, node=AppConfig)
    _CONFIG_REGISTERED = True
