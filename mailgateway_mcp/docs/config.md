# Configuration

## Purpose

Define the deployment-owned configuration contract for the MailGateway MCP server.

## Configuration system

The implementation language is Python so the server can use OmegaConf directly for hierarchical configuration and environment-variable interpolation.

Examples below use OmegaConf interpolation. Secrets may be sourced from environment variables via `oc.env`.

## Illustrative config shape

```yaml
mail:
  accounts:
    primary:
      description: Bot-owned account for automated email tasks.
      sensitivity_tier: standard
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
    personal:
      description: Personal account with stricter access policy.
      sensitivity_tier: sensitive
      account_access_profile: personal
      imap:
        host: imap.example.com
        port: 993
        username: personal@example.com
        password: ${oc.env: PERSONAL_IMAP_PASSWORD}
        tls: implicit
        verify_peer: true
        default_folder: INBOX
        folders:
          INBOX:
            description: Personal inbox.
          Archive:
            description: Personal archive folder.
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
    personal:
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

## Relevant settings

- `mail.accounts`: required mapping of configured accounts
- `mail.accounts.<account>.description`: required human-readable account purpose
- `mail.accounts.<account>.sensitivity_tier`: optional enum used by interactive callers to decide whether the selected account needs stricter confirmation; current values are `standard` and `sensitive`, default `standard`
- `mail.accounts.<account>.account_access_profile`: required reference to a profile under `mail.account_access_profiles`
- `mail.account_access_profiles`: required mapping of account access profile definitions
- `mail.account_access_profiles.bot.read_only`: required
- `mail.account_access_profiles.personal.read_only`: required
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

- `mail.accounts.<account>.imap.host`: required
- `mail.accounts.<account>.imap.port`: required
- `mail.accounts.<account>.imap.username`: optional
- `mail.accounts.<account>.imap.password`: optional secret
- `mail.accounts.<account>.imap.tls`: required enum
- `mail.accounts.<account>.imap.verify_peer`: required when TLS is enabled
- `mail.accounts.<account>.imap.default_folder`: optional folder name used when a tool does not specify one
- `mail.accounts.<account>.imap.folders`: required mapping keyed by folder name
- `mail.accounts.<account>.imap.folders.<folder>.description`: optional human-readable folder purpose

## Validation rules

- Each configured account may define `smtp`, `imap`, or both.
- Any account used for SMTP operations must define `smtp`.
- Any account used for IMAP operations must define `imap`.
- If `mail.accounts.<account>.smtp.authenticate` is `true`, both `mail.accounts.<account>.smtp.username` and `mail.accounts.<account>.smtp.password` must be set.
- If `mail.accounts.<account>.smtp.authenticate` is `false`, both `mail.accounts.<account>.smtp.username` and `mail.accounts.<account>.smtp.password` must be unset.
- If `mail.accounts.<account>.smtp.tls` is configured, failure to establish the configured TLS mode must fail closed.
- The `From` identity is server-owned and not caller-controlled in v1.
- `Reply-To` is omitted or set to the same sender identity in v1.
- `mail.accounts.<account>.sensitivity_tier` must be a supported enum value.
- `mail.accounts.<account>.account_access_profile` must match a key under `mail.account_access_profiles`.
- If `mail.accounts.<account>.imap.default_folder` is set, it must match a key under `mail.accounts.<account>.imap.folders`.

## Secret handling

- Secrets should not be committed to source control.
- SMTP and IMAP passwords may be sourced through OmegaConf environment interpolation such as `${oc.env: SMTP_PASSWORD}`.
- Prefer secret references such as `${oc.env: SMTP_PASSWORD}` over raw secret values in checked-in configs, but hard-coded values remain supported.

## Configuration evolution notes

- The initial config shape already includes both SMTP and IMAP, even though IMAP implementation is deferred to stage 2.
- Account-level policy and audit are defined through `account_access_profile`.
- Account sensitivity is defined per account rather than per access profile because interactive sender-choice and confirmation behavior depend on the specific account being used.
- Folder-specific policy and audit overrides are intentionally out of scope for the default shape.
