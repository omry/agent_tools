# TODO

## Purpose

Track agreed follow-up work that is not specific to tests.

Protocol:

- keep this file focused on open follow-up work
- remove completed items instead of marking them `done`
- capture durable findings in the relevant docs or code comments, not here

## Items

- Refine account access policy beyond the current broad `read_only` flag
  - Why: the current `account_access_profiles` examples (`bot`, `personal`) are too coarse for future SMTP and IMAP capabilities
  - Status: `todo`
  - Steps:
    1. Split policy by capability so SMTP and IMAP permissions can be controlled independently.
    2. Define the minimum policy surface needed for planned IMAP features instead of overloading `read_only`.
    3. Update config docs and examples once the finer-grained policy model is decided.

- Add optional bot-signing behavior for personal-account sends
  - Why: when sending through a personal account, the operator may want the body to disclose that the bot drafted or sent the message
  - Status: `todo`
  - Steps:
    1. Add account-level or skill-level config to control whether bot-signing is enabled for personal-account sends.
    2. Define how the signature text is injected for text and HTML bodies.
    3. Update interactive skill behavior and docs once the policy is decided.

- Add startup logging for MailGateway version and non-sensitive config summary
  - Why: operators need a quick sanity check that the expected build and account layout are running without exposing secrets
  - Status: `todo`
  - Steps:
    1. Log the MailGateway package/server version at startup.
    2. Log a basic non-sensitive config summary such as transport, bind address, account names, enabled protocols, and sensitivity tiers.
    3. Ensure no secrets, credentials, or raw env values are emitted in those startup logs.

- Improve the OpenClaw skill installer with file-change visibility
  - Why: operators should be able to see exactly which skill files are being added or updated during installation
  - Status: `todo`
  - Steps:
    1. Detect which installed files would change copying them into the container (dry mode) or during in real installation.
    2. Print a concise diff or change summary during installation.
    3. Keep the output readable without dumping large file contents by default.
