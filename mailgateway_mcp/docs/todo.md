# TODO

## Purpose

Track agreed follow-up work that is not specific to tests.

## Items

- Update Python package metadata in `pyproject.toml`
  - Why: published package metadata is currently incomplete
  - Status: `todo`
  - Needed fields: author, author email, and other standard package metadata as appropriate

- Add real multi-account send support
  - Why: config and `list_accounts` already expose multiple accounts, but `send_email` still resolves a default SMTP account server-side instead of accepting an explicit account selection
  - Status: `todo`
  - Needed work: make `send_email` accept `account`, resolve the requested SMTP-enabled account on the server, and pass the selected account from the OpenClaw skills/runtime instead of relying on the current default-account fallback
