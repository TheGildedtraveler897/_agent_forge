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
