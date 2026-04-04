# Evaluation

Use this layer to score whether the framework and its outputs are actually helping.

## Severity Tiers

All findings must be tagged with a severity:

- **Blocker** — Must fix before handoff. Goal unclear, acceptance untestable, doctrine violation, missing verification plan.
- **Warning** — Should fix. Context heavier than needed, minor reusability gap, verification present but weak.
- **Note** — Nice-to-have. Style improvement, optional optimization, cosmetic.

A single blocker means the artifact is not ready. Three or more warnings should trigger a revise cycle.

## Brief Quality Check

- goal is concrete (not vague aspirational language)
- success criteria are testable (a script or human can verify)
- constraints are explicit (model tier, time, scope)
- no major decisions left to the implementer

## Handoff Quality Check

- current state is unambiguous
- verified vs assumed is separated
- next restart point is obvious
- no hidden dependency on chat memory

## Context Efficiency Check

- duplicated repo facts removed
- only relevant docs named
- evidence is triaged before handoff
- rich skills are scoped to projects that need them

## Team Fit Check

- team used matches the real job shape
- roles are not overlapping without reason
- handoff artifacts exist between stages
- collapse/escalation conditions were considered

## Scorecard

```md
# Scorecard

- Goal clarity: blocker/warning/note/pass
- Acceptance clarity: blocker/warning/note/pass
- Context efficiency: blocker/warning/note/pass
- Verification quality: blocker/warning/note/pass
- Doctrine alignment: blocker/warning/note/pass
- Reusability: blocker/warning/note/pass

Findings: X blockers, Y warnings, Z notes
Action: keep / revise / reject
```
