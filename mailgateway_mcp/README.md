# MailGateway MCP Server

This directory contains the design and future implementation of a mail gateway MCP server.

## Development

Run the test suite from the repo root with:

- `python -m nox -s mailgateway_mcp`
- `python -m nox -s lint`

Or run the project-local noxfile from inside `mailgateway_mcp` with:

- `python -m nox -s tests`
- `python -m nox -s lint`

The `lint` session runs both `black --check` and the MailGateway `mypy` passes.

The design is documented in the `docs/` structure used by the MCP server template:

- [docs/overview.md](docs/overview.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/openclaw-integration/README.md](docs/openclaw-integration/README.md)
- [docs/openclaw-integration/wrapper-skill-decision.md](docs/openclaw-integration/wrapper-skill-decision.md)
- [docs/openclaw-integration/send-email-skills.md](docs/openclaw-integration/send-email-skills.md)
- [openclaw_skills/README.md](openclaw_skills/README.md)
- [docs/config.md](docs/config.md)
- [docs/policies.md](docs/policies.md)
- [docs/errors.md](docs/errors.md)
- [docs/todo.md](docs/todo.md)
- [docs/testing_backlog.md](docs/testing_backlog.md)
- [docs/tools/list_accounts.md](docs/tools/list_accounts.md)
- [docs/tools/send_email.md](docs/tools/send_email.md)
- [docs/tools/imap_extension.md](docs/tools/imap_extension.md)
