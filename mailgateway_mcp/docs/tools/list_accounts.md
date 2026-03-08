# Tool: list_accounts

## Status

- Stage: `v1`
- Owner: `MailGateway MCP server`

## Purpose

Return the configured accounts available to the caller, along with lightweight metadata needed to choose an account for later SMTP or IMAP operations.

## Intended usage

Use this when the caller needs to discover which accounts exist before selecting one explicitly for `send_email` or future IMAP tools.

## Input shape

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

## Output shape

```json
{
  "accounts": [
    {
      "name": "primary",
      "description": "Bot-owned account for automated email tasks",
      "account_access_profile": "bot",
      "sensitivity_tier": "standard",
      "smtp_enabled": true,
      "imap_enabled": true,
      "imap_read_only": false
    }
  ]
}
```

If `imap_enabled` is `false`, omit `imap_read_only`.

## Operation details

`list_accounts` is a discovery operation.

Expected behavior:

1. Read the configured account map.
2. Construct the defined response shape from the configured accounts.
3. Return stable account names and human-readable descriptions.
4. Return the configured sensitivity tier for each account.
   Current tiers are `standard` and `sensitive`.
5. Indicate which protocols are enabled for each account.
6. If `imap_enabled` is `true`, indicate whether IMAP access is read-only under the account's configured `account_access_profile`.
7. If `imap_enabled` is `false`, omit `imap_read_only`.

## Policy checks

- Return all configured accounts under the current trusted-caller model.
- Do not expose credentials, transport configuration, recipient-policy configuration, audit configuration, or other sensitive internal settings.
- Do expose the configured sensitivity tier because interactive callers use it to decide confirmation behavior.

## Audit behavior

- Emit normal debug logs for tool invocation and result handling.
- No special durable audit requirement is defined for account discovery in the current design.

## Errors

- `CONFIGURATION_ERROR` when configured accounts cannot be loaded or normalized correctly
- `INTERNAL_ERROR` for unexpected failures

## Out of scope

- Caller authentication and filtering results by caller identity
- Exposing raw transport settings or secrets

## Test checklist

- returns all configured accounts
- returns the configured sensitivity tier for each account
- omits `imap_read_only` when IMAP is not enabled on an account
- reflects the configured `account_access_profile`
- does not expose transport, recipient policy, or audit configuration
