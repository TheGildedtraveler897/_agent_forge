---
name: subagent-dispatcher
description: Use when a plan's tasks can be delegated to fresh subagents with isolated context, either sequentially or in parallel. Enforces context isolation, an independence check before parallelizing, a two-stage review loop, and a full-suite re-run after integration.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Subagent Dispatcher

Purpose: execute a micro-task plan by dispatching independent subagents with isolated context, then reviewing and integrating their output under discipline. This skill covers both sequential single-agent execution and genuinely parallel multi-agent execution.

## Preconditions

- An approved plan exists at `docs/plans/YYYY-MM-DD-<slug>.md` from `execution-planner`.
- Each task has: exact files, RED test spec, complete GREEN steps, and a verification command.

If any precondition is missing, return to `execution-planner`.

## Hard Gates

1. **Fresh context per dispatch.** Each dispatched agent receives exactly: the task spec, the files it needs, and any minimum context required. Never pass prior session history, unrelated tasks, or wider repo context.
2. **Independence check before parallelizing.** Two tasks may be parallelized only if: they touch disjoint files, share no mutable state, and do not depend on each other's side effects. Any doubt defaults to sequential.
3. **Two-stage review loop.** Every returned result goes through: (a) spec compliance review — does the output match the task spec exactly? (b) code quality review — does the output meet the repo's standards? Fixes loop back to the implementer agent with explicit feedback. The cycle repeats until both stages pass.
4. **Full-suite re-run after integration.** When results from multiple agents are merged, run the full test suite. Do not trust per-task passes to imply suite health.
5. **No completion claims.** After integration, hand off to `verification-gate`.

## Workflow

### Step 1 — Partition the plan
For each task, decide: sequential or parallel. Parallelizable tasks share no files and no state. When in doubt, sequential.

### Step 2 — Prepare the dispatch brief
For each dispatch, prepare a brief that contains only:
- The task ID and goal.
- The exact files the agent may read and write.
- The RED test specification.
- The GREEN steps.
- The verification command and expected output.
- The explicit constraint: "Do not modify files outside the allowed set. Do not invoke unrelated skills."

### Step 3 — Dispatch
- Sequential: dispatch one task, collect the result, review (Step 4), integrate, then dispatch the next.
- Parallel: dispatch independent tasks simultaneously, collect all results before the review stage.

### Step 4 — Two-stage review
For each returned result:

**Stage A — Spec compliance.** Does the output do exactly what the task asked? No added files, no scope creep, no "helpful" refactors. If not, send back with specific redirection.

**Stage B — Code quality.** Does the output meet the repo's standards (naming, tests present and passing, no hardcoded paths, no dead code)? If not, send back with specific redirection.

Both stages must pass independently. A failure in either stage is a loop-back, not a partial acceptance.

### Step 5 — Integration
When all tasks have been accepted, integrate the changes:
- Confirm no two accepted results edited the same file unexpectedly.
- Run the full test suite, not only the tests named in individual tasks.
- Record the command and its output.

### Step 6 — Handoff
Hand off to `verification-gate` with the integration evidence attached.

## Red-flag patterns to refuse

- Parallelizing tasks that share a file "because it's probably fine".
- Accepting a result because the test passes when the result also added unrelated changes.
- Skipping the full-suite re-run because per-task suites passed.
- Passing extensive prior session history to a subagent "for context".
- Declaring integration complete without running the full suite in the current, merged state.

## Output

- An integration summary including which tasks were sequential vs. parallel, which loop-backs were applied, and the full-suite result.
- An explicit handoff line naming `verification-gate` as the next skill.

## Non-goals

- Do not plan scope. That is `execution-planner`.
- Do not implement code yourself — dispatch it. If dispatching is not available in the current environment, execute each task yourself under the same discipline, but still run the two-stage review against your own output.
- Do not declare tasks complete without `verification-gate`.
