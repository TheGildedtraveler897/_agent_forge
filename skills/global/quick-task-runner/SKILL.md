---
name: quick-task-runner
description: Use when a small, bounded task should move faster than the full spec-to-plan workflow without bypassing branch discipline, verification, state capture, or commit hygiene.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Quick Task Runner

**STOP - QUICK DOES NOT MEAN UNGOVERNED.**

Purpose: run small tasks through the lightest safe workflow. This skill is for bounded work where the full `spec-architect` plus `execution-planner` chain would add more overhead than clarity.

## Hard Gates

1. **Branch discipline still applies.** All tiers require a named feature/task branch unless the user explicitly asks for integration or release work on the base branch. Run `scripts/enforce-branch-discipline.sh` before editing.
2. **No scope smuggling.** If the request is ambiguous, cross-subsystem, user-visible, architectural, security-sensitive, or likely to need more than one contained task, stop and route to `spec-architect` or `execution-planner`.
3. **Production behavior needs proof.** If production code behavior changes and a RED test is appropriate, use `tdd-engineer`. Quick mode does not bypass the failing-test gate.
4. **Fresh verification required.** Every tier ends with the relevant proof command and `verification-gate`. Prior runs, summaries, and code inspection do not count.
5. **State for multi-step work.** When more than one meaningful step is involved, capture state in `dev/active/quick-<slug>/cursor.json` using `scripts/continuity_cursor.py`.
6. **Atomic history.** A completed quick task gets one focused commit unless the user explicitly asks to leave it uncommitted for review.
7. **No bypasses.** Do not use hook bypass, signature bypass, force push, or primary-branch implementation shortcuts.

## Tier Selection

Use the smallest tier that safely fits the work.

### `fast`

Use `fast` only for trivial work:

- one file
- no production behavior change
- tiny docs, comment, metadata, or config correction
- no new public interface
- no unresolved requirement or design decision

Required flow:

1. Confirm branch discipline or explicit base-branch integration exception.
2. Restate the one-line change.
3. Edit the file.
4. Run the relevant verification command.
5. Use `verification-gate` before claiming completion.
6. Commit if the work is complete and the user did not ask for review first.

### `quick`

Use `quick` for one contained task that needs a short plan but not a full spec:

- one goal
- one small file set
- one proof command or focused test suite
- clear rollback path
- no parallel work

Required flow:

1. Confirm branch discipline or explicit base-branch integration exception.
2. Write a compact plan summary in the response or local scratch state:
   - goal
   - files
   - proof command
   - commit message
3. If the task has more than one meaningful step, initialize `dev/active/quick-<slug>/cursor.json`.
4. Execute the task.
5. Run the proof command fresh.
6. Use `verification-gate`.
7. Make one atomic commit.

### `quick --validate`

Use `quick --validate` when the task is still small but the cost of false completion is high:

- user-visible behavior
- release-adjacent work
- security, data, or governance impact
- generated surfaces or registry wiring
- any work where tests alone might not prove the goal

Required flow:

1. Confirm branch discipline or explicit base-branch integration exception.
2. Write the compact plan summary.
3. Run `plan-quality-auditor` before execution.
4. Execute through the appropriate implementation skill, including `tdd-engineer` when a RED test is needed.
5. Run the proof command fresh.
6. Use `verification-gate`.
7. Run `goal-verifier` before any feature-level completion claim.
8. Make one atomic commit.

## Cursor Discipline

Use `dev/active/quick-<slug>/cursor.json` when the task has more than one meaningful step, when rate-limit risk exists, or when another agent may resume the work.

Minimum cursor fields should come from `scripts/continuity_cursor.py`:

- current task
- next action
- dirty files
- last verification command and exit code
- blocker note, if any

Keep quick cursors small. Do not store transcripts. Do not promote `dev/active/quick-<slug>/` into durable docs automatically.

## Routing Rules

- Route to `spec-architect` when the user goal or acceptance criteria are unclear.
- Route to `execution-planner` when the task needs multiple micro-tasks, dependencies, or file ownership planning.
- Route to `plan-quality-auditor` when the task is small but scope loss would be expensive.
- Route to `tdd-engineer` when a failing test is the correct first proof.
- Route to `verification-gate` for task-local completion claims.
- Route to `goal-verifier` for feature, phase, sprint, or release completion claims.
- Route to `branch-finisher` only when the branch is ready to integrate, keep, PR, or discard.

## Output

For `fast`:

```text
Quick tier: fast
Goal: <one sentence>
Proof command: <command>
Verification: <exit code and evidence summary>
Commit: <hash or not committed by request>
```

For `quick` and `quick --validate`:

```text
Quick tier: quick | quick --validate
Goal: <one sentence>
Files: <paths>
Proof command: <command>
Cursor: <dev/active/quick-<slug>/cursor.json or none>
Verification: <exit code and evidence summary>
Goal verification: <goal-verifier verdict or not required>
Commit: <hash or not committed by request>
```

## Red-flag patterns to refuse

- Calling a multi-file feature "fast" to avoid planning.
- Editing on `main` or `master` without an explicit integration or release request.
- Skipping verification because the change is small.
- Making broad feature-complete claims after only a task-local proof command.
- Leaving multi-step quick work without a cursor when rate-limit or handoff risk exists.
- Bundling unrelated cleanup into a quick task.

## Non-goals

- Do not replace `spec-architect` for ambiguous or product-shaping work.
- Do not replace `execution-planner` for multi-task implementation.
- Do not replace `tdd-engineer` for behavior changes that need a failing test first.
- Do not replace `branch-finisher` for merge, PR, keep, or discard decisions.
