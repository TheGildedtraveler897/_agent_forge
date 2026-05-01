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
7. **Branch preflight.** Non-trivial implementation work must not run on `main` or `master`. Include `scripts/enforce-branch-discipline.sh` in the plan preflight, and create or switch to a named task branch before execution begins.
8. **Plan-quality audit.** Before execution begins, route the completed plan through `plan-quality-auditor`. Implementation may start only after a `PASS` verdict or explicit human override of documented warnings.
9. **Terminal handoff.** On approval and plan-quality pass, hand off to `tdd-engineer` (sequential execution) or `subagent-dispatcher` (parallel execution). Do not invoke implementation skills from here.

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
- **Plan metadata:** `must_haves`, `wave`, `depends_on`, `file_ownership`, `source_coverage`, and `context_budget` where relevant.
- **RED test:** file path + test name + what assertion fails and why (skip only for non-code tasks such as documentation or configuration with no code path).
- **GREEN steps:** the simplest change that makes the test pass. Complete code blocks only.
- **REFACTOR notes:** optional cleanup to do only after GREEN is observed.
- **Verification command:** exact shell command or equivalent and the expected output/exit code.
- **Dependencies:** IDs of tasks that must complete first.

### Plan Metadata Contract

Every non-trivial plan includes a compact metadata block. Use plain Markdown with fenced YAML; do not invent a new parser unless a future spec requires it.

```yaml
must_haves:
  truths:
    - "<observable truth>"
  artifacts:
    - path: "<relative/path>"
      provides: "<why this artifact matters>"
  key_links:
    - from: "<artifact or subsystem>"
      to: "<artifact or subsystem>"
      via: "<connection mechanism>"
wave: 1
depends_on: []
file_ownership:
  - path: "<relative/path>"
    owner_task: "T-01"
source_coverage:
  acceptance_criteria:
    - criterion: "<criterion id or text>"
      covered_by_tasks: ["T-01"]
  decisions:
    - "D-01"
context_budget:
  expected_files: 3
  expected_tasks: 2
  split_required: false
```

Field rules:

- `must_haves.truths` names observable end-state facts the plan must make true.
- `must_haves.artifacts` names files, generated surfaces, runtime artifacts, or docs that must exist.
- `must_haves.key_links` names wiring between artifacts and their consumers.
- `wave` groups tasks that can run after earlier dependency waves complete.
- `depends_on` lists prerequisite task IDs; keep it identical to each task's Dependencies line.
- `file_ownership` prevents parallel workers from claiming the same mutable file.
- `source_coverage.acceptance_criteria` maps every approved acceptance criterion to one or more task IDs.
- `source_coverage.decisions` maps stable decision IDs from the spec, when present.
- `context_budget` states whether the task set is small enough for one worker or must split.

### Phase 4 — Pre-emit audit
Before writing the plan to disk, verify:
- **Spec coverage scan.** Every acceptance criterion from the spec maps to at least one task ID.
- **Must-have coverage scan.** Every truth, artifact, and key link in `must_haves` maps to at least one task and one verification command.
- **Source coverage scan.** Every locked decision and non-goal constraint from the spec is represented in `source_coverage` or explicitly marked out of scope with human approval.
- **Dependency/wave scan.** `depends_on` and `wave` ordering must not allow a task to run before its prerequisites exist.
- **File ownership scan.** Parallelizable tasks must have disjoint `file_ownership`; any shared file forces sequential execution.
- **Context budget scan.** If `context_budget.split_required` is true, split the plan before handoff.
- **Placeholder scan.** No `TBD`, `...`, `fixme`, `placeholder` anywhere in the plan.
- **Type consistency scan.** Function names, signatures, and file paths are identical wherever they appear.
- **Independence check.** If tasks are being handed to parallel agents, tasks that share a file or shared state must be marked sequential, not parallel.

### Phase 5 — Write the plan
Write to `docs/plans/YYYY-MM-DD-<slug>.md`. Include at the top:
- Link to the approved spec.
- Whether execution will be sequential (`tdd-engineer`) or parallel (`subagent-dispatcher`).
- Total task count and rough effort estimate.
- Branch name and branch preflight command.
- The plan metadata contract block, either global for the plan or repeated per task when tasks differ materially.
- A `plan-quality-auditor` handoff section naming the exact plan file and expected audit command or invocation.
- If `dev/active/<slug>/` does not exist, create it, seed `tasks.md` from the plan's task IDs, and initialize `cursor.json` with `python3 scripts/continuity_cursor.py start --slug <slug> --plan docs/plans/YYYY-MM-DD-<slug>.md --task T-01 --next-action "<short next action>"`.

### Phase 6 — Human gate
Present the plan for review and `plan-quality-auditor` pass. On approval, name the next skill explicitly. On rejection or audit failure, loop back to the failed phase.

## Task Template

```
### T-01 — <one-sentence goal>
Files: <exact/path/to/file.ext>, <exact/path/to/test_file.ext>
Dependencies: none | T-<nn>

Plan metadata:
  must_haves:
    truths:
      - <observable truth>
    artifacts:
      - path: <relative/path>
        provides: <why this artifact matters>
    key_links:
      - from: <artifact or subsystem>
        to: <artifact or subsystem>
        via: <connection mechanism>
  wave: <integer>
  depends_on: []
  file_ownership:
    - path: <relative/path>
      owner_task: T-<nn>
  source_coverage:
    acceptance_criteria:
      - criterion: <criterion id or text>
        covered_by_tasks: [T-<nn>]
    decisions: []
  context_budget:
    expected_files: <integer>
    expected_tasks: <integer>
    split_required: false

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

## Checkpoint Discipline

For any plan with more than one micro-task, the executor maintains a transient working tree at `dev/active/<slug>/` containing:

- `cursor.json` — tiny machine-readable resume state, maintained with `scripts/continuity_cursor.py`.
- `plan.md` — pointer or copy reference to `docs/plans/<slug>.md`.
- `context.md` — scratch context dumps, intermediate diffs, evidence not durable enough for the spec.
- `tasks.md` — live task ledger marking which `T-<nn>` is in flight.
- `handoff.md` — optional human-readable compaction output.

Cadence: update `cursor.json` after each meaningful state transition and after each verification command exits. Write `handoff.md` only for explicit `/handoff`, explicit `/checkpoint`, context-risk, rate-limit-risk, or immediately before any `context-engineer` compaction. Do not bind the cadence to a fixed task count.

Token discipline: `cursor.json` is the default continuity artifact and should stay tiny. It records only pointers and state: current task, last completed task, dirty files, last verification command/result, next action, blocker note, and timestamp. Do not capture transcripts by default.

Branch discipline: before any handoff, rate-limit stop, model swap, or end-of-day pause, commit and push the task branch. Record the branch, latest commit hash, next task, and intentional dirty state in `cursor.json` or `handoff.md`.

Lifecycle: created at task start by the executor; deleted at task close by `branch-finisher`. The directory is `.gitignore`d so transient state stays local.

Coexistence: the durable plan lives at `docs/plans/<slug>.md`; the cross-host pointer of record is `MEMORY.md active_tasks` (rewriteable, archivist-owned). Host-local plan tools are not sufficient continuity surfaces unless mirrored into `dev/active/<slug>/cursor.json`. Never promote the contents of `dev/active/<slug>/` into the durable plan or into `MEMORY.md` automatically — promotion is an explicit `branch-finisher` or `sprint-harvester` step.
