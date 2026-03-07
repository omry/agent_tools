# Tool: <tool_name>

## Status

- Stage: `v1` or later
- Owner: `<owner>`

## Purpose

Describe what this tool does for the caller.

## Intended usage

Describe when the caller should use this tool.

## Input shape

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [],
  "properties": {}
}
```

## Output shape

```json
{
  "ok": true
}
```

## Operation details

Describe the expected behavior step by step.

Recommended structure:

1. Validate inputs
2. Resolve config and policy
3. Execute the underlying operation
4. Normalize the result
5. Emit logs, and audit records if applicable

## Policy checks

- Check 1
- Check 2

## Audit behavior, if applicable

- What debug logs should be emitted
- What durable audit records should be written, if any

## Errors

- Relevant shared errors from `docs/errors.md`
- Tool-specific errors if needed

## Out of scope

- Explicitly excluded behavior 1
- Explicitly excluded behavior 2

## Test checklist

- valid request succeeds
- invalid request fails with the right error
- policy denial is enforced
- audit behavior is emitted as specified, if applicable
