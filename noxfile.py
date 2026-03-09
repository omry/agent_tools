from __future__ import annotations

import nox


nox.options.sessions = ["mailgateway_mcp"]


@nox.session
def mailgateway_mcp(session: nox.Session) -> None:
    session.install("nox>=2024.10,<2026.0")
    session.run(
        "python",
        "-m",
        "nox",
        "-f",
        "mailgateway_mcp/noxfile.py",
        "-s",
        "tests",
        *session.posargs,
    )
