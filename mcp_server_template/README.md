# MCP Server Stub

This directory is a small bootstrap stub for a new Hydra + FastMCP server.

It is not a generic framework and not a real templating system. The intended use is:

1. Copy this directory to a new project directory.
2. Rename the package and project metadata.
3. Replace the `hello` smoke-test tool with the first real tool.
4. Keep the same split between app logic, MCP wiring, config, and tests.

What is included:

- `src/mcp_server/`
  - `app.py`: pure application logic
  - `main.py`: FastMCP server wiring
  - `config.py`: structured Hydra config
  - `conf/config.yaml`: runtime defaults
- `tests/unit/`
  - app behavior test
  - config composition test
  - MCP wiring test
- `docs/`
  - lightweight design placeholders if you want to keep docs with the server

## Bootstrap Workflow

Copy the directory:

```bash
cp -r mcp_server_template <new_server_dir>
cd <new_server_dir>
```

Rename these first:

- package directory: `src/mcp_server/` -> `src/<your_package>/`
- package imports from `mcp_server` -> `<your_package>`
- script entry in `pyproject.toml`
- project name in `pyproject.toml`

Edit these next:

- [`pyproject.toml`](/home/omry/dev/agent-tools/mcp_server_template/pyproject.toml)
  - `project.name`
  - `project.description`
  - `[project.scripts]`
  - package-data key if the package name changes
- [`src/mcp_server/config.py`](/home/omry/dev/agent-tools/mcp_server_template/src/mcp_server/config.py)
  - `ServerConfig.name`
  - config sections if the new server needs different settings
- [`src/mcp_server/conf/config.yaml`](/home/omry/dev/agent-tools/mcp_server_template/src/mcp_server/conf/config.yaml)
  - `server.name`
  - transport defaults if needed
- [`src/mcp_server/app.py`](/home/omry/dev/agent-tools/mcp_server_template/src/mcp_server/app.py)
  - replace `hello` with the first real domain behavior
- [`src/mcp_server/main.py`](/home/omry/dev/agent-tools/mcp_server_template/src/mcp_server/main.py)
  - replace the `hello` tool registration with the real tool set
- [`tests/unit/`](/home/omry/dev/agent-tools/mcp_server_template/tests/unit)
  - rename imports
  - update the smoke-test expectations

## Verify The Copy

Install and run tests:

```bash
python -m pip install -e . --no-build-isolation
pytest
```

Run the server:

```bash
mcp-server
```

`mcp-server` is only a placeholder command name in this stub. Rename the package, script entry in `pyproject.toml`, and `server.name` before using this as a real server.

Default local test mode is HTTP:

- transport: `streamable-http`
- URL: `http://127.0.0.1:8000/mcp`

You can point MCP Inspector at that URL and call the `hello` tool as a quick connectivity check.

## Editing Guidance

Keep these boundaries:

- app logic in `app.py`
- FastMCP registration in `main.py`
- structured config in `config.py`
- environment defaults in `conf/config.yaml`
- behavior checks in `tests/`

That keeps the next server easy to grow without mixing domain logic into the MCP transport layer.
