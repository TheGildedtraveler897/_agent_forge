# Debian VM Operator Runbook

Use this doc when setting up Agent Forge on a fresh Debian or Ubuntu VM and you want the current omni-factory flow, not the retired Claude-first model.

## What You Need Before You Start

- a Debian or Ubuntu VM with internet access and `sudo`
- an Agent Forge suitcase archive
- this doc available in another window

## Step 1 - Copy The Archive Into The VM

Preferred transfer:

```bash
scp agent-forge-suitcase-<timestamp>.tar.gz youruser@vm-ip:~/
```

## Step 2 - Unpack The Archive

```bash
cd ~
tar -xzf agent-forge-suitcase-<timestamp>.tar.gz
```

If you used zip:

```bash
unzip agent-forge-suitcase-<timestamp>.zip
```

## Step 3 - Run The One-Shot Setup Wrapper

```bash
cd ~/agent-forge-suitcase-<timestamp>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

This does two things:

1. deploys `_agent_forge` into `~/Projects`
2. syncs global Claude, Codex, and Gemini surfaces before asking whether to run workstation bootstrap

Nothing installs silently.

## Step 4 - Authenticate The CLIs

After installation, complete auth for the CLIs you selected:

- Claude Code: `claude`
- Codex: `codex --login`
- Gemini CLI: `gemini`

Common Debian VM pitfalls:

- if browser login fails, use the CLI’s documented fallback auth path
- if Gemini login hits org entitlement issues, try `unset GOOGLE_CLOUD_PROJECT`
- on TLS-inspected networks, set `NODE_USE_SYSTEM_CA=1`

## Step 5 - Verify The Machine

Check versions:

```bash
claude --version
codex --version
gemini --version
```

Check factory health:

```bash
python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py
```

Expected result: no `[FAIL]` lines.

## Step 6 - Bootstrap The First Governed Project

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
```

The bootstrap creates the minimum governed footprint and auto-syncs Claude, Codex, and Gemini project surfaces.

## Ready State Checklist

- [ ] `~/Projects/_agent_forge` exists
- [ ] `~/.claude/agents` and `~/.claude/commands` are populated
- [ ] `~/.agents/skills` is populated
- [ ] `~/.gemini/agents`, `~/.gemini/commands`, `~/.gemini/skills`, and `~/.gemini/GEMINI.md` exist
- [ ] selected CLIs respond to `--version`
- [ ] auth completed for each selected CLI
- [ ] `verify-agent-forge.py` reports 0 failures
- [ ] at least one governed project exists under `~/Projects`

## Refresh Rule

When the canonical machine improves the factory:

1. rebuild the suitcase on the canonical machine
2. copy the new archive into the VM
3. re-run `./deploy-and-bootstrap.sh --replace-factory --no-bootstrap`

Do not patch the VM snapshot by hand unless that VM becomes canonical.
