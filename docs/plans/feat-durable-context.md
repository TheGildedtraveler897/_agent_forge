---
status: approved
branch: feat/durable-context
---
# Plan: Execution Planner Upgrade (Durable Context)

## Objective
Upgrade the `execution-planner` skill to implement a `## Durable Context` persistent heading within plan files. This creates a low-context, branch-specific persistent memory layer that survives plan overwrites and ensures critical continuity across host sessions.

## Key Files & Context
- `skills/global/execution-planner/SKILL.md`: The canonical doctrine for the skill.

## Proposed Solution & Implementation Steps

### 0. Persist Plan & Update Memory (Cross-Host Continuity)
*(First action upon exiting Plan Mode)*
- Save this plan directly to `docs/plans/feat-durable-context.md` with `status: approved` in the frontmatter.
- Use the `memory-archivist` skill to add a pointer to this plan in the `MEMORY.md` active tasks section.

### 1. Upgrade `execution-planner` (Persistent Plan Heading)
- Modify the `execution-planner` skill (`skills/global/execution-planner/SKILL.md`) to include a `## Durable Context` section in its required output template.
- Add an explicit rule: When regenerating or updating an existing plan, the agent MUST preserve the contents of the `## Durable Context` heading exactly. This ensures that branch-specific learnings or constraints are not lost during iteration.

## Verification & Testing
1. Verify the changes in `skills/global/execution-planner/SKILL.md`.
2. Run `python3 scripts/verify-agent-forge.py` to ensure structural integrity.
