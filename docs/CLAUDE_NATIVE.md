# Claude Native Integration

Claude Code supports three native reusable specialization primitives:

- **subagents** in `~/.claude/agents/` or `.claude/agents/` — invoked via the Agent tool
- **slash commands** in `~/.claude/commands/` or `.claude/commands/` — invoked via the Skill tool as `/command-name`
- **skills** in `.claude/skills/*/SKILL.md` — invoked via the Skill tool, with rich metadata and full context

## Three-Layer Delivery Model

Each skill in `_agent_forge` can be delivered through up to three mechanisms:

| Layer | Source | Target | Purpose |
|---|---|---|---|
| Agent adapter | `claude/global/agents/*.md` | `~/.claude/agents/` | Thin prompt for Agent tool subagent invocation |
| Command adapter | `claude/global/commands/*.md` | `~/.claude/commands/` | Thin prompt for slash command invocation |
| Skill content | `skills/global/*/SKILL.md` | `<project>/.claude/skills/` | Rich skill with full context, invoked via Skill tool |

The Agent/Command adapters are thin (10-20 lines) — just enough personality for the tool to work. The SKILL.md is the detailed canonical knowledge (50-200+ lines) that loads when the skill is actually invoked.

Token impact: only adapter descriptions (~20 tokens each) are loaded into every session. Full SKILL.md content loads on-demand when invoked. Global skills appearing in every project cost negligible tokens.

## Operating Model

- Global reusable expert skills -> user-level Claude subagents + per-project skills
- Global reusable utility skills -> user-level Claude slash commands + per-project skills
- Project-local expert skills -> project `.claude/agents/` + project `.claude/skills/`
- Project-local utility skills -> project `.claude/commands/` + project `.claude/skills/`

## Source Of Truth

Do not edit tool-home copies or project `.claude/skills/` copies directly. They are symlinks.

Edit:

- canonical skill intent in `skills/`
- canonical Claude adapter files in `claude/`
- registry metadata in `registry.json`

Then run the sync helpers:

```bash
# Global agents + commands + project skills
./scripts/sync-claude-adapters.sh --project <name>

# Codex skills
./scripts/sync-codex-skills.sh --project <name>
```

## Current Skill Inventory

Global subagents (8):

- `zorroforge-infra`
- `zorroforge-finance`
- `zorroforge-brand`
- `zorroforge-legal`
- `zorroforge-procurement`
- `governor-auditor`
- `portability-reviewer`
- `remediation-planner`

Global commands (4):

- `multi-agent-governor`
- `project-bootstrap`
- `portability-audit`
- `doctrine-review`

Jarvis project subagents (2):

- `jarvis-system`
- `jarvis-coder`

Jarvis project commands (3):

- `jarvis-healthcheck`
- `jarvis-reviewer`
- `jarvis-audit`

## Validation Runbook

For a full workspace validation or remediation pass driven by Claude itself, use:

- `docs/CLAUDE_VALIDATION_RUN.md`

That runbook provides the preflight reads, verification command, execution order, recovery commands, and copy/paste operator prompt.
