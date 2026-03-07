# MCP Server Template

This directory is a reusable starting point for designing and implementing a new MCP server.

The structure separates:

- server-wide design
- configuration contract
- policy rules and optional audit rules
- normalized error model
- per-tool behavior
- architecture decisions

Recommended usage:

1. Copy this directory to a new server-specific directory.
2. Rename placeholder titles and identifiers.
3. Fill out `docs/overview.md` first.
4. Define the config contract in `docs/config.md`.
5. Define shared behavior in `docs/policies.md` and `docs/errors.md`.
6. Add one document per MCP tool under `docs/tools/`.
7. Record foundational decisions under `docs/adr/`.
8. Implement the shared server skeleton under `src/`.
9. Add tests under `tests/` that mirror the tool contracts.

Suggested directory layout:

```text
<server_name>/
  README.md
  docs/
    overview.md
    architecture.md
    config.md
    policies.md
    errors.md
    tools/
      tool_template.md
    adr/
      0000-decision-template.md
  src/
  tests/
```

Design process:

1. Define the server purpose, trust model, and rollout stages.
2. Lock the config shape and validation rules.
3. Define the initial tool set with one contract per tool.
4. Implement one shared server that exposes those tools.
5. Add tools incrementally by extending the same service.

Implementation rule:

Implement the server incrementally, using tool-level documents as the primary behavioral contract and the overview/config/policy documents as shared constraints.
