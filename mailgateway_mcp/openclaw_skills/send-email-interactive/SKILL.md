---
name: send-email-interactive
description: Use when a user is actively composing or sending an email through MailGateway. Gather recipients, subject, and body, apply the interactive confirmation rule, and submit through the local MailGateway MCP helper script.
---

# Send Email Interactive

Use this skill when the user is present and wants help composing or sending an email.

Required environment:

- `MAILGATEWAY_MCP_URL`
- optional `MAILGATEWAY_MCP_BEARER_TOKEN`
- optional `MAILGATEWAY_TIMEOUT_SECONDS`
- optional `MAILGATEWAY_ACCOUNT_LABEL` for reporting only

Use the helper script at `scripts/send_email_interactive.py`.

Workflow:

1. Gather `to`, `subject`, and at least one of `text_body` or `html_body`.
2. Prefer plain text unless the user explicitly wants HTML formatting.
3. Apply conditional confirmation:
   - confirm before sending if recipients or message content were materially inferred, expanded, or transformed
   - confirmation is not required only for straightforward user-directed sends with explicit recipients and explicit message content
4. Run the helper script with explicit arguments.
5. Report the normalized result returned by the helper.

Do not:

- expose SMTP transport details
- expose credentials
- imply delivery beyond SMTP submission acceptance
- use this skill for unattended or templated sends; use `send-email-predefined` instead

If the user wants the broader design context, read:

- `../../docs/openclaw-integration/send-email-skills.md`
- `../../docs/tools/send_email.md`
