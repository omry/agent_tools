---
name: send-email-predefined
description: Use for unattended or preapproved MailGateway sends driven by deployment-owned templates or profiles. Resolve a configured template, validate allowed parameters, and submit without a final confirmation step.
---

# Send Email Predefined

Use this skill for unattended or preapproved email sends.

Required environment:

- `MAILGATEWAY_MCP_URL`
- `MAILGATEWAY_ACCOUNT`
- `MAILGATEWAY_PREDEFINED_TEMPLATES`
- optional `MAILGATEWAY_MCP_BEARER_TOKEN`
- optional `MAILGATEWAY_TIMEOUT_SECONDS`

Use the helper script at `scripts/send_email_predefined.py`.

Workflow:

1. Accept only a configured template/profile name and its allowed parameters.
2. Load the template registry from `MAILGATEWAY_PREDEFINED_TEMPLATES`.
3. Resolve the deployment-owned `MAILGATEWAY_ACCOUNT` and use it as the `send_email.account` value.
4. Reject the request if it tries to introduce arbitrary recipients, arbitrary bodies, or unsupported parameters.
5. Resolve the final `send_email` payload from the configured template/profile.
6. Submit immediately without a final confirmation step.
7. Report the normalized result returned by the helper.

Do not:

- degrade into freeform composition
- ask for a final confirmation step
- expose SMTP transport details
- expose credentials

If the user wants the template registry shape, read `references/template-config.md`.

If the user wants the broader design context, read:

- `../../docs/openclaw-integration/send-email-skills.md`
- `../../docs/tools/send_email.md`
