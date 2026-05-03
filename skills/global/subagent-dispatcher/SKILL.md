---
name: subagent-dispatcher
description: Use when a plan's tasks can be delegated to fresh subagents with isolated context, sequentially or by wave, using depends_on and file_ownership metadata.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Subagent Dispatcher

Purpose: execute a micro-task plan by dispatching independent subagents with isolated context, then reviewing and integrating their output under discipline. This skill covers sequential execution and parallel execution inside explicit dependency waves.

## Preconditions

- An approved plan exists at `docs/plans/YYYY-MM-DD-<slug>.md` from `execution-planner`.
- Each task has: exact files, RED test spec, complete GREEN steps, and a verification command.
- Parallel plans include `wave`, `depends_on`, and `file_ownership` metadata from `execution-planner`.

If any precondition is missing and parallelism is needed, return to `execution-planner`. If metadata is missing and the work is still safe to run, default to sequential execution.

## Hard Gates

1. **Fresh context per dispatch.** Each dispatched agent receives exactly: the task spec, the files it needs, and any minimum context required. Never pass prior session history, unrelated tasks, or wider repo context.
2. **Wave ordering.** Read `wave` and `depends_on` before dispatch. Do not start a task until its dependencies are accepted and integrated. Do not start a later wave until the current wave passes wave-level integration checks.
3. **File ownership check before parallelizing.** Read `file_ownership` before dispatch. Tasks may run in parallel only inside the same `wave`, with disjoint mutable files, no shared mutable state, and no unresolved `depends_on` edge between them. Any doubt defaults to sequential.
4. **Owner record required.** Record which wave, task, file set, and owner each agent receives. If workstreams are involved, keep this aligned with `workstream-manager` lane ownership.
5. **Two-stage review loop.** Every returned result goes through: (a) spec compliance review - does the output match the task spec exactly? (b) code quality review - does the output meet the repo's standards? Fixes loop back to the implementer agent with explicit feedback. The cycle repeats until both stages pass.
6. **Wave-level integration before next wave.** After every wave, integrate accepted results, run the wave-level integration check or full suite required by the plan, and record the command plus exit code before advancing.
7. **No bypass imports.** Do not adopt GSD's hook-bypass, permission-skip, signature-bypass, force-push, or unsafe commit automation behavior.
8. **No completion claims.** After integration, hand off to `verification-gate`.

## Workflow

### Step 1 - Read plan metadata
For each task, extract:
- Task ID and goal.
- `wave`.
- `depends_on`.
- `file_ownership`.
- RED test specification.
- GREEN steps.
- Verification command and expected output.

If a task lacks metadata and the plan expects parallel execution, stop and return to `execution-planner`. If a task lacks metadata but can safely run alone, mark it sequential.

### Step 2 - Partition by waves
Group tasks by `wave`, then sort waves in ascending order. A later wave is locked until every prior wave task is accepted, integrated, and verified.

Inside each wave:
- Parallelize only tasks with disjoint `file_ownership`.
- Keep tasks sequential when they share a file, share mutable state, or have a direct or indirect `depends_on` relationship.
- Treat missing, broad, or ambiguous file ownership as sequential.
- Record the owner for each wave/task/file set before dispatch.

### Step 3 - Prepare the dispatch brief
For each dispatch, prepare a brief that contains only:
- The task ID and goal.
- The wave number.
- The `depends_on` list.
- The `file_ownership` list.
- The assigned owner or agent.
- The exact files the agent may read and write.
- The RED test specification.
- The GREEN steps.
- The verification command and expected output.
- The explicit constraint: "Do not modify files outside the allowed set. Do not invoke unrelated skills."

### Step 4 - Dispatch by wave
- Sequential task: dispatch one task, collect the result, review it, integrate it, then dispatch the next eligible task.
- Parallel tasks: dispatch only tasks in the same wave that passed the file ownership and dependency checks.
- Workstream-backed tasks: confirm the branch/worktree lane and cursor ownership from `workstream-manager` before dispatch.
- Never advance to the next wave while any current-wave task is unreviewed, rejected, blocked, dirty, or unverified.

### Step 5 - Two-stage review
For each returned result:

**Stage A - Spec compliance.** Does the output do exactly what the task asked? No added files, no scope creep, no "helpful" refactors. If not, send back with specific redirection.

**Stage B - Code quality.** Does the output meet the repo's standards (naming, tests present and passing, no hardcoded paths, no dead code)? If not, send back with specific redirection.

Both stages must pass independently. A failure in either stage is a loop-back, not a partial acceptance.

### Step 6 - Wave-level integration
When all accepted results for a wave are ready:
- Confirm no two accepted results edited the same file unexpectedly.
- Confirm actual changed files are within declared `file_ownership`.
- Run the wave-level integration check required by the plan. If the plan does not name one, run the full suite relevant to the touched subsystem.
- Record the command, exit code, output summary, wave number, task IDs, and owner list.
- Start the next wave only after this check passes.

After the final wave passes, run the full-suite command required by the plan, not only the tests named in individual tasks.

### Step 7 - Handoff
Hand off to `verification-gate` with the integration evidence attached.

## Red-flag patterns to refuse

- Parallelizing tasks that share a file "because it's probably fine".
- Parallelizing tasks from different waves.
- Starting a task before its `depends_on` prerequisites are accepted and integrated.
- Ignoring `file_ownership` because the brief "seems obvious".
- Accepting a result because the test passes when the result also added unrelated changes.
- Skipping wave-level integration because per-task suites passed.
- Skipping the final full-suite re-run because wave-level checks passed.
- Passing extensive prior session history to a subagent "for context".
- Declaring integration complete without running the full suite in the current, merged state.
- Adopting GSD hook-bypass, permission-skip, force-push, or signature-bypass commit behavior.

## Output

- A wave ownership table listing wave, task, owner, `depends_on`, and `file_ownership`.
- An integration summary including which tasks were sequential vs. parallel, which loop-backs were applied, each wave-level integration result, and the final full-suite result.
- An explicit handoff line naming `verification-gate` as the next skill.

## Non-goals

- Do not plan scope. That is `execution-planner`.
- Do not implement code yourself — dispatch it. If dispatching is not available in the current environment, execute each task yourself under the same discipline, but still run the two-stage review against your own output.
- Do not declare tasks complete without `verification-gate`.
