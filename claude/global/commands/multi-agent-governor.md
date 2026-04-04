---
description: Audit a project for Agent Forge governance drift, adapter wiring, and portable multi-agent readiness
argument-hint: [optional project path or name]
---

Audit the target project for multi-agent governance alignment.

Check:
- required governance files
- `AGENTS.md` and `CLAUDE.md` role separation
- `docs/CONOPS.md` and `docs/HANDOFF.md` presence
- `.claude` adapter wiring
- Codex skill delivery when applicable
- suitcase portability and agent-agnostic structure
- registry alignment against `_agent_forge`

Default to audit-only behavior and provide exact remediation actions.

Optional target: $ARGUMENTS
