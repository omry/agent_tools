# Source Layout

Use this directory for the mail MCP server implementation.

Suggested subdirectories:

- `config/`
- `tools/`
- `services/`
- `transports/`
- `policies/`

Keep MCP tool handlers thin and move shared behavior into services, transports, and policies.
