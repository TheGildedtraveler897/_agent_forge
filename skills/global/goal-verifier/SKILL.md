---
name: goal-verifier
description: Use when a feature, sprint, phase, or release completion claim must be verified against the original user-visible goal instead of summaries, commits, tests alone, or agent reports.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Goal Verifier

**STOP - DO NOT CLAIM FEATURE, PHASE, SPRINT, OR RELEASE COMPLETION FROM SUMMARIES ALONE.**

Purpose: prove whether completed work actually satisfies the approved goal. This skill runs after implementation evidence exists and before a broad completion claim is made.

## Hard Gates

1. **Goal-backward verification.** Start from the approved spec, user brief, or accepted sprint goal. Reconstruct the observable truths that must be real if the goal is complete.
2. **Evidence over reports.** Do not trust summaries, commit messages, branch names, checklists, or agent reports as proof. Treat them as claims that need verification.
3. **Full verification levels.** Check truths, artifacts, substance, wiring, data flow, disabled or skipped tests, circular tests, assertion strength, and manual acceptance uncertainty.
4. **No hollow success.** A passing command is insufficient when the artifact is stubbed, orphaned, static, unwired, or not reachable through the path the user will exercise.
5. **Tests prove only their assertions.** Passing tests support the specific behavior they exercise. They do not prove the overall goal unless every required truth maps to a strong assertion or direct artifact proof.
6. **Uncertainty is explicit.** If a truth cannot be proven from available commands or artifacts, mark it as `UNCERTAIN WARNING`. Do not silently upgrade uncertainty into success.
7. **Fix-plan handoff.** Every `FAILED BLOCKER` must name the missing truth, proof command or evidence path, likely owner, and next skill: `root-cause-analyst` for broken behavior or `execution-planner` for missing scope.

## Inputs

Read the smallest evidence set that can prove or disprove the goal:

- approved spec, user brief, or sprint goal
- implementation plan and Decision IDs, if present
- current git diff or landed commit range
- proof commands and fresh command outputs
- generated artifacts, runtime artifacts, or evidence paths named by the work
- relevant tests, including skipped or disabled tests
- wiring surfaces such as registries, manifests, policies, docs, or generated delivery surfaces

If no approved goal or accepted brief exists, stop and route to `spec-architect`. If no implementation evidence exists, stop and route to `verification-gate` or `tdd-engineer` as appropriate.

## Workflow

### Step 1 - Reconstruct The Goal

Write one sentence for the user-visible goal. Then derive the required truths:

- observable behavior or operator outcome
- required artifacts
- key links between artifacts and their consumers
- data flow from input to user-visible result
- locked decisions or non-goal constraints that must remain true
- required proof commands and evidence paths

### Step 2 - Build The Goal Matrix

For every required truth, record:

- source requirement
- expected artifact, behavior, or data path
- proof command
- evidence path
- verdict: `VERIFIED`, `FAILED BLOCKER`, or `UNCERTAIN WARNING`

Do not merge rows just because one command passes. Each truth needs its own proof mapping.

### Step 3 - Verify Artifacts And Substance

Inspect artifacts as evidence, not as a checklist:

- Required files exist at the expected paths.
- Generated outputs match the canonical source, not stale or hand-edited surfaces.
- New skills, policies, teams, scripts, or docs are wired to their actual consumers.
- Stub content, placeholder text, TODO markers, fake data, or static examples are not standing in for real behavior.
- Runtime artifacts prove the current branch state, not an earlier branch or stale run.

### Step 4 - Verify Wiring And Data Flow

Trace each goal-critical path end to end:

- input or trigger
- canonical source
- renderer, registry, manifest, policy, script, or command path
- runtime or operator-facing surface
- observed output or durable artifact

If a created artifact is never consumed, mark the related truth as `FAILED BLOCKER`. If the wiring likely exists but cannot be proven in the current environment, mark it as `UNCERTAIN WARNING` and name the missing proof.

### Step 5 - Audit Test Strength

Review the tests or proof commands that support the claim:

- Identify skipped, disabled, quarantined, or expected-failure tests that overlap the goal.
- Reject circular tests where expected values come from the implementation under test.
- Reject assertions that only prove file presence when the goal requires behavior.
- Reject smoke tests that do not touch the user-visible path being claimed.
- Record which truths remain unproven by automated checks.

### Step 6 - Emit Verdict

Use the weakest applicable overall verdict:

- `VERIFIED` - every required truth is proven by fresh command output, artifact inspection, or evidence path.
- `FAILED BLOCKER` - at least one required truth is false, missing, unwired, stubbed, or contradicted.
- `UNCERTAIN WARNING` - no blocker is proven, but at least one required truth cannot be verified from available evidence.

Do not claim feature, sprint, phase, or release completion unless the overall verdict is `VERIFIED`.

## Output Format

```text
# Goal Verification: <goal or feature name>

Overall verdict: VERIFIED | FAILED BLOCKER | UNCERTAIN WARNING

Goal:
- <one sentence>

Goal matrix:
| Truth | Source | Proof command | Evidence path | Verdict | Notes |
|---|---|---|---|---|---|

Blockers:
- <none or blocker list with fix-plan handoff>

Warnings:
- <none or uncertainty list>

Proof commands:
- <command, exit code, and what it proves>

Evidence paths:
- <path and why it matters>

Fix-plan handoff:
- <none, or route to root-cause-analyst / execution-planner with the exact missing truth>
```

## Handoff Rules

- `VERIFIED` may hand off to `branch-finisher` when the branch is otherwise ready.
- `FAILED BLOCKER` routes to `root-cause-analyst` when behavior is broken or contradictory.
- `FAILED BLOCKER` routes to `execution-planner` when accepted scope is missing or was never planned.
- `UNCERTAIN WARNING` requires operator acknowledgement before any broad completion claim.

## Red-flag phrases to refuse

- "The tests passed, so the feature is done."
- "The agent said it completed the sprint."
- "The commit message says this shipped."
- "The file exists, so the integration works."
- "This warning is probably fine."
- "The rest can be verified later."

## Non-goals

- Do not replace `verification-gate`; this skill verifies goal achievement after task-level proof exists.
- Do not replace `plan-quality-auditor`; that skill predicts whether a plan can deliver before implementation starts.
- Do not write fixes while verifying. Route failures to the appropriate upstream skill.
- Do not merge, push, or close branches. That is `branch-finisher`.
