# RFC: Mail MCP Server Design

- Document ID: `mail-mcp-design`
- Version: `0.1.0`
- Status: `Draft`
- Authors: `Codex`, `Omry Yadan`
- Last Updated: `2026-03-07`
- Intended Use: implementation-driving design document for the initial server build and future revisions

## Purpose

Define a Model Context Protocol (MCP) server that gives an agent controlled access to email capabilities.

The first version focuses on outbound SMTP mail submission. Future versions may add IMAP-based inbox access for reading and manipulating messages.

The initial deployment target is a bot operating on its own private email account. The design should keep a path open for a later deployment against a personal account with stricter guardrails.

## Goals

- Expose email capabilities through a narrow MCP surface
- Start with reliable SMTP message submission
- Support multiple configured email accounts
- Keep transport configuration and credentials outside tool inputs
- Make it easy to add IMAP read and folder actions later
- Preserve strong safety boundaries for credentials, recipients, account scope, and access policy

## Non-goals for v1

- Full mail client behavior
- Bulk email or campaign workflows
- Attachment handling
- Inbox search, read, delete, or move operations
- Per-call transport parameter overrides such as host, port, TLS mode, credentials, or sender identity

## Core design principles

### 1. Capability-first interface

The MCP server should expose message-level, account-level, and folder-level operations such as `send_email`, `list_messages`, and `get_message`, while keeping SMTP and IMAP session management internal.

### 2. Deployment-owned configuration

SMTP and future IMAP settings belong to server configuration, not tool payloads. The caller should not choose hosts, ports, TLS modes, or credentials.

### 3. Future personal inbox guardrails

The initial target is a private account used by the bot itself, but future access to a personal inbox needs stricter guardrails.

Questions to resolve before supporting a personal inbox:

- whether sending should be restricted to approved recipients or known correspondents
- whether first-contact messages should require a separate approval step
- whether inbox access should start as read-only before any write or delete operations are allowed
- what audit trail is required for message access, message sending, and destructive folder actions

### 4. Small, explicit surface area

Add capabilities incrementally. v1 should expose a minimal tool set: account discovery plus a single mail submission tool. IMAP is designed in this document, but its implementation belongs to a second stage rather than a partial v1 rollout.

### 5. Auditable behavior

Every tool call should produce structured logs and normalized results so that automated actions can be inspected later.

## Terminology

- `account`: the credential and identity boundary used for SMTP submission and IMAP access
- `folder`: an IMAP folder within an account, such as `INBOX` or `Alerts`
- `account_access_profile`: a policy profile applied at the account level; the initial profile types are `bot` and `owner`

This document uses these terms deliberately:

- SMTP is tied to an `account`
- IMAP is tied to an `account`
- IMAP operations target a `folder`
- sensitive behavior is controlled by the account's configured `account_access_profile`
- multiple configured accounts may coexist in one server deployment

## High-level architecture

The server should be split into four layers:

1. `mcp interface`
   - Defines tools and schemas
   - Converts tool calls into application requests

2. `mail service layer`
   - Applies policy validation
   - Builds RFC 5322/MIME messages
   - Normalizes responses and errors

3. `transport adapters`
   - `smtp adapter` for outbound submission
   - Future `imap adapter` for inbound account and folder operations

4. `configuration and secrets`
   - Loads deployment settings
   - Resolves credentials from environment variables or secret references

## Recommended repository shape

```text
mail_mcp/
  mail_mcp_server_design.md
  README.md
  src/
    server.*
    config.*
    tools/
      list_accounts.*
      send_email.*
    services/
      mail_service.*
    transports/
      smtp_transport.*
      imap_transport.*   # added later
    policies/
      recipient_policy.*
      access_policy.*
```

The implementation language is Python so the server can use OmegaConf directly for hierarchical configuration and environment-variable interpolation.

## v1 capability: Account Discovery

### Tool name

`list_accounts`

### Description

Return the configured accounts available to the caller, along with lightweight metadata needed to choose an account for later SMTP or IMAP operations.

### Intended usage

Use this when the caller needs to discover which accounts exist before selecting one explicitly for `send_email` or future IMAP tools.

### Input shape

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

### Output shape

```json
{
  "accounts": [
    {
      "name": "primary",
      "description": "Bot-owned account for automated email tasks",
      "account_access_profile": "bot",
      "smtp_enabled": true,
      "imap_enabled": true,
      "imap_read_only": false
    }
  ]
}
```

### Operation details

`list_accounts` is a discovery operation. It should not expose credentials, transport configuration, recipient-policy configuration, audit configuration, or other sensitive internal settings.

In the current design, `list_accounts` returns all configured accounts. The caller is assumed to be trusted once connected to the MCP server, and caller authentication is out of scope for now.

Expected behavior:

1. Read the configured account map
2. Construct the defined response shape from the configured accounts
3. Return stable account names and human-readable descriptions
4. Indicate which protocols are enabled for each account
5. If `imap_enabled` is `true`, indicate whether IMAP access is read-only under the account's configured `account_access_profile`
6. If `imap_enabled` is `false`, omit `imap_read_only`

## v1 capability: SMTP send

### Tool name

`send_email`

### Description

Send a single email through the deployment-configured SMTP submission path.

### Intended usage

Use this when the agent has enough information to send a complete message to one or more recipients and sending mail is allowed by local policy.

### Input shape

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["account", "to", "subject"],
  "properties": {
    "account": {
      "type": "string",
      "minLength": 1,
      "description": "Configured account name returned by list_accounts"
    },
    "idempotency_key": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "Optional caller-supplied key used to suppress duplicate sends on retries"
    },
    "to": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "format": "email" }
    },
    "cc": {
      "type": "array",
      "items": { "type": "string", "format": "email" }
    },
    "bcc": {
      "type": "array",
      "items": { "type": "string", "format": "email" }
    },
    "in_reply_to": {
      "type": "string",
      "description": "Optional Message-ID for reply threading"
    },
    "references": {
      "type": "array",
      "items": { "type": "string" }
    },
    "subject": {
      "type": "string",
      "minLength": 1,
      "maxLength": 998
    },
    "text_body": {
      "type": "string"
    },
    "html_body": {
      "type": "string"
    }
  },
  "anyOf": [
    { "required": ["text_body"] },
    { "required": ["html_body"] }
  ]
}
```

This keeps the mail composition contract narrow and predictable for MCP clients.

### Output shape

Success:

```json
{
  "ok": true,
  "message_id": "<generated-message-id@example.com>",
  "idempotency_replayed": false
}
```

Failure:

```json
{
  "ok": false,
  "error_code": "SUBMISSION_REJECTED",
  "message": "The SMTP submission failed",
  "retryable": false,
  "idempotency_replayed": false
}
```

Optional submission diagnostics may be included when available, but they should be treated as transport-level acceptance details rather than end-to-end delivery confirmation.

If recipient-level diagnostics are returned, they are best-effort transport details. They are primarily useful when the SMTP server is close to the final destination and may be absent or low-value when sending through an intermediate relay.

### Operation details

`send_email` is a one-shot message submission operation. It does not create drafts, manage conversation state, or confirm final delivery to a recipient inbox.

Expected behavior:

1. Validate the input payload
2. Resolve the selected configured account
3. Apply recipient and policy checks
4. Resolve the deployment-owned sender identity for that account
5. Build an RFC 5322 message with plain text and optional HTML parts
6. Add reply-threading headers when provided
7. Submit the message through the configured SMTP path
8. Return a normalized success or failure result

Header and envelope rules:

- `to` and `cc` appear in message headers and SMTP recipient handling
- `bcc` participates in SMTP recipient handling only and must not appear in the final serialized message headers
- the caller may not provide a `Reply-To` override in v1
- the caller must select a configured account explicitly

Idempotency rules:

- the caller may provide `idempotency_key` to suppress duplicate sends during retries
- if the same `idempotency_key` is received again with the same effective payload, the server should return the earlier normalized result instead of sending again and should set `idempotency_replayed` to `true`
- the server may compare effective payloads using a stored cryptographic hash such as SHA-256 instead of retaining the full message content in memory
- if the same `idempotency_key` is reused with a different effective payload, the server should fail with `IDEMPOTENCY_CONFLICT`
- replay applies to prior success and prior failure results alike
- a caller that wants to force a fresh submission attempt after a stored result must use a new `idempotency_key`
- once the configured idempotency record expires, the same `idempotency_key` should be treated as new work
- if no `idempotency_key` is provided, the operation has at-least-once semantics under retry

Notably out of scope for `send_email`:

- delivery tracking after SMTP acceptance
- inbox inspection to discover recipients or thread context
- template rendering
- attachments
- bulk fan-out behavior across many recipients

## Deployment configuration

Configuration is deployment-owned and should be expressed hierarchically so SMTP and IMAP settings remain clearly separated.

Examples below use OmegaConf interpolation. Secrets may be sourced from environment variables via `oc.env`.

Illustrative YAML shape:

```yaml
mail:
  accounts:
    primary:
      description: Bot-owned account for automated email tasks.
      account_access_profile: bot
      smtp:
        host: smtp.example.com
        port: 587
        authenticate: true
        username: bot@example.com
        password: ${oc.env: SMTP_PASSWORD}
        tls: starttls
        verify_peer: true
        from:
          email: bot@example.com
          name: Bot
        limits:
          max_messages_per_minute: 30
          max_recipients_per_message: 20
        idempotency:
          expiration_days: 7
        recipient_policy:
          allowed_domains:
            - example.com
          blocked_domains: []
      imap:
        host: imap.example.com
        port: 993
        username: bot@example.com
        password: ${oc.env: IMAP_PASSWORD}
        tls: implicit
        verify_peer: true
        default_folder: INBOX
        folders:
          INBOX:
            description: Primary inbox folder.
          Alerts:
            description: Operational notifications.
    owner:
      description: Owner account with stricter access policy.
      account_access_profile: owner
      imap:
        host: imap.example.com
        port: 993
        username: owner@example.com
        password: ${oc.env: OWNER_IMAP_PASSWORD}
        tls: implicit
        verify_peer: true
        default_folder: INBOX
        folders:
          INBOX:
            description: Owner inbox.
          Archive:
            description: Owner archive folder.
  account_access_profiles:
    bot:
      read_only: false
      smtp_audit:
        enabled: true
        retention_days: 365
        store_message_metadata: true
        store_message_body: false
      imap_audit:
        enabled: true
        retention_days: 365
        store_message_metadata: true
        store_message_body: false
        audit_read_access: false
        audit_search_queries: false
        audit_message_state_changes: true
        audit_message_moves: true
        audit_message_deletes: true
    owner:
      read_only: true
      smtp_audit:
        enabled: true
        retention_days: 365
        store_message_metadata: true
        store_message_body: false
      imap_audit:
        enabled: true
        retention_days: 365
        store_message_metadata: true
        store_message_body: false
        audit_read_access: true
        audit_search_queries: true
        audit_message_state_changes: true
        audit_message_moves: true
        audit_message_deletes: true
```

Relevant top-level settings:

- `mail.accounts`: required mapping of configured accounts
- `mail.accounts.<account>.description`: required human-readable account purpose
- `mail.account_access_profiles`: required mapping of account access profile definitions
- `mail.account_access_profiles.bot.read_only`: required
- `mail.account_access_profiles.owner.read_only`: required
- `mail.account_access_profiles.<profile>.smtp_audit`: required SMTP audit config for that profile
- `mail.account_access_profiles.<profile>.imap_audit`: required IMAP audit config for that profile

Relevant SMTP settings for an account with SMTP enabled:
- `mail.accounts.<account>.smtp.host`: required
- `mail.accounts.<account>.smtp.port`: required
- `mail.accounts.<account>.smtp.authenticate`: required
- `mail.accounts.<account>.smtp.username`: optional
- `mail.accounts.<account>.smtp.password`: optional secret
- `mail.accounts.<account>.smtp.tls`: required enum: `none`, `starttls`, `implicit`
- `mail.accounts.<account>.smtp.verify_peer`: required when TLS is enabled
- `mail.accounts.<account>.smtp.from.email`: required
- `mail.accounts.<account>.smtp.from.name`: optional
- `mail.accounts.<account>.smtp.limits.max_messages_per_minute`: optional outbound rate limit
- `mail.accounts.<account>.smtp.limits.max_recipients_per_message`: optional safety limit
- `mail.accounts.<account>.smtp.idempotency.expiration_days`: optional retention for idempotency records, default `7`
- `mail.accounts.<account>.smtp.recipient_policy.allowed_domains`: optional allowlist
- `mail.accounts.<account>.smtp.recipient_policy.blocked_domains`: optional denylist

Relevant IMAP settings for an account with IMAP enabled:

- `mail.accounts.<account>.imap.host`: required when IMAP is enabled
- `mail.accounts.<account>.imap.port`: required when IMAP is enabled
- `mail.accounts.<account>.imap.username`: optional
- `mail.accounts.<account>.imap.password`: optional secret
- `mail.accounts.<account>.imap.tls`: required enum when IMAP is enabled
- `mail.accounts.<account>.imap.verify_peer`: required when TLS is enabled
- `mail.accounts.<account>.imap.default_folder`: optional folder name used when a tool does not specify one
- `mail.accounts.<account>.imap.folders`: required mapping keyed by folder name
- `mail.accounts.<account>.imap.folders.<folder>.description`: optional human-readable folder purpose

Relevant account-level policy settings:

- `mail.accounts.<account>.account_access_profile`: required reference to a profile under `mail.account_access_profiles`

Rules:

- Each configured account may define `smtp`, `imap`, or both.
- Any account used for SMTP operations must define `smtp`.
- Any account used for IMAP operations must define `imap`.
- If `mail.accounts.<account>.smtp.authenticate` is `true`, both `mail.accounts.<account>.smtp.username` and `mail.accounts.<account>.smtp.password` must be set.
- If `mail.accounts.<account>.smtp.authenticate` is `false`, both `mail.accounts.<account>.smtp.username` and `mail.accounts.<account>.smtp.password` must be unset.
- If `mail.accounts.<account>.smtp.tls` is configured, failure to establish the configured TLS mode must fail closed.
- The `From` identity should be server-owned and not caller-controlled in v1.
- `Reply-To` should be omitted or set to the same sender identity in v1.
- `mail.accounts.<account>.account_access_profile` must match a key under `mail.account_access_profiles`.
- If `mail.accounts.<account>.imap.default_folder` is set, it must match a key under `mail.accounts.<account>.imap.folders`.

## Policy model

The design should assume future policy tightening, especially before connecting this to a personal inbox.

### Baseline v1 policies

- The caller may choose recipients, subject, and body.
- The caller must choose a configured account explicitly for `send_email`.
- The caller may not override SMTP transport settings.
- The caller may not override the `From` address.
- The caller may not override `Reply-To` in v1.
- The server should validate recipient counts and address syntax.
- The server should enforce configured outbound send rate limits before attempting SMTP submission.
- The server should maintain operational debug logs separately from the durable audit log.
- The server should log attempts and results with sensitive fields redacted where appropriate.

### Future considerations for personal inbox access

- Require explicit allowlists for recipient domains or exact addresses
- Optionally require human approval for first-contact recipients
- Restrict sending to known correspondents
- Maintain a separate audit trail with message metadata
- Disable destructive IMAP operations by default

## Error model

The server should normalize transport and validation failures into stable application error codes.

Recommended initial codes:

- `INVALID_INPUT`
- `POLICY_DENIED`
- `CONFIGURATION_ERROR`
- `AUTHENTICATION_FAILED`
- `TLS_NEGOTIATION_FAILED`
- `CONNECTION_FAILED`
- `RATE_LIMITED`
- `IDEMPOTENCY_CONFLICT`
- `SUBMISSION_REJECTED`
- `SUBMISSION_STATUS_UNKNOWN`
- `INTERNAL_ERROR`

Each failure response should include:

- `ok: false`
- `error_code`
- human-readable `message`
- `retryable`

## Observability and Audit

The server should distinguish between operational debug logs and a durable audit log.

### Debug logs

Debug logs are for troubleshooting and operational visibility.

The server should emit structured debug logs for:

- tool invocation start
- validation failure
- SMTP connection attempt
- SMTP submission result
- unexpected exception

Recommended debug-log fields:

- timestamp
- tool name
- recipient counts
- recipient domains
- generated message id
- error code
- retryable

Debug logs should have shorter retention than the audit log and should not include message bodies or secrets by default.

### Durable audit log

The durable audit log is for accountability, later review, and sensitive-account governance.

The durable audit log should:

- be enabled by default
- retain records for `365` days by default
- store message metadata by default
- avoid storing message bodies by default
- record state-changing actions and policy-relevant decisions

Protocol-specific audit policy:

- audit behavior should be configured under `mail.account_access_profiles`
- the implementation should read SMTP audit settings directly from `mail.account_access_profiles.<profile>.smtp_audit`
- the implementation should read IMAP audit settings directly from `mail.account_access_profiles.<profile>.imap_audit`
- there is no per-account audit override in the current design
- IMAP state-changing operations such as flag changes, message moves, and deletes should generate durable audit records by default
- destructive IMAP operations such as delete should always produce durable audit records when the operation is enabled
- IMAP read access and search-query auditing may be configured separately because they can generate much higher event volume

Recommended audit fields:

- timestamp
- tool name
- account name when applicable
- folder name when applicable
- configured account access profile when applicable
- caller identity when available
- idempotency key when provided
- generated message id
- target recipient counts
- target recipient domains
- policy decision
- result status
- error code when applicable

For IMAP mutation operations, audit records should also include:

- target message identifier
- source folder when applicable
- destination folder when applicable
- previous and new state for flag changes when applicable

The implementation should treat the durable audit log as a distinct storage and retention concern rather than a long-retained copy of ordinary debug logs.

## Future IMAP extension

IMAP should be added only after the SMTP send flow is stable.

### Expected future capabilities

- `list_messages`
- `get_message`
- `search_messages`
- `move_message`
- `mark_message_read`
- `delete_message`

Each future IMAP tool must take `account` as a mandatory input. That input must reference an account with IMAP enabled. IMAP tools may take `folder` explicitly as well, or default to `mail.accounts.<account>.imap.default_folder` when omitted.

Initial IMAP scope assumptions:

- operations are scoped to a single selected account
- folder names are interpreted within that selected account only
- cross-account search and cross-account moves are out of scope for the initial IMAP release

### IMAP-specific design constraints

- Support write-capable IMAP operations from the first IMAP implementation
- Model accounts and folders explicitly
- Keep destructive actions opt-in and separately gated
- Preserve stable message identifiers where possible, but account for IMAP UID and folder scoping realities

### IMAP configuration notes

The IMAP config should be organized under an account. Within an account, tools should refer to configured folder names rather than raw user-provided folder strings.

Each account should define at least:

- zero or one SMTP config
- zero or one IMAP config
- a human-readable description
- one account-level `account_access_profile` reference

Each configured folder should define at least:

- a stable folder name via the map key
- an optional description

Access profiles should establish default policy:

- `bot`: defaults come from `mail.account_access_profiles.bot`
- `owner`: defaults come from `mail.account_access_profiles.owner`

The initial config shape should rely on account-level `account_access_profile` definitions. Folder-specific policy and audit overrides are intentionally out of scope for the default document shape.

When IMAP is added, the initial implementation may include both read and write operations. Write-capable behavior should still be controlled by access-profile policy and any future guardrails for sensitive accounts. Startup validation must also confirm that `mail.accounts.<account>.imap.default_folder`, when set, refers to a configured folder.

## Security considerations

- Store credentials outside source control
- Treat personal account access as a separate trust tier
- Fail closed on TLS validation errors
- Avoid exposing raw protocol errors that may leak secrets
- Enforce outbound rate limits to reduce abuse, loops, and accidental message storms
- Keep durable audit data metadata-only by default and make retention configurable
- Consider additional per-call safety checks before allowing broader usage

## Open design decisions

- Whether to expose MCP resources in addition to tools
- Whether message drafts should exist as a separate future tool
- Whether attachments belong in v2 or later
- What approval hook is required before supporting a personal inbox

## Recommended next step

After this design is accepted, create a minimal MCP server skeleton with these initial tools:

- `list_accounts`
- `send_email`

That first implementation should wire together:

- config loading
- account discovery from config
- schema validation
- MIME message assembly
- SMTP submission
- normalized error handling
