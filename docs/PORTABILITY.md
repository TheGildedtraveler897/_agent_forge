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

The export produces:

- an unpacked suitcase directory
- a `.tar.gz` archive
- a `.zip` archive
- a `MANIFEST.json` describing what was included

Deploy on a target machine with:

```bash
./_agent_forge/scripts/deploy-factory.sh
```

The deploy flow installs `_agent_forge`, shared doctrine docs, and user-level Claude/Codex delivery targets.

Validated on 2026-04-05 with an isolated smoke test using:

- export root: `/tmp/agent-forge-export`
- target Projects root: `/tmp/agent-forge-suitcase-smoke/Projects`
- isolated Claude home: `/tmp/agent-forge-suitcase-smoke/.claude`
- isolated Codex home: `/tmp/agent-forge-suitcase-smoke/.codex`

The tested flow:

1. build suitcase snapshot
2. deploy into isolated temp roots
3. confirm root doctrine docs copied
4. confirm Claude agents/commands and Codex skills synced
5. re-run deploy with `--replace-factory`

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
- sync/bootstrap/export/deploy scripts
- portable handoff and operator docs

## Never Carry

- project repositories unless explicitly approved
- `.env` files or credentials
- runtime data, caches, or machine-local settings
- generated archives from other machines as a substitute for the canonical repo
