import pytest
from hydra import compose, initialize_config_module
from omegaconf import DictConfig

from mailgateway_mcp.config import SmtpConfig, register_configs


def _compose_config(overrides: list[str] | None = None) -> DictConfig:
    register_configs()
    with initialize_config_module(version_base=None, config_module="mailgateway_mcp.conf"):
        return compose(config_name="config", overrides=overrides or [])


def test_compose_config_returns_hydra_config() -> None:
    cfg = _compose_config()

    assert isinstance(cfg, DictConfig)
    assert cfg.server.name == "mailgateway-mcp"
    assert cfg.server.transport == "streamable-http"
    assert cfg.server.host == "127.0.0.1"
    assert cfg.server.port == 8000
    assert cfg.server.path == "/mcp"
    assert cfg.smtp.host == "localhost"
    assert cfg.smtp.port == 587
    assert cfg.smtp.from_email == "agent@example.com"
    assert cfg.smtp.verify_peer is True
    assert cfg.hello.greeting == "Hello"
    assert cfg.hello.default_name == "world"


def test_compose_config_applies_overrides() -> None:
    cfg = _compose_config(
        [
            "server.transport=stdio",
            "server.port=9000",
            "smtp.host=smtp.example.com",
            "smtp.port=2525",
            "smtp.verify_peer=false",
            "hello.greeting=Hi",
            "hello.default_name=team",
        ]
    )

    assert cfg.server.transport == "stdio"
    assert cfg.server.port == 9000
    assert cfg.smtp.host == "smtp.example.com"
    assert cfg.smtp.port == 2525
    assert cfg.smtp.verify_peer is False
    assert cfg.hello.greeting == "Hi"
    assert cfg.hello.default_name == "team"


def test_hydra_config_preserves_lazy_interpolations() -> None:
    app_config = _compose_config(["hello.default_name=${server.name}"])

    assert app_config.server.name == "mailgateway-mcp"
    assert app_config.hello.default_name == "mailgateway-mcp"


def test_smtp_config_rejects_mutually_exclusive_tls_modes() -> None:
    with pytest.raises(ValueError, match="both use_ssl and starttls"):
        SmtpConfig(use_ssl=True, starttls=True)


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("user", ""),
        ("", "secret"),
    ],
)
def test_smtp_config_requires_username_and_password_together(
    username: str,
    password: str,
) -> None:
    with pytest.raises(ValueError, match="username and password together"):
        SmtpConfig(username=username, password=password)
