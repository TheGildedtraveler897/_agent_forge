# Team Runbooks

This file explains how to use the starter teams in practice without needing a heavy orchestration engine.

## Governance Team

Use this team when:
- a repo may have governance drift
- a new project was just bootstrapped
- a repo was moved, copied, or restructured
- you want an audit-first pass before deeper implementation work

### Claude pattern

Use:
- `/multi-agent-governor` as the main entry
- `governor-auditor` for repo-governance inspection
- `portability-reviewer` for suitcase-doctrine and agent-agnostic path review
- `remediation-planner` for ordered follow-up actions
- `docs/CLAUDE_VALIDATION_RUN.md` when the goal is a full workspace validation or remediation run

Recommended flow:
1. Run `/multi-agent-governor` for a top-level audit.
2. If findings are broad or mixed, use the three governance subagents to split the work.
3. Consolidate into one remediation checklist.

### Codex pattern

Use:
- `multi-agent-governor` skill as the main audit skill
- `portability-auditor` skill for portability-specific depth
- delegated runtime agents only if separate contexts are materially useful

Recommended flow:
1. Run a governance audit.
2. If needed, split portability review into a separate delegated pass.
3. Produce one remediation checklist and stop.

### Stop condition

Stop when:
- blockers and warnings are categorized
- exact remediation actions are listed
- no further mutation is required without explicit approval

## Bootstrap Team

Use this team when:
- creating a governed project
- standardizing an older repo

Primary entry:
- `project-bootstrap`

## Delivery Team

Use this team for actual repo work when planning, building, and review should stay separate.

Primary pattern:
- planner
- builder
- reviewer
