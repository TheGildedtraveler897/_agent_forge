---
name: workstream-manager
description: Use when concurrent agent or human work must be split into safe branches, worktrees, owners, file ownership lanes, and resumable continuity cursors.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Workstream Manager

**STOP - PARALLEL WORK NEEDS EXPLICIT LANES.**

Purpose: manage concurrent work as branches/worktrees plus independent `dev/active/<slug>/cursor.json` state. This skill keeps multiple agents or humans from writing the same branch, claiming the same files, or losing resume context at rate-limit, handoff, or end-of-day boundaries.

## Hard Gates

1. **One writable lane per workstream.** A workstream owns one branch and, when concurrent local execution is needed, one worktree. Do not let two agents write the same branch unless the operator explicitly declares deliberate pairing.
2. **File ownership before dispatch.** Before parallel work begins, record the mutable files each workstream may change. Two active workstreams may not claim the same mutable file unless they are serialized or deliberately paired.
3. **Branch discipline applies.** Implementation work must use a named feature or task branch. Do not work on `main` or `master` unless the user explicitly asks for integration or release work.
4. **Independent cursor state.** Every non-trivial workstream records resume state in `dev/active/<slug>/cursor.json`. Do not use host-local memory, chat history, or a hidden `.planning/` directory as the source of truth.
5. **Checkpoint before interruption.** Before a pause, handoff, rate-limit stop, model swap, or end-of-day stop, record branch, upstream, latest commit, dirty state, next task, and owner.
6. **No unsafe cleanup.** Completing a workstream does not delete branches, worktrees, or `dev/active/<slug>/` state. Route closure to `branch-finisher`.

## Workstream Record

Each active workstream must have a compact record in its cursor. Use `scripts/continuity_cursor.py` for the base cursor fields, then preserve this workstream block when recording lane state:

```json
{
  "workstream": {
    "owner": "<agent-or-human>",
    "branch": "<branch-name>",
    "upstream": "<remote-branch-or-none>",
    "worktree": "<path-or-none>",
    "latest_commit": "<commit-hash>",
    "dirty_state": "clean|dirty",
    "next_task": "<task-id-or-next-action>",
    "pairing": false,
    "file_ownership": ["<relative/path>"]
  }
}
```

Required fields:
- `owner`: the responsible agent or human.
- `branch`: the branch being written.
- `upstream`: the tracked remote branch, or `none` until first push.
- `worktree`: the worktree path when one exists, otherwise `none`.
- `latest_commit`: the latest local commit hash for the lane.
- `dirty_state`: `clean` or `dirty`; if dirty, summarize intentional dirty files in the cursor note.
- `next_task`: the next task ID or concrete next action.
- `pairing`: `true` only when the operator deliberately allows two agents on one branch.
- `file_ownership`: repo-relative mutable paths this workstream may edit.

## Actions

Use these actions as skill workflow actions, not host-specific slash commands: create, list, switch, status, complete, resume.

### create

Use when starting a new lane of work.

1. Confirm the base branch and current working tree state.
2. Choose a branch name that names the task or workstream.
3. If local concurrent execution is needed, create or select a dedicated worktree for that branch.
4. Assign one owner.
5. Record file ownership before dispatch. If ownership overlaps an active workstream, stop and serialize, split the files, or get explicit pairing approval.
6. Initialize `dev/active/<slug>/cursor.json` with `scripts/continuity_cursor.py start`.
7. Add the workstream block with branch, upstream, latest commit, dirty state, next task, owner, pairing, worktree, and file ownership.
8. Push the branch and set upstream before handoff if another host or agent may resume it.

### list

Use when the operator asks what work is currently in flight.

1. Inspect active branches, worktrees, and `dev/active/*/cursor.json`.
2. Report each workstream's owner, branch, upstream, latest commit, dirty state, next task, and file ownership.
3. Flag missing cursors, missing upstreams, dirty worktrees, duplicate branch writers, and file ownership collisions.
4. Do not infer completion from a clean tree; route completion claims to `verification-gate`.

### switch

Use when moving the current agent or human to an existing lane.

1. Read the target cursor before switching.
2. Confirm the target branch, worktree, latest commit, dirty state, owner, and next task.
3. Refuse to switch into a branch already owned by another active non-paired workstream.
4. If switching hosts or models, restate the exact cursor path and next action before editing.

### status

Use when checking whether a workstream is safe to continue, hand off, or integrate.

1. Refresh branch, upstream, latest commit, and dirty state from the repository.
2. Compare actual changed files to declared `file_ownership`.
3. Update `dev/active/<slug>/cursor.json` after any verification command exits.
4. Report blockers, missing upstream, ownership collisions, stale commit pointers, and dirty state explicitly.

### complete

Use when a lane's assigned task appears finished.

1. Run the task's required verification command in the lane.
2. Record the verification command and exit code in `dev/active/<slug>/cursor.json`.
3. Hand off completion claims to `verification-gate`.
4. Route branch integration, PR, keep-as-is, discard, worktree cleanup, and cursor cleanup to `branch-finisher`.
5. Do not delete local or remote branches from this skill.

### resume

Use after a rate limit, model swap, handoff, or next-day return.

1. Read `dev/active/<slug>/cursor.json` first.
2. Confirm the branch, upstream, latest commit, dirty state, owner, next task, and file ownership.
3. Confirm the working tree still matches the cursor's branch and ownership claims.
4. If the cursor is stale, refresh status before editing and record the mismatch.
5. Continue with the next task only after branch discipline and ownership checks pass.

## Red-flag Patterns To Refuse

- Two agents writing the same branch without explicit deliberate pairing.
- Parallel workstreams claiming the same mutable file because "the edits are probably separate."
- Starting work without a branch or worktree lane when another agent may work concurrently.
- Resuming from chat history while ignoring `dev/active/<slug>/cursor.json`.
- Treating clean git status as proof that a workstream is complete.
- Deleting worktrees, branches, or cursor state before `branch-finisher` has run.
- Creating `.planning/` or another competing state root for GSD-style workstreams.

## Output

For create, switch, status, complete, and resume, report:

```text
Workstream: <slug>
Owner: <agent-or-human>
Branch: <branch>
Upstream: <upstream-or-none>
Worktree: <path-or-none>
Latest commit: <hash>
Dirty state: <clean|dirty plus intentional dirty files if any>
Next task: <task-id-or-next-action>
File ownership: <paths>
Cursor: dev/active/<slug>/cursor.json
Next skill: <subagent-dispatcher|verification-gate|branch-finisher|none>
```

For list, report one compact line per workstream plus any collisions or missing state.

## Non-goals

- Do not decompose plans or assign waves; that is `execution-planner`.
- Do not dispatch or review subagents; that is `subagent-dispatcher`.
- Do not verify feature-level completion; that is `verification-gate` and `goal-verifier`.
- Do not merge, open PRs, discard branches, or clean worktrees; that is `branch-finisher`.
- Do not introduce new state roots or generated host-specific commands.
