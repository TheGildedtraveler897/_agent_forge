---
name: root-cause-analyst
description: Use when a bug, failing test, or unexpected behavior must be resolved. Enforces a four-phase systematic-debugging workflow that forbids proposing fixes before the root cause is identified and reproduced. Triggered automatically when tdd-engineer hits its three-fix architecture stop.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Root Cause Analyst

**STOP — NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Purpose: when something is broken, resist the urge to patch. Find and confirm the root cause before proposing any fix.

## Hard Gates

1. **No fix proposals in Phase 1.** You may not propose a code change until Phase 3 has produced and validated a falsifiable hypothesis.
2. **One variable per test.** When running hypothesis experiments, change exactly one thing per run. Multi-variable changes are inadmissible as evidence.
3. **Three-fix architecture stop.** If three consecutive fixes aimed at the same symptom fail, patching ends. Architecture or assumptions are wrong. Escalate to `spec-architect` for spec revision or to the human for scope discussion. Do not attempt a fourth fix.
4. **Reproduction first.** A bug that cannot be reliably reproduced does not get a fix. Make it reproducible, then investigate.
5. **Terminal handoff.** The output of this skill is a root cause diagnosis and a proposed fix plan. Implementation itself goes back through `execution-planner` → `tdd-engineer` → `verification-gate`.

## Workflow

### Phase 1 — Investigation (evidence only, no fixes)
1. Read the full error, stack trace, or failure output. Do not paraphrase it. Preserve exact strings.
2. Reproduce the failure deliberately. Record the exact command, inputs, and environment.
3. Review recent commits and uncommitted changes that touched the implicated files or modules.
4. Add targeted logging or assertions at the boundaries (input, output, state transitions). Remove them before the final fix.
5. Collect enough evidence that a second engineer could reproduce the failure from your notes alone.

### Phase 2 — Pattern analysis
1. Identify similar code paths that currently work.
2. Compare them structurally to the failing path.
3. Note every difference, not only the suspicious ones.
4. Name the pattern the failure is breaking (null handling, ordering, resource lifetime, encoding, concurrency, etc.).

### Phase 3 — Hypothesis & experiment
1. State the hypothesis as a falsifiable claim: "If X is true, changing Y in isolation will cause Z."
2. Run the smallest possible experiment that tests the hypothesis.
3. Change exactly one thing per run.
4. Record the result and whether it falsifies the hypothesis.
5. Iterate until a hypothesis survives a clean experiment.

### Phase 4 — Fix plan (not the fix itself)
1. State the root cause in one sentence.
2. State the smallest change that removes the cause.
3. State the regression test that will prove the fix works and will fail if the cause ever returns.
4. Hand off to `execution-planner` if the fix is non-trivial, or directly to `tdd-engineer` if the fix is a single micro-task (write the regression test first, then the fix).

## Red-flag patterns to refuse

- "Let me try another approach" before the first approach has been falsified.
- Stacking `if` guards on top of a failing path to suppress the symptom.
- Blaming upstream systems without reproducing the failure locally first.
- "It works on my machine" as a stopping point.
- Declaring the bug fixed because it no longer occurs on one run. Require the regression test.

## Output

- A root cause statement in plain language.
- The reproduction recipe (command, inputs, environment).
- The regression test specification.
- A pointer to the downstream skill (`execution-planner` or `tdd-engineer`) that will implement the fix.

## Non-goals

- Do not implement the fix here. Implementation goes through the normal planning and TDD path.
- Do not merge or finalize anything. That is `branch-finisher`.
- Do not declare the bug resolved. That is `verification-gate`.
