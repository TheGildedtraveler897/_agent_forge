# Factory Suitcase Runbook

Use this runbook to move the current Agent Forge factory state to another machine without carrying project repos or secrets.

## Purpose

The suitcase is a portable snapshot of the factory layer only:

- `_agent_forge/` canonical source
- shared root doctrine docs needed under `~/Projects`
- sync, bootstrap, export, deploy, and validation scripts

It is for:

- fresh machine setup
- VM portability tests
- controlled refreshes of another workstation’s factory layer

It is not for:

- remote auto-update systems
- carrying governed project repos by default
- carrying `.env`, credentials, caches, or runtime logs

## Build The Suitcase

From the canonical machine:

```bash
cd ~/Projects/_agent_forge
./scripts/factory-export.sh
```

Modes:

- `clean`: portable factory capability only; session residue replaced with clean stubs
- `backup`: preserve current state for personal backup

Outputs:

- `exports/<bundle-name>/`
- `exports/<bundle-name>.tar.gz`
- `exports/<bundle-name>.zip`

Each bundle includes `MANIFEST.json` and `README.md`.

## Deploy The Suitcase

Recommended:

```bash
cd <bundle-root>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

This deploys the factory, syncs global Claude/Codex/Gemini surfaces, then offers workstation bootstrap.

Manual two-step path:

```bash
cd <bundle-root>
./_agent_forge/scripts/deploy-factory.sh
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
```

## Current Validation Status

The suitcase path is structurally wired for the omni-factory model:

- export excludes runtime residue
- deploy refreshes shared root docs plus global host surfaces
- post-deploy bootstrap creates project-local Claude, Codex, and Gemini surfaces

What still needs real-world proof:

- fresh Debian VM operator run
- fresh macOS operator run
- first shared MCP server carried through export, deploy, and live runtime validation

## Bootstrap After Deploy

After authentication:

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
```

The bootstrap auto-syncs project-local host surfaces. No extra manual sync loop should be required for the normal path.

## Refresh Rule

This machine stays canonical. When the factory improves:

1. rebuild the suitcase
2. redeploy the fresh snapshot elsewhere
3. do not patch remote suitcase copies by hand unless that machine becomes canonical
