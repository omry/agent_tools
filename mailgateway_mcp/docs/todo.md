# TODO

## Purpose

Track agreed follow-up work that is not specific to tests.

## Items

- Add real multi-account send support
  - Why: config and `list_accounts` already expose multiple accounts, but `send_email` still resolves a default SMTP account server-side instead of accepting an explicit account selection
  - Status: `todo`
  - Steps:
    1. Make the `send_email` MCP tool accept an explicit `account` input.
    2. Resolve the requested SMTP-enabled account server-side instead of using the current `primary`/first-SMTP fallback.
    3. Reject unknown accounts and IMAP-only accounts with clear validation errors.
    4. Add tests proving that selecting different accounts changes the SMTP config used for submission.

- Tie `list_accounts` to real account-aware sending
  - Why: discovery exists, but it is not yet connected to the actual `send_email` selection path
  - Status: `todo`
  - Steps:
    1. Ensure the `list_accounts` names are the exact values accepted by `send_email.account`.
    2. Add end-to-end tests that use a discovered account name directly in `send_email`.
    3. Update docs so `list_accounts` is described as the discovery source for valid send-account names.

- Pass the selected account through the OpenClaw skill/runtime layer
  - Why: the current skill runtime only has optional account labels for reporting and does not control the actual MailGateway sending account
  - Status: `todo`
  - Steps:
    1. Decide per skill whether account selection is deployment-fixed or discovered from `list_accounts`.
    2. Pass the real selected account value into the MailGateway MCP `send_email` call.
    3. Remove or demote any account-label-only behavior once real account routing is wired through.
