# Temporary OpenClaw Send Email Skill Design

## Purpose

Define the temporary OpenClaw skill surfaces that will call MailGateway MCP through the MailGateway-specific MCP-over-HTTP shim.

This document describes only the OpenClaw-facing skill behavior. It does not change the underlying MailGateway MCP contracts.

## Skill split

The temporary design uses two separate skills:

- `send_email_interactive`
- `send_email_predefined`

These skills stay separate because they have different safety rules, different allowed inputs, and different user expectations.

## Shared design rules

Both skills should:

- talk to MailGateway MCP through the temporary skill-local MCP-over-HTTP shim
- resolve the MailGateway account from deployment-owned skill configuration
- call `send_email` for the actual submission
- return a normalized short result to OpenClaw rather than raw MCP transport details
- stay MailGateway-specific instead of trying to behave like a generic MCP client
- be structured so future MailGateway IMAP tools can be added to the same shim

Both skills must not:

- expose SMTP transport settings
- expose credentials
- let callers override `From` or `Reply-To`
- present delivery as guaranteed beyond SMTP submission acceptance

## Skill: `send_email_interactive`

### Intended use

Use this skill when a user is actively collaborating with OpenClaw and wants help composing or sending an email.

### Inputs

The skill may begin from freeform user intent such as:

- "send an email to Alice about tomorrow's meeting"
- "draft and send a reply to the vendor"
- "email the team that the deploy is complete"

### Behavior

The skill should:

1. Extract or ask for the required MailGateway fields:
   - `to`
   - `subject`
   - at least one of `text_body` or `html_body`
2. Resolve the `account` from deployment-owned skill configuration rather than asking the user to choose from MailGateway accounts.
   In the current helper implementation, this is the deployment-owned `MAILGATEWAY_ACCOUNT` setting.
3. Prefer plain text body generation unless the user explicitly wants HTML formatting.
4. Pass the body to the helper through stdin rather than multiline shell arguments.
   The interactive skill should use exactly one of the helper's stdin body flags:
   - `--text-stdin`
   - `--html-stdin`
   Keep CLI body flags only as a manual testing fallback.
5. Ask for confirmation before submission when:
   - the message body was materially inferred or expanded by the model
   - recipients were inferred rather than directly provided
   - the action looks higher risk than a straightforward user-directed send
6. Call `send_email` only after the interactive skill's conditional confirmation rule is satisfied.

### Confirmation policy

The temporary rule is conditional confirmation, not unconditional confirmation.

The skill may submit without an extra confirmation only when all of these are true:

- the user directly requested sending, not just drafting
- recipients are explicit
- subject and body are explicit or minimally edited
- there is no sign that the send is unusually risky or ambiguous

Otherwise, the skill should stop and ask for explicit final confirmation before calling `send_email`.

### Output to OpenClaw

On success, return a short result containing:

- selected account
- recipient summary
- subject
- MailGateway message id when available

On failure, return:

- the normalized MailGateway error code when available
- a short human-readable failure summary
- whether retry looks reasonable when that can be inferred from the MailGateway result

## Skill: `send_email_predefined`

### Intended use

Use this skill for unattended or preapproved sends where the message shape, recipients, or both are constrained by deployment-owned configuration.

Examples:

- recurring status notifications
- alert messages
- templated operational emails

### Inputs

This skill should accept only a narrow predefined invocation shape, such as:

- template or profile name
- required template parameters
- no arbitrary account selection; account resolution is deployment-owned unless a tightly constrained override is explicitly configured

It must not accept arbitrary freeform recipients or arbitrary freeform message bodies.

### Behavior

The skill should:

1. Resolve the requested template or profile from deployment-owned skill configuration.
2. Resolve the MailGateway account from deployment-owned skill configuration for that template/profile.
   In the current helper implementation, this is the deployment-owned `MAILGATEWAY_ACCOUNT` setting.
3. Validate that the requested parameters match the allowed template inputs.
4. Resolve the final MailGateway payload from that template/profile.
5. Call `send_email` directly without a final confirmation step.

### Safety policy

This skill is the only temporary send path that may operate unattended.

That is only acceptable because:

- recipients are preapproved
- the body shape is preapproved
- the account is fixed or tightly constrained

If a request falls outside those constraints, this skill should reject it instead of degrading into interactive freeform composition.

This skill does not use a final confirmation step. Once the predefined template/profile and its allowed parameters validate successfully, it may call `send_email` immediately.

### Output to OpenClaw

On success, return a short result containing:

- template or profile used
- selected account
- recipient summary
- MailGateway message id when available

On failure, return:

- the normalized MailGateway error code when available
- a short summary of whether the failure came from template validation, configuration resolution, or MailGateway submission

## Shim responsibilities

The temporary MCP-over-HTTP shim should support the minimum MailGateway flow needed by these skills:

1. initialize the MailGateway MCP session or request flow as required by the server
2. call `send_email`
3. normalize tool responses into a shape the skills can consume without embedding protocol details into prompts

The shim should be designed around MailGateway tool invocation rather than SMTP-specific shortcuts so that planned IMAP tools can later reuse the same internal structure.

## Migration note

The skill-local MCP-over-HTTP shim is temporary.

When OpenClaw supports native MCP:

- retire the skill-local MCP-over-HTTP shim
- have these skill modes call MailGateway MCP directly

The two skill modes do not necessarily need to disappear. They may still remain useful as thinner OpenClaw wrappers if the deployment still wants explicit separation between interactive and unattended sending behavior.
