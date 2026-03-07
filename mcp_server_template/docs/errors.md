# Error Model

## Purpose

Define the stable error contract shared by all tools.

## Error response shape

```json
{
  "ok": false,
  "error_code": "EXAMPLE_ERROR",
  "message": "Human-readable explanation",
  "retryable": false
}
```

## Recommended error-code categories

- `INVALID_INPUT`
- `POLICY_DENIED`
- `CONFIGURATION_ERROR`
- `AUTHENTICATION_FAILED`
- `CONNECTION_FAILED`
- `INTERNAL_ERROR`

Add server-specific codes here.

## Error-code definitions

### `INVALID_INPUT`

Describe when this should be returned.

### `POLICY_DENIED`

Describe when this should be returned.

### `CONFIGURATION_ERROR`

Describe when this should be returned.

## Retry semantics

Describe:

- which failures are retryable
- which failures are permanent
- any idempotency or replay semantics
