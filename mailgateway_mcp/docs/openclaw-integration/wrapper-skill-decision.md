# Decision: OpenClaw Wrapper Skills via a Temporary MCP-over-HTTP Shim

## Context

MailGateway MCP is intended to be used by an OpenClaw installation.

The current MailGateway design assumes a narrow MCP surface with a trusted internal caller. OpenClaw does not yet support MCP natively, so it cannot consume the server directly in the intended way.

Without an interim design, there are two weak alternatives:

- embed MailGateway-specific behavior directly into OpenClaw prompts or ad hoc workflow logic
- build a dummy non-MCP HTTP surface around MailGateway

Neither of those fits the current MailGateway design goals well. A dummy HTTP surface also gets weaker if MailGateway later needs more MCP features, and it would still be temporary and retired once OpenClaw gains native MCP support.

## Decision

Use OpenClaw wrapper skills that call MailGateway MCP directly over HTTP through a temporary MailGateway-specific MCP shim in the skill runtime.

Make the temporary OpenClaw integration split into two separate skill surfaces:

- an interactive send skill with dynamic account choice and conditional confirmation
- a predefined templated unattended send skill without confirmation and with a template-fixed account

Do not embed MailGateway-specific sending logic directly into OpenClaw prompts.

Implement only a narrow MailGateway-specific MCP subset needed for the current OpenClaw integration.

Design that shim around MailGateway tool invocation rather than SMTP-only special cases so future MailGateway IMAP tools can be added without a second integration redesign.

Do not build a generic MCP client.

Do not introduce a separate dummy business HTTP API.

Do not treat this shim as native OpenClaw MCP support.

For account handling:

- `send-email-interactive` should discover accounts through `list_accounts`, choose an explicit account at runtime, and use the returned `sensitivity_tier` to enforce stricter confirmation for sensitive accounts
- `send-email-predefined` should remain fixed-account and use the account attached to the selected template rather than dynamic runtime account choice

## Motivation

This decision keeps coupling to OpenClaw internals low. The OpenClaw-specific behavior is isolated in a temporary wrapper layer instead of leaking into the MailGateway server design.

This decision preserves MailGateway's intended narrow MCP surface. MailGateway remains designed around its real MCP contract instead of drifting into a throwaway business HTTP API.

This decision scales better than a dummy HTTP surface if MailGateway later needs additional MCP features, because the temporary integration continues to speak the real MailGateway protocol rather than a separate compatibility contract.

This decision still keeps the interim integration intentionally low-scope. The shim is narrow, MailGateway-specific, and temporary rather than a reusable MCP client investment.

This decision also leaves room for the planned MailGateway IMAP stage. The shim can remain MailGateway-specific while still being structured to add future IMAP tool calls instead of being tightly coupled to the initial SMTP send flow.

This decision provides a clean migration path. Once OpenClaw supports native MCP, OpenClaw can call MailGateway MCP directly and the temporary shim can be removed:

- the skill-side MCP shim

The two skill modes may still remain valuable after native MCP support exists, because interactive and unattended sending are still different OpenClaw behaviors even when the underlying transport no longer needs a compatibility shim.

This decision creates a clearer safety boundary between attended and unattended sending. Interactive sending and predefined unattended sending have different confirmation expectations and should not rely on a single ambiguous skill surface.

This decision also creates a clearer account-selection model. Interactive sending benefits from runtime account discovery and explicit sender choice, while predefined sending is safer when the sending account remains fixed by the selected template.

This decision also matches the current MailGateway trust model. The existing design assumes trusted internal callers, so the interim shim should remain an internal compatibility layer rather than a broadly exposed public API.

## Consequences

The interim OpenClaw path introduces two short-lived integration components:

- wrapper skills that present OpenClaw-friendly behavior
- a MailGateway-specific MCP-over-HTTP shim inside the skill runtime

This places temporary protocol logic in the OpenClaw integration layer instead of in a separate business API surface.

The shim is intentionally MailGateway-specific and is not reusable infrastructure for arbitrary MCP servers.

The shim therefore needs a small internal structure that can grow from the initial SMTP tools to future MailGateway IMAP tools without becoming a generic MCP framework.

Interactive and unattended sending will need separate operational and documentation treatment because they are intentionally separate skill surfaces.

Interactive sending now depends on `list_accounts` as a first-class discovery step rather than a deployment-fixed account binding.

Per-account sensitivity becomes part of the MailGateway contract because the interactive skill uses it to decide when stronger confirmation is required.

## Deferred future change

When OpenClaw gains native MCP support, replace the compatibility path with direct OpenClaw-to-MailGateway MCP integration.

At that point:

- retire the skill-side MCP shim
- simplify the OpenClaw skill implementations so they call native MCP directly
- keep the two skill modes as long as OpenClaw still benefits from explicitly separate interactive and unattended send behavior

Even after native MCP support exists, the wrapper skills are still expected to remain useful as the OpenClaw policy layer for:

- interactive vs unattended behavior
- dynamic vs fixed account selection
- confirmation rules, including sensitive-account handling

The long-term target is:

`OpenClaw skills -> MailGateway MCP`
