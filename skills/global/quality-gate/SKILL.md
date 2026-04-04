---
name: quality-gate
description: Score plans, handoffs, and outputs against clarity, verification, doctrine, and context-efficiency checks. Use after planning or execution to decide whether a result is ready to hand off or ship.
context_cost: light
model_tier: any
---

# Quality Gate

Evaluate an artifact before it moves to the next stage.

## Checks

1. Goal clarity
2. Acceptance clarity
3. Verification quality
4. Context efficiency
5. Doctrine alignment
6. Reusability of the output

## Severity Tiers

- **Blocker** — Must fix before handoff. Goal unclear, acceptance untestable, doctrine violation, missing verification plan.
- **Warning** — Should fix. Context heavier than needed, minor reusability gap, verification present but weak.
- **Note** — Nice-to-have. Style improvement, optional optimization, cosmetic.

A single blocker means the artifact is not ready. Warnings accumulate — 3+ warnings should trigger a revise cycle.

## Output

- severity-tagged findings (blocker/warning/note)
- one compact scorecard
- explicit next action: keep, revise, or reject

## Example Scorecard

```
# Quality Gate: playlist-archive implementation brief

- Goal clarity: PASS
- Acceptance clarity: WARNING — "downloads work" is vague; specify: yt-dlp exits 0, file exists, metadata preserved
- Verification quality: BLOCKER — no verification commands listed; add exact CLI test
- Context efficiency: PASS — brief is 40 lines, no repo facts repeated
- Doctrine alignment: PASS — no hardcoded paths, .env for credentials
- Reusability: NOTE — script could be parameterized for other archives later

Findings: 1 blocker, 1 warning, 1 note
Action: REVISE — fix verification plan, tighten acceptance criteria
```
