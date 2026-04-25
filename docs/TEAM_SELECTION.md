# Team Selection

Use this guide to choose the smallest team that can finish the job without collapsing roles.

## Default Choice

If the task is normal repo work with known requirements, use `delivery-team`.

## Choose By Problem Shape

- `governance-team`: host-surface drift, missing docs, portability concerns, stale generated outputs
- `bootstrap-team`: new governed project or older repo standardization
- `research-team`: broad or conflicting source gathering before action
- `planning-team`: requirements are still soft and an executor needs a decision-complete brief
- `delivery-team`: implementation should stay separate from planning and review
- `assessment-team`: work is done but quality or regressions still need proof
- `improvement-team`: findings already exist and now need prioritization, doctrine updates, and lesson harvesting

## Escalation Rules

- start with one team, not a swarm
- add a second team only when the first would otherwise hold too much unrelated context
- move between teams with explicit handoff artifacts, not hidden memory

## Selective Capability Delivery

Project-local host surfaces should stay selective:

- include project-local capabilities only when the repo genuinely needs them
- keep global user-home overlays thin
- avoid adding delivery targets just because a capability exists
- use `docs/LESSONS_LEARNED.md` to record durable lessons before promoting them into always-loaded doctrine
