# Factory Suitcase Runbook

Use this runbook when you want to move the current Agent Forge factory state to another machine or a Debian VM without carrying project repos or secrets.

## Purpose

The suitcase is a portable snapshot of the factory layer only:

- `_agent_forge/` canonical source
- shared root doctrine docs needed under `~/Projects`
- bootstrap, sync, export, deploy, and workstation-setup scripts

It is designed for:

- fresh machine setup
- VM portability tests
- controlled refreshes of another workstation's factory layer

It is not designed for:

- auto-updating remote machines
- carrying governed project repos by default
- carrying `.env` files, credentials, caches, or runtime data

## Build The Suitcase

From the canonical development machine:

```bash
cd ~/Projects/_agent_forge
./scripts/factory-export.sh
```

Output:

- `exports/<bundle-name>/`
- `exports/<bundle-name>.tar.gz`
- `exports/<bundle-name>.zip`

Each bundle includes a `MANIFEST.json` and a `README.md`.

## Deploy The Suitcase

After unpacking the bundle on a target machine:

```bash
cd <bundle-root>
./_agent_forge/scripts/deploy-factory.sh
```

Default target locations:

- `~/Projects/_agent_forge`
- `~/.claude`
- `~/.codex`

Useful overrides:

```bash
./_agent_forge/scripts/deploy-factory.sh \
  --projects-root /tmp/vm-test/Projects \
  --claude-home /tmp/vm-test/.claude \
  --codex-home /tmp/vm-test/.codex
```

Use `--replace-factory` if the target already has an `_agent_forge` snapshot and you intentionally want to refresh it from the new suitcase.

## Prepare The Workstation

After deploy, the machine still is not ready for actual LLM development until the hosted CLI tools are installed and authenticated.

Run:

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
```

That script handles:

- base development dependencies
- Claude Code installation
- Codex installation
- Gemini CLI installation
- guided authentication notes and a durable machine setup log

## Current Validation Status

Validated on 2026-04-05 with an isolated temp-root smoke test:

- export root: `/tmp/agent-forge-export`
- target root: `/tmp/agent-forge-suitcase-smoke/Projects`
- redeploy test: passed with `--replace-factory`

Observed isolated delivery counts in the smoke test:

- Claude agents: 8
- Claude commands: 7
- Codex skills: 12

These counts reflect the portable global factory layer only. Project-local skills are synced later when a governed project is bootstrapped and the project-specific sync commands are run.

## Debian VM Validation Flow

1. Export the suitcase on the canonical machine.
2. Copy the archive into the Debian VM.
3. Unpack it.
4. Run `./_agent_forge/scripts/deploy-factory.sh`.
5. Run `~/Projects/_agent_forge/scripts/bootstrap-workstation.sh`.
6. Verify:
   - `~/Projects/_agent_forge` exists
   - `~/.claude/agents` and `~/.claude/commands` are populated
   - `~/.codex/skills` is populated
   - root doctrine docs exist under `~/Projects`
   - selected hosted CLIs are installed and authenticated
7. Bootstrap the next proof project:

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
./scripts/bootstrap-project.sh --name reddit-archive
./scripts/sync-claude-adapters.sh --project reddit-archive
./scripts/sync-codex-skills.sh --project reddit-archive
```

## Reddit Archive Pilot

The next portability proof project should be a governed repo for:

- Reddit saved post export
- image/media download where accessible
- structured metadata sidecars
- restartable archival runs

Recommended artifact chain:

1. Evidence pack on Reddit API/auth/media constraints
2. Implementation brief for the downloader/exporter
3. Assessment scorecard after the first working slice
4. Handoff for the next VM session

## Refresh Rule

This machine stays canonical. When the factory improves:

1. rebuild the suitcase
2. redeploy the new snapshot elsewhere
3. do not patch remote suitcase copies by hand unless emergency conditions require it
