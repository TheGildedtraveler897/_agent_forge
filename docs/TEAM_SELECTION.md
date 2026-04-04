# Team Selection

Use this guide to choose the smallest team that can finish the job without collapsing roles.

## Default Choice

If the task is normal repo work with known requirements, use `delivery-team`.

## Choose By Problem Shape

- `governance-team`: adapter drift, missing docs, registry mismatch, portability concerns
- `bootstrap-team`: new project or older repo standardization
- `research-team`: broad or conflicting source gathering is needed before acting
- `planning-team`: requirements are still soft and an executor needs a decision-complete brief
- `delivery-team`: implementation should stay separate from planning and review
- `assessment-team`: work is done but quality, regressions, or acceptance still need proof
- `improvement-team`: findings already exist and now need prioritization plus doctrine/process updates

## Escalation Rules

- Start with one team, not a swarm.
- Add a second team only when the first one would otherwise hold too much unrelated context.
- Use handoff artifacts, not hidden chat memory, when moving between teams.

## Rich Skill Delivery

Project `.claude/skills/` should stay selective:

- include skills that are repeatedly useful in that project
- keep globally available agents and commands thin
- avoid adding project skill delivery just because a skill exists
