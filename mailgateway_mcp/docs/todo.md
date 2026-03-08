# TODO

## Purpose

Track agreed follow-up work that is not specific to tests.

## Items

- Tie `list_accounts` to real account-aware sending
  - Why: discovery exists, but it is not yet connected to the actual `send_email` selection path
  - Status: `todo`
  - Steps:
    1. Add end-to-end tests that use a discovered account name directly in `send_email`.
    2. Update docs so `list_accounts` is described as the discovery source for valid send-account names.

- Pass the selected account through the OpenClaw skill/runtime layer
  - Why: the current skill runtime only has optional account labels for reporting and does not control the actual MailGateway sending account
  - Status: `todo`
  - Steps:
    1. Decide per skill whether account selection is deployment-fixed or discovered from `list_accounts`.
    2. Pass the real selected account value into the MailGateway MCP `send_email` call.
    3. Remove or demote any account-label-only behavior once real account routing is wired through.
