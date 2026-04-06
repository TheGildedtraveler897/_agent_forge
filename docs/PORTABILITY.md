# Portable Skill Notes

## Canonical Model

- The repo copy under `_agent_forge` is the only maintained source of truth.
- Tool-native directories are adapters or mirrors.
- Global skills should avoid repo-specific paths, commands, and names unless they are genuinely part of the skill's domain.

## Current Tooling

- Codex native skills live under `~/.codex/skills/`
- Claude native specialization uses:
  - `~/.claude/agents/` and `.claude/agents/` for subagents
  - `~/.claude/commands/` and `.claude/commands/` for custom slash commands

## Suitcase Snapshot Model

- This machine remains the canonical factory development lab.
- Portable deployments are snapshot exports, not live replicas.
- When the factory improves here, rebuild the suitcase export and redeploy it elsewhere.
- Never treat a remote suitcase copy as the canonical source of truth.

Use:

```bash
./scripts/factory-export.sh
```

You are asked to choose an export mode:

- **`clean`** — factory capability only; session history replaced with stubs. Use for new machines / new companies.
- **`backup`** — preserves current-state notes and session history. Use for personal backups.

Pass `--mode clean` or `--mode backup` to skip the interactive prompt.

The export produces:

- an unpacked suitcase directory
- a `.tar.gz` archive
- a `.zip` archive
- a `MANIFEST.json` describing what was included (including `export_mode`)

Deploy on a target machine with the one-shot wrapper:

```bash
cd <unpacked-bundle>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

This wrapper runs `deploy-factory.sh` (no packages) and then asks whether to run `bootstrap-workstation.sh` (installs CLIs). Nothing is installed silently.

Portable deployment has two layers:

1. **Factory deploy** — copy `_agent_forge`, doctrine docs, and tool-native delivery surfaces
2. **Workstation bootstrap** — install the hosted coding CLIs and walk the operator through authentication

The wrapper chains them with a prompt between steps. See `docs/VM_OPERATOR_RUNBOOK.md` for the full Debian VM walkthrough.

Validated on 2026-04-05 (suitcase + deploy) and 2026-04-06 (clean/backup export modes + deploy-and-bootstrap wrapper + bootstrap-project auto-sync) with isolated smoke tests.

Smoke-test coverage:
- `factory-export.sh --mode clean` — HANDOFF/TECH_DEBT replaced with stubs; runtime/ excluded; skills preserved
- `factory-export.sh --mode backup` — current state preserved intact
- `deploy-and-bootstrap.sh --no-bootstrap` — deploy succeeds, bootstrap skipped cleanly
- `bootstrap-project.sh --no-define` — scaffold created, Claude adapter sync succeeds, Codex global sync succeeds

## Migration Rule

When a project-local skill becomes reusable:

1. Copy it into `skills/global/`
2. Remove repo-specific assumptions
3. Tighten the description so it triggers only on the right requests
4. Sync it to any tool-native locations that need it

## Auto-Improvement Rule

Future auto-research or auto-improvement workflows should patch the canonical skill files here, never the copies under tool-home directories.

## Hybrid Claude Model

Use Claude adapters with this split:

- subagents for expert-role skills
- slash commands for utility or procedural workflows

The canonical adapter sources live under `_agent_forge/claude/` and are synced into tool-native locations as symlinks.

## Governance Defaults

Projects governed by Agent Forge should carry a minimum portable contract set:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/CONOPS.md`
- `docs/HANDOFF.md`
- `.claude/CLAUDE.md`

Additional `.claude/agents/` and `.claude/commands/` entries are only required when the project actually has local Claude-native adapters.

## Safe To Carry

- `_agent_forge/` canonical source
- shared root doctrine docs
- team manifests
- sync/bootstrap/export/deploy/workstation scripts
- portable handoff and operator docs

## Never Carry

- project repositories unless explicitly approved
- `.env` files or credentials
- runtime data, caches, or machine-local settings
- generated archives from other machines as a substitute for the canonical repo
