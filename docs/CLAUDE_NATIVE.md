# Claude Native Integration

Claude Code supports two native reusable specialization primitives that matter here:

- subagents in `~/.claude/agents/` or `.claude/agents/`
- custom slash commands in `~/.claude/commands/` or `.claude/commands/`

## Operating Model

- Global reusable expert skills -> user-level Claude subagents
- Global reusable utility skills -> user-level Claude slash commands
- Project-local expert skills -> project `.claude/agents/`
- Project-local utility skills -> project `.claude/commands/`

## Source Of Truth

Do not edit tool-home copies directly.

Edit:

- canonical skill intent in `skills/`
- canonical Claude adapter files in `claude/`
- registry metadata in `registry.json`

Then run the sync helper.

## Current First-Wave Mapping

Global subagents:

- `zorroforge-infra`
- `zorroforge-finance`
- `zorroforge-brand`
- `zorroforge-legal`
- `zorroforge-procurement`
- `governor-auditor`
- `portability-reviewer`
- `remediation-planner`

Global commands:

- `portability-audit`
- `doctrine-review`

Jarvis project subagents:

- `jarvis-system`
- `jarvis-coder`

Jarvis project commands:

- `jarvis-healthcheck`
- `jarvis-reviewer`
- `jarvis-audit`

Global governance commands:

- `multi-agent-governor`
- `project-bootstrap`

## Validation Runbook

For a full workspace validation or remediation pass driven by Claude itself, use:

- `docs/CLAUDE_VALIDATION_RUN.md`

That runbook provides the preflight reads, verification command, execution order, recovery commands, and copy/paste operator prompt.
