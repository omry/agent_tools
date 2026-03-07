from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfigLike


@dataclass(frozen=True)
class HelloResult:
    tool: str
    message: str


class MailMcpApp:
    """Minimal application surface before wiring a concrete MCP SDK."""

    def __init__(self, config: AppConfigLike) -> None:
        self._config = config

    def tool_names(self) -> list[str]:
        return ["hello"]

    def hello(self, name: str | None = None) -> HelloResult:
        target = name or self._config.hello.default_name
        return HelloResult(
            tool="hello",
            message=f"{self._config.hello.greeting}, {target}!",
        )
