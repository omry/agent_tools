# Architecture

## High-level architecture

Describe the major layers of the server and their responsibilities.

Suggested layers:

1. `mcp interface`
   - tool registration
   - schema validation
   - request and response translation
2. `service layer`
   - policy enforcement
   - normalized behavior
   - orchestration across components
3. `transport or backend adapters`
   - protocol-specific or provider-specific behavior
4. `configuration and secrets`
   - config loading
   - secret resolution

## Request lifecycle

1. MCP tool call received
2. Input validated
3. Config and policy resolved
4. Service operation executed
5. Result normalized
6. Logs emitted, and audit records when required
7. Response returned

## Repository shape

```text
src/
  server.py
  config/
  tools/
  services/
  transports/
  policies/
tests/
  unit/
  integration/
  spec/
```

## Implementation notes

- Keep MCP tool handlers thin.
- Keep backend or transport details out of tool handlers.
- Centralize policy evaluation and error normalization.
