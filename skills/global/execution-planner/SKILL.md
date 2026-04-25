---
name: execution-planner
description: Use when an approved spec exists and work must be decomposed into bite-sized, file-specific, verification-complete tasks before any implementation begins. Emits a micro-task plan with exact file paths, complete code blocks, embedded RED tests, and zero placeholders.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Execution Planner

**STOP — DO NOT WRITE IMPLEMENTATION CODE IN THIS SKILL. ONLY THE PLAN.**

Purpose: turn an approved spec (from `spec-architect`) into a task-by-task implementation plan that is so detailed an executor does not need to make new product or architecture decisions.

## Preconditions

- An approved spec exists at `docs/specs/YYYY-MM-DD-<slug>.md`. If no approved spec exists, stop and invoke `spec-architect`. Do not plan from a verbal or inferred spec.

## Hard Gates

1. **Scope split.** If the spec touches more than one subsystem (independent module, service, or data store), emit one plan file per subsystem. Do not mix subsystems in a single plan.
2. **Micro-task size.** Every task is sized to complete in 2–5 minutes of focused work. If a task grows larger, split it.
3. **Exact file paths.** Every task names the precise file(s) it will create or modify. No "the relevant module" or "the helper file".
4. **Complete code blocks.** No `...`, no `TBD`, no `// implementation here`. If the exact code cannot be written into the plan, the task is not yet decision-complete — refine the spec.
5. **Embedded RED test.** Every task that produces production code includes a named failing test as step one. The test path and test name must be explicit.
6. **Verification command.** Every task ends with the exact command to run to prove the task is done.
7. **Terminal handoff.** On approval, hand off to `tdd-engineer` (sequential execution) or `subagent-dispatcher` (parallel execution). Do not invoke implementation skills from here.

## Workflow

### Phase 1 — Read the approved spec
- Confirm `docs/specs/YYYY-MM-DD-<slug>.md` exists and is marked approved.
- Re-read the acceptance criteria. Every criterion must map to at least one task.

### Phase 2 — Map file structure
List every file that will be created, modified, or deleted. Group them by subsystem. If more than one subsystem is touched, stop and split the plan.

### Phase 3 — Decompose into micro-tasks
For each task write:

- **ID:** `T-<nn>`
- **Goal:** one sentence.
- **Files:** exact paths.
- **RED test:** file path + test name + what assertion fails and why (skip only for non-code tasks such as documentation or configuration with no code path).
- **GREEN steps:** the simplest change that makes the test pass. Complete code blocks only.
- **REFACTOR notes:** optional cleanup to do only after GREEN is observed.
- **Verification command:** exact shell command or equivalent and the expected output/exit code.
- **Dependencies:** IDs of tasks that must complete first.

### Phase 4 — Pre-emit audit
Before writing the plan to disk, verify:
- **Spec coverage scan.** Every acceptance criterion from the spec maps to at least one task ID.
- **Placeholder scan.** No `TBD`, `...`, `fixme`, `placeholder` anywhere in the plan.
- **Type consistency scan.** Function names, signatures, and file paths are identical wherever they appear.
- **Independence check.** If tasks are being handed to parallel agents, tasks that share a file or shared state must be marked sequential, not parallel.

### Phase 5 — Write the plan
Write to `docs/plans/YYYY-MM-DD-<slug>.md`. Include at the top:
- Link to the approved spec.
- Whether execution will be sequential (`tdd-engineer`) or parallel (`subagent-dispatcher`).
- Total task count and rough effort estimate.

### Phase 6 — Human gate
Present the plan for review. On approval, name the next skill explicitly. On rejection, loop back to the failed phase.

## Task Template

```
### T-01 — <one-sentence goal>
Files: <exact/path/to/file.ext>, <exact/path/to/test_file.ext>
Dependencies: none | T-<nn>

RED test:
  File: <test file path>
  Test name: <test_function_name>
  Fails because: <exact assertion that will fail>

GREEN steps:
  1. Open <file>
  2. <complete code block — no ellipsis>
  3. Save

REFACTOR (optional, after GREEN):
  - <specific cleanup, or "none">

Verification:
  Command: <exact command>
  Expected: <exact output or exit code>
```

## Red-flag phrases to refuse

- "Add validation here" (specify the validation).
- "Handle errors appropriately" (specify the error case and response).
- "Update the relevant tests" (name the tests).
- "Implement the feature" (decompose the feature).
- "Various small fixes" (enumerate the fixes).

## Output

- A `docs/plans/YYYY-MM-DD-<slug>.md` file.
- An explicit statement naming the next skill: `tdd-engineer` or `subagent-dispatcher`.

## Non-goals

- Do not write production code.
- Do not run tests.
- Do not dispatch subagents — that is `subagent-dispatcher`.
- Do not revise the spec — return to `spec-architect`.
