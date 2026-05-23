---
name: multi-agent-governor
description: Audit a project for SOTA 2026 multi-agent, multi-LLM, agent-agnostic governance readiness. Use when checking whether a repo stays aligned with Agent Forge contracts, host-surface wiring, handoff discipline, portability rules, and canonical skill delivery.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
delivery_projects: ["*"]
---

# Multi Agent Governor

Audit the target project for multi-agent governance drift.

## What To Check

1. Shared contracts:
   - root and project `AGENTS.md`
   - project `CLAUDE.md` and `GEMINI.md` host adapters
   - durable docs such as `docs/CONOPS.md` and `docs/HANDOFF.md`
   - `docs/LESSONS_LEARNED.md` when prior workaround history matters
2. Claude wiring:
   - `.claude/CLAUDE.md`
   - `.claude/agents/`
   - `.claude/commands/`
   - `.claude/skills/`
3. Codex native delivery:
   - `.agents/skills/`
   - `.codex/agents/`
   - `.codex/config.toml`
4. Gemini native delivery:
   - `GEMINI.md`
   - `.agents/skills/`
   - `.gemini/commands/`
   - `.gemini/agents/`
   - `.gemini/skills/`
   - `.gemini/settings.json`
5. Suitcase portability:
   - no hardcoded local-user paths
   - no machine-specific governance assumptions
6. Canonical alignment:
   - governed project files exist
   - canonical skill and host paths match generated outputs
   - registry compatibility output matches canonical sources

## Workflow

1. Read the current registry and relevant project contracts.
2. Inspect the target project state and host wiring.
3. Report findings ordered by severity.
4. Provide exact remediation actions.
5. Default to audit only; do not mutate unless explicitly asked to fix.

## Output

- `ALIGNED` when the project is clean
- otherwise:
  - blockers
  - warnings
  - remediation commands or follow-up edits
