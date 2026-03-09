from __future__ import annotations

from pathlib import Path

import nox


nox.options.sessions = ["mailgateway_mcp", "lint"]

REPO_ROOT = Path(__file__).parent


def install_nox(session: nox.Session) -> None:
    session.install("nox>=2024.10,<2026.0")


def run_subproject_nox(
    session: nox.Session,
    *,
    noxfile: str,
    session_name: str,
) -> None:
    install_nox(session)
    session.run("nox", "-f", noxfile, "-s", session_name, *session.posargs)


@nox.session
def mailgateway_mcp(session: nox.Session) -> None:
    run_subproject_nox(
        session,
        noxfile=str(REPO_ROOT / "mailgateway_mcp/noxfile.py"),
        session_name="tests",
    )


@nox.session
def lint(session: nox.Session) -> None:
    run_subproject_nox(
        session,
        noxfile=str(REPO_ROOT / "mailgateway_mcp/noxfile.py"),
        session_name="lint",
    )
