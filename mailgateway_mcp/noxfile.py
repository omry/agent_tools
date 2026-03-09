from __future__ import annotations

import nox


nox.options.sessions = ["tests"]


def install_project(session: nox.Session) -> None:
    session.install("-e", ".[dev]")


@nox.session
def tests(session: nox.Session) -> None:
    install_project(session)
    session.run("pytest", *(session.posargs or ["tests"]))
