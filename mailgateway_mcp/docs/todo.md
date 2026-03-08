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
  - Why: interactive account choice now happens through runtime discovery while predefined sending stays deployment-fixed, and the remaining work is to tighten that split in the real OpenClaw UI/runtime
  - Status: `todo`
  - Steps:
    1. Verify in the real OpenClaw runtime that the interactive skill can discover accounts via `list_accounts` and send with an explicit selected account.
    2. Verify in the real OpenClaw runtime that predefined sending stays bound to its configured account through OpenClaw skill config.
    3. Manually verify in the real OpenClaw UI/runtime that the interactive skill respects sensitive-account confirmation behavior, since that path is not currently automated.

- Revalidate OpenClaw `SKILL.md` metadata format behavior
  - Why: current runtime behavior appears to accept richer multiline metadata, while the docs claim `metadata` should be a single-line JSON object
  - Status: `todo`
  - Steps:
    1. Re-test custom skill metadata parsing after the core OpenClaw MailGateway flow is working end to end.
    2. Confirm whether multiline YAML metadata is fully supported or only partially tolerated.
    3. Align the skill files with actual runtime behavior rather than the current documentation claim.

- Convert SMTP and IMAP TLS mode config values to enums
  - Why: `sensitivity_tier` now uses an OmegaConf-backed enum, while SMTP and IMAP TLS modes still use raw string sets
  - Status: `todo`
  - Steps:
    1. Replace `_SMTP_TLS_MODES` and `_IMAP_TLS_MODES` string sets with enum-backed config fields.
    2. Preserve lowercase operator-facing values if Hydra/OmegaConf allows it cleanly.
    3. Update validation, docs, and override tests to match the enum-backed TLS modes.

- Add mypy and a static type-checking test target
  - Why: direct Python construction in tests can drift from the typed config contract without runtime failures
  - Status: `todo`
  - Steps:
    1. Add `mypy` to the development toolchain.
    2. Introduce a static test target alongside the existing automated test suite.
    3. Fix existing type mismatches in tests and skill/runtime code as they are surfaced.

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
