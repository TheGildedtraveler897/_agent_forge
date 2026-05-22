---
name: sprint-harvester
description: Run at the end of a sprint to harvest hard-won lessons from diffs, validation artifacts, handoffs, and session context, then append normalized entries to Agent Forge's lesson ledger without silently rewriting doctrine.
context_cost: medium
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Sprint Harvester

Capture durable learning before it evaporates.

## Mission

Turn the end of a sprint into a reusable knowledge-anchor update so the next operator does not have to rediscover the same workaround.

## Inputs

- current repo diff and changed files
- `docs/HANDOFF.md`
- `docs/CHANGELOG.md` if present
- validation artifacts and probe outputs
- recent errors, failed assumptions, and workarounds from session context

## Output Contract

- harvest summary
- normalized lesson entries for `docs/LESSONS_LEARNED.md`
- promotion candidates for doctrine updates
- explicit note of anything that should stay local or ephemeral instead of being harvested

## Rules

1. Harvest only evidenced, reusable lessons.
2. Prefer lessons about architecture, portability, validation, host behavior, and operator workflow over one-off implementation trivia.
3. Append normalized entries to `docs/LESSONS_LEARNED.md` or produce a reviewable diff. Do not silently rewrite doctrine files.
4. Never overwrite `AGENTS.md`, `docs/CONOPS.md`, or other durable truth docs as part of harvesting.
5. If a lesson deserves promotion, name the exact target doc and the reason, but keep promotion as a separate follow-up action.
6. Exclude secrets, auth state, machine-local residue, and transient debugging noise.
7. Mark the lesson status as `active`, `promoted`, or `superseded`.
8. Compaction is downstream and out of scope. Once an entry's `Status:` becomes `promoted` and the named doctrine reference resolves, `lesson-distiller` is the bounded-decay counterpart that archives it. The harvester only appends; it never deletes or rewrites prior entries.

## Workflow

1. Read the current handoff, lesson ledger, and validation artifacts.
2. Inspect the sprint diff and identify:
   - repeated failure modes
   - host quirks
   - portability traps
   - operator or runbook improvements
3. Convert only the durable findings into normalized lesson entries.
4. Separate lesson harvesting from doctrine promotion:
   - lesson ledger entry now
   - doctrine change later, only if the lesson is broad enough to load by default
5. Produce a compact summary of what was harvested, what was intentionally excluded, and what should be promoted next.
