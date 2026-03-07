# Source Layout

Use this directory for the MCP server implementation.

The bootstrap stub now lives under `src/mcp_server/`.

Suggested next steps when starting a new server:

- rename `mcp_server` to the real package name
- update `ServerConfig.name`
- replace the `hello` smoke-test tool with the first real tool
- keep `main.py` as the thin FastMCP wiring layer

Suggested subdirectories as the server grows:

- `config/`
- `tools/`
- `services/`
- `transports/`
- `policies/`

Keep MCP tool handlers thin and move shared behavior into services and policies.
