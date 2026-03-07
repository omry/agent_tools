# Configuration

## Purpose

Define the deployment-owned configuration contract for the server.

## Configuration system

State the intended config loader and interpolation model.

Example:

- implementation language: Python
- config library: OmegaConf
- secret interpolation: `${oc.env: SOME_SECRET}`

## Illustrative config shape

```yaml
<root_config_key>:
  example_setting: value
  nested_block:
    enabled: true
```

## Relevant settings

- `<root>.<setting>`: required or optional, purpose, and type
- `<root>.<nested>.<setting>`: required or optional, purpose, and type

## Validation rules

- Rule 1
- Rule 2
- Rule 3

## Secret handling

- Secrets should not be committed to source control.
- Describe how secrets are sourced at runtime.

## Configuration evolution notes

Describe how future versions may extend the config without breaking the initial shape.
