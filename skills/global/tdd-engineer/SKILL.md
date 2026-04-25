---
name: tdd-engineer
description: Use when executing a micro-task plan and about to write production code. Enforces the RED-GREEN-REFACTOR cycle with a watched-failing-test gate, simplest-code-to-pass rule, and a three-fix architecture stop that blocks patch stacking.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# TDD Engineer

**STOP — NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**

Purpose: enforce disciplined Red-Green-Refactor execution against an approved micro-task plan. This skill is the only approved path from plan to committed code.

## Preconditions

- An approved plan exists at `docs/plans/YYYY-MM-DD-<slug>.md` produced by `execution-planner`.
- The next task has a RED test already specified in the plan.

If either precondition is missing, stop and return to the appropriate upstream skill.

## Hard Gates

1. **Watched RED.** The test must be observed failing before a single line of production code is written. "I wrote the test and it would fail" is not sufficient. Run the test. Read the failure output. Confirm the failure is the expected one.
2. **Tests-passing-immediately restart.** If the test passes on its first run, the RED phase was skipped. Delete the test, study why it was already satisfied, rewrite it to fail against the current code, and restart.
3. **Simplest-code GREEN.** The code that turns RED green must be the smallest change that does so. Over-engineering in GREEN is a defect.
4. **REFACTOR only with green bar.** Tests must be passing before any restructure, rename, or deduplication. If GREEN breaks mid-refactor, revert immediately.
5. **Three-fix architecture stop.** If three attempts to fix a single failing test all fail, stop patching. Invoke `root-cause-analyst`. Do not try a fourth patch.
6. **No completion claims from this skill.** When the cycle finishes, hand off to `verification-gate` before declaring the task done.

## Workflow (per task)

### RED
1. Open the test file named in the plan.
2. Write the minimal failing test exactly as specified.
3. Run the test.
4. Confirm the failure mode matches the expected one in the plan.
5. If it passes, apply the Tests-passing-immediately restart gate above.

### GREEN
1. Write the smallest change that makes the test pass.
2. Run the test.
3. Confirm it now passes.
4. Run any other tests in the affected suite to confirm nothing else broke.

### REFACTOR
1. Identify duplication, poor names, or needless branches introduced by GREEN.
2. Apply one refactor at a time.
3. Run the test after each refactor.
4. If any test goes red, revert that refactor and stop refactoring for this task.

### Handoff
- Update the task's status in the plan (for example, append `DONE` to the task ID).
- Hand off to `verification-gate` for fresh end-to-end evidence before committing.

## Red-flag patterns to refuse

- Writing production code first, tests after. Delete the production code. Restart from RED.
- Skipping the test run and assuming the test would fail.
- Writing a test that exercises future work rather than the current task.
- Adding error handling, logging, or helper abstractions in GREEN that were not required by the failing test.
- Stacking patches when a test keeps failing.

## Evidence captured each cycle

- The exact command used to run the test.
- The RED output (showing the expected failure).
- The GREEN output (showing the test now passes and siblings did not regress).

Keep these three lines available for the `verification-gate` handoff.

## Non-goals

- Do not decide scope. That was `execution-planner`.
- Do not debug architectural failures. That is `root-cause-analyst`.
- Do not announce task completion. That is `verification-gate`.
- Do not merge, push, or finalize the branch. That is `branch-finisher`.
