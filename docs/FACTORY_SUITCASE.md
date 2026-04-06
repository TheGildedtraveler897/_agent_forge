# Factory Suitcase Runbook

Use this runbook when you want to move the current Agent Forge factory state to another machine or a Debian VM without carrying project repos or secrets.

For a step-by-step walkthrough of Debian VM setup, see `docs/VM_OPERATOR_RUNBOOK.md`.

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

You will be asked to choose an export mode:

| Mode | When to use |
|------|-------------|
| `clean` | Moving factory to a new machine or company. Session history replaced with stubs. |
| `backup` | Personal backup of your live factory. All session history preserved. |

Pass `--mode clean` or `--mode backup` to skip the prompt.

Output:

- `exports/<bundle-name>/`
- `exports/<bundle-name>.tar.gz`
- `exports/<bundle-name>.zip`

Each bundle includes a `MANIFEST.json` (which records the export mode) and a `README.md`.

## Deploy The Suitcase

### Recommended: one-shot wrapper

After unpacking, run the one-shot wrapper. It deploys the factory and then asks whether to install the hosted CLIs:

```bash
cd <bundle-root>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

You will be asked whether to run workstation bootstrap. Nothing is installed without your confirmation.

### Manual two-step path

If you need more control:

```bash
# Step 1: deploy factory only (no packages installed)
cd <bundle-root>
./_agent_forge/scripts/deploy-factory.sh

# Step 2: install CLIs and authenticate
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
```

Useful overrides for both scripts:

```bash
./_agent_forge/scripts/deploy-and-bootstrap.sh \
  --projects-root /tmp/vm-test/Projects \
  --claude-home /tmp/vm-test/.claude \
  --codex-home /tmp/vm-test/.codex
```

Use `--replace-factory` if the target already has an `_agent_forge` snapshot and you intentionally want to refresh it.

## Current Validation Status

Validated on 2026-04-05 with an isolated temp-root smoke test:

- export root: `/tmp/agent-forge-export`
- target root: `/tmp/agent-forge-suitcase-smoke/Projects`
- redeploy test: passed with `--replace-factory`

Observed isolated delivery counts in the smoke test:

- Claude agents: 8
- Claude commands: 7
- Codex skills: 12

These counts reflect the portable global factory layer only. Project-local skills are synced automatically when a governed project is bootstrapped.

## Bootstrap A New Project After Deploy

After authentication is complete:

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
```

The script automatically syncs Claude adapters and Codex skills, then offers an interactive project-definition flow. No separate sync commands needed.

## Debian VM Validation Flow

See `docs/VM_OPERATOR_RUNBOOK.md` for the full step-by-step Debian VM guide.

Quick reference:

1. Build suitcase on canonical machine: `./scripts/factory-export.sh`
2. Copy archive into the VM and unpack it.
3. Run: `./_agent_forge/scripts/deploy-and-bootstrap.sh`
4. Complete authentication for selected CLIs.
5. Bootstrap a project: `./scripts/bootstrap-project.sh --name <your-project>`
6. Verify: `python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py`

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
