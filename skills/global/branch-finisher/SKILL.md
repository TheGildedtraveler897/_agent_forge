---
name: branch-finisher
description: Use at the end of a development branch to safely integrate, open a pull request, keep as-is, or discard. Enforces a tests-must-pass gate before offering options, a typed confirmation on destructive choices, post-merge re-verification, and refuses hook or signature bypass flags.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Branch Finisher

Purpose: close out a development branch safely. Merge, open a PR, keep as-is, or discard — but only after evidence that the work is in a finishable state.

## Hard Gates

1. **Tests must pass before options are offered.** Do not present merge, PR, or discard options until the full test suite passes in the current branch state. Verification is fresh, not inferred. This skill typically runs after `verification-gate`.
2. **Detect the base branch deliberately.** Do not assume `main`. Inspect the repository to determine the real base branch. Confirm with the user before any merge or PR action.
3. **Typed confirmation for destructive choices.** Discarding a branch, force-pushing, or overwriting upstream requires the user to type the exact branch name. Do not accept "yes" or "ok" alone.
4. **Post-merge re-verification.** After a local merge, re-run the proof command on the base branch before cleaning up the feature branch or worktree. Do not delete anything until the merged state is clean.
5. **No hook or signature bypass.** Never use `--no-verify`, `--no-gpg-sign`, `-c commit.gpgsign=false`, or equivalent flags unless the user has explicitly asked for a specific bypass and explained why.
6. **No force push to the primary branch.** Refuse `--force` or `--force-with-lease` against the base branch. If asked, escalate for explicit human confirmation.

## Workflow

### Step 1 — Verify clean state
1. Inspect working-tree status. Uncommitted changes must be either committed or explicitly acknowledged.
2. Confirm the branch name and the remote it tracks.
3. Identify and confirm the base branch.

### Step 2 — Run the full test suite
Execute the project's full verification command. Read the output and the exit code. A non-zero exit code halts the skill and returns the user to `tdd-engineer` or `root-cause-analyst` depending on the failure mode.

### Step 3 — Present options
Only after Step 2 passes, present four options:
1. **Merge locally into the base branch.**
2. **Open a pull request against the base branch.**
3. **Keep the branch as-is** (no integration action now).
4. **Discard the branch** (destructive — typed confirmation required).

### Step 4 — Execute the chosen option
- **Merge:** fast-forward if possible, otherwise a merge commit with a descriptive message. After merging, re-run the full test suite on the merged state. Only then offer branch or worktree cleanup.
- **PR:** build the PR with a clear title (under ~70 characters) and a body containing summary and test plan. Do not auto-approve or auto-merge the PR.
- **Keep as-is:** record the current state and exit the skill.
- **Discard:** require typed confirmation of the branch name. Prefer recoverable actions (local branch delete) before unrecoverable ones (remote branch delete, reflog expiry).

### Step 5 — Cleanup
Only after Step 4's verification passes:
- Remove worktrees associated with the merged branch if present.
- Remove local branches safely.
- Do not touch unrelated branches or worktrees.

## Red-flag patterns to refuse

- Offering merge when tests have not been re-run on the current state.
- Assuming `main` or `master` is the base branch without checking.
- Accepting "yes" as a destructive confirmation.
- Skipping post-merge re-verification because "the merge was clean".
- Using a hook bypass flag because a hook is inconveniently slow.
- Force-pushing to the base branch.

## Output

- A summary line of the action taken.
- The fresh proof-command output for both pre-action and post-action verification.
- Any cleanup that was performed, listed explicitly.

## Non-goals

- Do not write or fix code here. Return to `tdd-engineer` or `root-cause-analyst` for fixes.
- Do not revise scope. Return to `spec-architect`.
- Do not dispatch subagents — that is `subagent-dispatcher`.
