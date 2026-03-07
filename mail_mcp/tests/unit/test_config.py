from hydra import compose, initialize_config_module
from omegaconf import DictConfig

from mail_mcp.config import register_configs


def _compose_config(overrides: list[str] | None = None) -> DictConfig:
    register_configs()
    with initialize_config_module(version_base=None, config_module="mail_mcp.conf"):
        return compose(config_name="config", overrides=overrides or [])


def test_compose_config_returns_hydra_config() -> None:
    cfg = _compose_config()

    assert isinstance(cfg, DictConfig)
    assert cfg.server.name == "mail-mcp"
    assert cfg.server.transport == "streamable-http"
    assert cfg.server.host == "127.0.0.1"
    assert cfg.server.port == 8000
    assert cfg.server.path == "/mcp"
    assert cfg.hello.greeting == "Hello"
    assert cfg.hello.default_name == "world"


def test_compose_config_applies_overrides() -> None:
    cfg = _compose_config(
        [
            "server.transport=stdio",
            "server.port=9000",
            "hello.greeting=Hi",
            "hello.default_name=team",
        ]
    )

    assert cfg.server.transport == "stdio"
    assert cfg.server.port == 9000
    assert cfg.hello.greeting == "Hi"
    assert cfg.hello.default_name == "team"


def test_hydra_config_preserves_lazy_interpolations() -> None:
    app_config = _compose_config(["hello.default_name=${server.name}"])

    assert app_config.server.name == "mail-mcp"
    assert app_config.hello.default_name == "mail-mcp"
