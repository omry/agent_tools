# OpenClaw Skill Installation

These files package the temporary OpenClaw wrapper skills for MailGateway:

- `send-email-interactive`
- `send-email-predefined`
- the shared helper under `_shared`

They are meant to be installed into the running `openclaw` container as user-managed skills under `/home/node/.openclaw/skills`.

Built-in OpenClaw skills live separately under `/app/skills`. The MailGateway installer does not modify `/app/skills`.

## Recommended flow

### First installation

1. Set the MailGateway endpoint in the host env file used by the `openclaw` container.

   For the current VM setup, the recommended value is:

   ```bash
   MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp
   ```

   Set the deployment-owned MailGateway account there as well:

   ```bash
   MAILGATEWAY_ACCOUNT=primary
   ```

   That works for the current deployment because the `openclaw` container is using host networking.

   This value depends on Docker networking:

   - if `openclaw` is using host networking, `127.0.0.1` is usually correct
   - if `openclaw` is on a bridge network, it may need the host gateway address or another reachable host/interface address instead

   In the current container layout, the env file is typically:

   ```bash
   ~/.openclaw/.env
   ```

2. Recreate the `openclaw` container so it picks up the updated `--env-file` values.

3. Run the installer script from GitHub:

```bash
curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/main/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --source github
```

4. Smoke-test the interactive skill:

```bash
printf 'Hello Omry\n\nThis is a MailGateway stdin test.\n\nBest,\nAtlas\n' | docker exec -i \
  -e MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp \
  -e MAILGATEWAY_ACCOUNT=primary \
  openclaw \
  python3 /home/node/.openclaw/skills/send-email-interactive/scripts/send_email_interactive.py \
  --to you@example.com \
  --subject "MailGateway skill test" \
  --text-stdin
```

### Updating without losing the installed skills

The host path `~/.openclaw` is mounted into the container at `/home/node/.openclaw`.

That means:

- skill files under `~/.openclaw/skills` persist across container recreation
- editing `~/.openclaw/.env` on the host updates the mounted env file content

Update flow:

1. edit the host env file:

```bash
nano ~/.openclaw/.env
```

2. recreate the `openclaw` container so it picks up the updated `--env-file` values

3. rerun the MailGateway installer

The installed skill files stay on the mounted host path, but Python dependencies like `httpx` and `mcp` are installed into the container filesystem and do not survive container recreation.

## Installer details

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
REF=<git-ref>; curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- uninstall
```

This removes only the MailGateway skill files from `/home/node/.openclaw/skills`. It does not remove `python3-pip`, `httpx`, or `mcp`.

### Automatic install overrides

Use a different container:

```bash
REF=<git-ref>; curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --ref "${REF}" --source github --container my-openclaw
```

Use a different skill directory inside the container:

```bash
REF=<git-ref>; curl -fsSL "https://raw.githubusercontent.com/omry/agent_tools/${REF}/mailgateway_mcp/openclaw_skills/install-openclaw-skills.sh" | bash -s -- install --ref "${REF}" --source github --skill-dir /home/node/.openclaw/skills
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

### 6. Smoke-test the interactive skill

```bash
printf 'Hello Omry\n\nThis is a MailGateway stdin test.\n\nBest,\nAtlas\n' | docker exec -i \
  -e MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp \
  -e MAILGATEWAY_ACCOUNT=primary \
  openclaw \
  python3 /home/node/.openclaw/skills/send-email-interactive/scripts/send_email_interactive.py \
  --to you@example.com \
  --subject "MailGateway skill test" \
  --text-stdin
```

### 7. Manual testing notes

For OpenClaw automation, always pass the body through stdin and declare the body type explicitly with exactly one of:

- `--text-stdin`
- `--html-stdin`

The `--text-body` and `--html-body` flags are kept only for manual ad hoc testing.

HTML body via stdin:

```bash
printf '<p>Hello Omry</p><p>This is an HTML stdin test.</p><p>Best,<br>Atlas</p>\n' | docker exec -i \
  -e MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp \
  -e MAILGATEWAY_ACCOUNT=primary \
  openclaw \
  python3 /home/node/.openclaw/skills/send-email-interactive/scripts/send_email_interactive.py \
  --to you@example.com \
  --subject "MailGateway HTML stdin test" \
  --html-stdin
```

Regression example showing why arg-passed multiline content is bad:

```bash
docker exec \
  -e MAILGATEWAY_MCP_URL=http://127.0.0.1:8025/mcp \
  -e MAILGATEWAY_ACCOUNT=primary \
  openclaw \
  python3 /home/node/.openclaw/skills/send-email-interactive/scripts/send_email_interactive.py \
  --to you@example.com \
  --subject "arg newline regression test" \
  --text-body 'Hello Omry\n\nThis will keep literal backslash-n sequences.\n\nBest,\nAtlas'
```

## Current target environment

This installer path assumes the current OpenClaw container environment that was validated during development:

- container name: `openclaw`
- Debian-based image with `apt-get`
- `python3` present
- `pip` may be absent and needs to be bootstrapped
- user home: `/home/node`
- user-managed skill directory: `/home/node/.openclaw/skills`
