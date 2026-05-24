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
2. **Context Rot Limit (Max 4 Tasks).** To prevent "Lost in the Middle" degradation, no single plan may exceed 4 atomic tasks. If the approved spec requires more than 4 tasks, segment the work and plan only the first 4 tasks. The remaining work must be deferred to a follow-up plan via a fresh session.
3. **Micro-task size.** Every task is sized to complete in 2–5 minutes of focused work. If a task grows larger, split it.
3. **Exact file paths.** Every task names the precise file(s) it will create or modify. No "the relevant module" or "the helper file".
4. **Complete code blocks.** No `...`, no `TBD`, no `// implementation here`. If the exact code cannot be written into the plan, the task is not yet decision-complete — refine the spec.
5. **Embedded RED test.** Every task that produces production code includes a named failing test as step one. The test path and test name must be explicit.
6. **Verification command.** Every task ends with the exact command to run to prove the task is done.
7. **Branch preflight.** Non-trivial implementation work must not run on `main` or `master`. Include `scripts/enforce-branch-discipline.sh` in the plan preflight, and create or switch to a named task branch before execution begins.
8. **Terminal handoff.** On approval, hand off to `tdd-engineer` (sequential execution) or `subagent-dispatcher` (parallel execution). Do not invoke implementation skills from here.
9. **Persisted plan artifact.** The plan must be written to `docs/plans/<branch-slug>.md` with frontmatter `status: awaiting-approval` BEFORE presenting it for review. This guarantees the plan survives session glitches, context overflow, or model swaps, and is discoverable by peer agents on other hosts via the `MEMORY.md active_tasks` pointer. Never present a plan body without first persisting it.

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

### Phase 5 — Write the plan with awaiting-approval status

The plan is persisted to disk **before** the human approval gate. This is non-negotiable: if the session glitches mid-review, the plan must survive.

- Resolve the current branch: `git branch --show-current`.
- Slugify it (replace `/` with `-`). Example: `feat/ship-prep` → `feat-ship-prep`.
- Target path: `docs/plans/<branch-slug>.md`.
- If a plan file already exists for this branch:
  - Read its frontmatter status.
  - If status is `approved` or `in-progress`, **halt** and surface a confirmation prompt to the operator. Existing work may be in-flight; overwriting without consent would orphan a continuity cursor.
  - If status is `awaiting-approval`, `superseded`, or `completed`, overwrite is safe.
- Write the plan file with this frontmatter:

  ```yaml
  ---
  plan_id: <branch-slug>
  branch: <full branch name>
  status: awaiting-approval
  created: <ISO 8601 UTC>
  last_updated: <same as created>
  spec_ref: <docs/specs/YYYY-MM-DD-<slug>.md, or null>
  task_count: <int>
  execution_mode: sequential | parallel
  approved_at: null
  approved_by: null
  title: <one-line plan title>
  ---
  ```

- Body includes:
  - **Durable Context**: A dedicated `## Durable Context` section at the top of the body. This is a low-context, branch-specific persistent memory layer. **If a plan file already exists, the agent MUST preserve the contents of this section exactly when overwriting or updating.**
  - Link to the approved spec (if one exists).
  - Branch name and branch preflight command.
  - Total task count and rough effort estimate.
  - All micro-tasks T-01..T-NN per the Task Template.

- Append a one-line pointer to project `MEMORY.md` `active_tasks` section via `memory-archivist`:

  ```
  - Plan: docs/plans/<branch-slug>.md — <one-line title> (status: awaiting-approval, tasks: <count>)
  ```

- Commit the plan file with message: `Plan: <branch-slug> (awaiting approval)`.

**Do not** initialize `dev/active/<slug>/` at this stage. The continuity cursor is created only on approval (Phase 6c), because cursor state implies execution intent.

### Phase 6 — Human approval gate

Present the plan **file path** (not the full plan body inline) for review:

> "Plan saved to `docs/plans/<branch-slug>.md` (status: awaiting-approval). Please review and approve, request changes, or reject."

#### Phase 6a — On approval

- Update plan frontmatter:
  - `status: approved`
  - `last_updated: <now>`
  - `approved_at: <now>`
  - `approved_by: <operator identifier>`
- Update the MEMORY.md pointer status field.
- Initialize the continuity cursor:
  ```
  python3 scripts/continuity_cursor.py start \
    --slug <branch-slug> \
    --plan docs/plans/<branch-slug>.md \
    --task T-01 \
    --next-action "<short next action>"
  ```
  This creates `dev/active/<branch-slug>/` with `cursor.json`, `tasks.md`, etc.
- Commit: `Plan: <branch-slug> (approved)`.
- Name the next skill explicitly: `tdd-engineer` (sequential) or `subagent-dispatcher` (parallel).

#### Phase 6b — On rejection

- Update plan frontmatter:
  - `status: superseded`
  - `last_updated: <now>`
- Update the MEMORY.md pointer status field.
- Commit: `Plan: <branch-slug> (superseded)`.
- Loop back to the failed phase. The superseded file remains on disk as iteration history until the next plan overwrites it.

#### Phase 6c — On revision request

- Treat as a loop-back to Phase 1 or 3 (operator names the phase).
- Phase 5 will overwrite the file with a new `awaiting-approval` plan once the revision is ready.
- No frontmatter update at this stage — the existing `awaiting-approval` file is the iteration baseline.

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

- A `docs/plans/<branch-slug>.md` file with status frontmatter (initially `awaiting-approval`, transitioning to `approved` or `superseded` after the human gate).
- A one-line pointer in project `MEMORY.md active_tasks` section.
- On approval, an initialized `dev/active/<branch-slug>/` directory with cursor state.
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
