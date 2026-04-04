---
name: multi-agent-governor
description: Audit a project for SOTA 2026 multi-agent, multi-LLM, agent-agnostic governance readiness. Use when checking whether a repo stays aligned with Agent Forge contracts, adapter wiring, handoff discipline, portability rules, and canonical skill delivery.
context_cost: light
model_tier: any
---

# Multi Agent Governor

Audit the target project for multi-agent governance drift.

## What To Check

1. Shared contracts:
   - root and project `AGENTS.md`
   - project `CLAUDE.md` adapter
   - durable docs such as `docs/CONOPS.md` and `docs/HANDOFF.md`
2. Claude adapter wiring:
   - `.claude/CLAUDE.md`
   - `.claude/agents/`
   - `.claude/commands/`
3. Codex native skill delivery:
   - `~/.codex/skills` symlinks for declared skills
4. Suitcase portability:
   - no hardcoded local-user paths
   - no machine-specific governance assumptions
5. Registry alignment:
   - governed project files exist
   - canonical skill and adapter paths match declared registry entries

## Workflow

1. Read the current registry and relevant project contracts.
2. Inspect the target project state and adapter wiring.
3. Report findings ordered by severity.
4. Provide exact remediation actions.
5. Default to audit only; do not mutate unless explicitly asked to fix.

## Output

- `ALIGNED` when the project is clean
- otherwise:
  - blockers
  - warnings
  - remediation commands or follow-up edits
