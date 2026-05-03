---
name: plan-quality-auditor
description: Use when an implementation plan, sprint plan, or multi-agent dispatch plan must be checked before execution for goal delivery, requirement coverage, hidden scope loss, dependency correctness, and verifier strength.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Plan Quality Auditor

**STOP - DO NOT EXECUTE A PLAN UNTIL THIS AUDIT HAS A PASSING VERDICT OR EXPLICIT HUMAN OVERRIDE.**

Purpose: audit whether a plan can actually deliver the approved goal before implementation begins. This skill is stricter than `quality-gate`: it checks goal delivery, not just artifact polish.

## Hard Gates

1. **Goal-backward audit.** Start from the approved spec, user goal, or accepted brief. Work backward to the truths that must be observable when the plan is done.
2. **Requirement coverage.** Every acceptance criterion, locked decision, and non-goal constraint must map to at least one task and one verification command.
3. **No hidden scope reduction.** Phrases like "simplify", "defer", "phase later", "for now", or "not needed" are blockers unless tied to an explicit human-approved decision.
4. **Dependency correctness.** Tasks must be ordered so prerequisites exist before dependent work starts. Parallel tasks must have disjoint file ownership and no shared mutable state.
5. **Key-link coverage.** Plans must connect artifacts to their consumers. A file that is created but never wired into the runtime, docs, registry, team manifest, or verifier is not complete.
6. **Verifier strength.** Verification commands must prove the claim they are attached to. Code inspection, agent summaries, stale test output, and "should work" statements are inadmissible.
7. **Context budget sanity.** If a plan asks one worker to hold too many files, domains, or decisions at once, require a split before execution.
8. **Canonical-layer fit.** Agent Forge changes must land in canonical sources first. Generated host surfaces are delivery targets, not authoring surfaces.

## Inputs

Read only the smallest set needed for the audit:

- approved spec or user brief
- implementation plan
- evidence pack, if one exists
- affected skill, team, policy, or script files named by the plan
- current branch and dirty-state summary

If no approved spec or accepted brief exists, stop and route to `spec-architect`.
If no implementation plan exists, stop and route to `execution-planner`.

## Workflow

### Step 1 - Reconstruct The Goal

Write a compact goal statement in one sentence. Then derive the plan's `must_haves` even if the plan has not adopted explicit `must_haves` metadata yet:

- observable truths
- required artifacts
- key links between artifacts
- required verification evidence
- locked decisions
- non-goal constraints

Missing explicit metadata is a warning. Missing actual goal coverage is a blocker.

### Step 2 - Build The Coverage Matrix

For each acceptance criterion or locked decision, map:

- source requirement
- task ID
- files changed
- proof command
- expected evidence

Any row without a task is a blocker.
Any row without a proof command is a blocker.
Any proof command that does not logically prove the row is a blocker.

### Step 3 - Audit Task Integrity

Check every task for:

- exact file paths
- clear dependencies
- bounded task size
- RED test or justified non-code exception
- GREEN steps that do not smuggle extra scope
- verification command with expected result
- branch and checkpoint discipline
- generated-surface safety
- file ownership when parallel work is planned

### Step 4 - Run Adversarial Checks

Look specifically for:

- scope reduction hidden as "MVP"
- placeholder language
- skipped tests
- circular tests where expected values come from the implementation under test
- static or fake data standing in for real wiring
- orphan artifacts
- missing registry, manifest, or docs integration
- security or trust posture regressions
- host-specific instructions in global skills
- plans that depend on Claude-only, Codex-only, or Gemini-only behavior without documenting the exclusion

### Step 5 - Emit Verdict

Use exactly one verdict:

- `PASS` - no blockers; implementation may proceed.
- `REVISE` - no blockers, but warnings should be fixed before expensive work starts.
- `FAIL` - one or more blockers; implementation must not start.

Warnings are allowed only when the plan can still deliver the approved goal safely.

## Output Format

```text
# Plan Quality Audit: <plan name>

Verdict: PASS | REVISE | FAIL

Goal:
- <one sentence>

Must-haves:
- Truths: <items>
- Artifacts: <items>
- Key links: <items>
- Required evidence: <items>

Coverage:
| Requirement | Task | Files | Proof | Result |
|---|---|---|---|---|

Blockers:
- <none or blocker list>

Warnings:
- <none or warning list>

Revision Instructions:
- <specific edits required before execution>

Next Skill:
- `tdd-engineer` for sequential implementation, `subagent-dispatcher` for parallel implementation, or `execution-planner` if revisions are required.
```

## Handoff Rules

- `PASS` hands off to `tdd-engineer` or `subagent-dispatcher`.
- `REVISE` normally returns to `execution-planner`, unless the warnings are explicitly accepted by the operator.
- `FAIL` returns to `execution-planner` or `spec-architect`, depending on whether the blocker is a plan defect or a missing decision.
- This skill never declares implementation complete. Completion claims belong to `verification-gate` and feature-level completion belongs to `goal-verifier`.

## Non-goals

- Do not write or modify implementation files.
- Do not repair the plan during the audit.
- Do not replace `quality-gate`; this skill is specifically for implementation-plan readiness.
- Do not replace `verification-gate`; this skill runs before execution, not after.
- Do not replace `goal-verifier`; this skill predicts whether a plan can deliver, while `goal-verifier` proves whether completed work did deliver.
