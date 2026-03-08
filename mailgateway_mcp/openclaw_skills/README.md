# OpenClaw Skill Installation

These files package the temporary OpenClaw wrapper skills for MailGateway:

- `send-email-interactive`
- `send-email-predefined`
- the shared helper under `_shared`

They are meant to be installed into the running `openclaw` container as user-managed skills under `/home/node/.openclaw/skills`.

Built-in OpenClaw skills live separately under `/app/skills`. The MailGateway installer does not modify `/app/skills`.

## Recommended: automatic install

Use the installer script from GitHub and pin it to a tag or commit:

```bash
REF=<git-ref> curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --ref "${REF}" --source github
```

Defaults:

- target container: `openclaw`
- target skill directory: `/home/node/.openclaw/skills`

What the installer does:

1. verifies the target container exists and is running
2. creates `/home/node/.openclaw/skills` if needed
3. installs `python3-pip` in the container with `apt-get` if `pip` is missing
4. installs the required Python dependencies in the container:
   - `httpx`
   - `mcp`
5. downloads the MailGateway skill files from GitHub at the requested ref
6. installs `_shared`, `send-email-interactive`, and `send-email-predefined` into `/home/node/.openclaw/skills`

The installer is idempotent. Re-running it updates the skill files in place.

### Automatic source modes

The installer supports three source modes:

- `--source github`: always download the skill tree from GitHub at `--ref`
- `--source local`: install from the local `openclaw_skills` tree next to the installer script
- `--source auto`: prefer the local tree when present, otherwise fall back to GitHub

Default behavior is `--source auto`.

For the published `curl | bash` flow, use `--source github`.

For pre-push testing from a local checkout, use `--source local`.

### Automatic uninstall

```bash
REF=<git-ref> curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- uninstall
```

This removes only the MailGateway skill files from `/home/node/.openclaw/skills`. It does not remove `python3-pip`, `httpx`, or `mcp`.

### Automatic install overrides

Use a different container:

```bash
REF=<git-ref> curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --ref "${REF}" --source github --container my-openclaw
```

Use a different skill directory inside the container:

```bash
REF=<git-ref> curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --ref "${REF}" --source github --skill-dir /home/node/.openclaw/skills
```

### Local checkout install

When testing from a local checkout before pushing to GitHub, run the installer script directly and force local source mode:

```bash
bash /path/to/agent_tools/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh install --source local
```

## Manual install

Use manual install if you do not want to pipe a remote script into `bash`.

### 1. Copy the skill tree to the VM host

From a checkout of this repo:

```bash
scp -r /path/to/agent_tools/mailgateway_mcp/openclaw_skills openclaw:~/openclaw-skill-staging/
```

### 2. Bootstrap `pip` inside the container if needed

```bash
docker exec openclaw python3 -m pip --version || \
  docker exec -u 0 openclaw sh -lc 'apt-get update && apt-get install -y python3-pip'
```

### 3. Install the Python dependencies used by the skills

```bash
docker exec -u 0 openclaw python3 -m pip install --break-system-packages httpx mcp
```

### 4. Copy the skill files into OpenClaw's shared skill directory

```bash
docker exec -u node openclaw sh -lc 'mkdir -p /home/node/.openclaw/skills'

tar -C ~/openclaw-skill-staging/openclaw_skills -cf - _shared send-email-interactive send-email-predefined \
  | docker exec -i -u node openclaw sh -lc 'tar -xf - -C /home/node/.openclaw/skills'
```

### 5. Verify the installed files

```bash
docker exec openclaw sh -lc 'find /home/node/.openclaw/skills -maxdepth 3 -name SKILL.md -o -name mailgateway_mcp_client.py'
```

### 6. Configure the MailGateway endpoint

The skills require `MAILGATEWAY_MCP_URL` in the `openclaw` container environment.

For the current VM setup, the recommended value is:

```bash
MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp
```

That works for the current deployment because the `openclaw` container is using host networking.

This value depends on Docker networking:

- if `openclaw` is using host networking, `127.0.0.1` is usually correct
- if `openclaw` is on a bridge network, it may need the host gateway address or another reachable host/interface address instead

Add it to the environment source used by the `openclaw` container. In the current container layout, the env file is typically:

```bash
/home/node/.openclaw/.env
```

### 7. Smoke-test the interactive skill

```bash
docker exec -e MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp openclaw \
  python3 /home/node/.openclaw/skills/send-email-interactive/scripts/send_email_interactive.py \
  --to you@example.com \
  --subject "MailGateway skill test" \
  --text-body "Testing the interactive MailGateway skill."
```

## Current target environment

This installer path assumes the current OpenClaw container environment that was validated during development:

- container name: `openclaw`
- Debian-based image with `apt-get`
- `python3` present
- `pip` may be absent and needs to be bootstrapped
- user home: `/home/node`
- user-managed skill directory: `/home/node/.openclaw/skills`
