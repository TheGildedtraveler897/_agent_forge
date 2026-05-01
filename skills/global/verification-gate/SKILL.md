---
name: verification-gate
description: Use when about to claim a task, fix, or change is complete. Blocks completion claims that rest on code inspection, earlier test runs, or subordinate-agent reports. Requires fresh command output and exit codes, detects hedging language, and enforces a five-step assertion protocol.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Verification Gate

**STOP — NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Purpose: sit between "I think it works" and "it works". Completion is an observation, not a prediction.

## Hard Gates

1. **Fresh evidence only.** Prior test runs, earlier CI output, agent reports from upstream tasks, and visual code inspection are all insufficient. Run the proof command now. Read this run's output.
2. **Output must map to claim.** The output you just produced must logically imply the claim. If it only partially supports the claim, the claim must be narrowed until the mapping is clean.
3. **Hedging is not evidence.** Words like "should work", "probably", "I believe", "it looks like", "Great!", and "Done!" are inadmissible as completion signals. If you catch yourself using them, restart this skill.
4. **Exit code matters.** A zero exit code on a command that only prints a warning is still insufficient unless the command actually exercises the claim.
5. **Subordinate-agent reports do not count.** If a dispatched subagent reported success, you must re-run the proof command yourself.
6. **Claim scope matters.** Task-local claims stay in this skill. Feature, phase, sprint, or release completion claims require `goal-verifier` before completion is asserted.

## The Five-Step Assertion Protocol

Follow this in order, every time.

1. **Identify the proof command.** Name the exact command whose output will prove the claim. If no such command exists, the claim is not verifiable — narrow it.
2. **Run it fresh.** Execute the command now, in the current state of the repository, against the current environment.
3. **Read the full output.** Read every line, including stderr and the final exit code.
4. **Map output to claim.** For each element of the claim, cite the line in the output that proves it. Unmapped claim elements must be dropped or re-verified.
5. **Assert with evidence.** State the claim together with the mapped evidence. Bare assertions are rejected.

## Claim Scope Routing

Use this skill for task-local claims:

- one failing test now passes
- one bug fix is verified
- one command produced the expected artifact
- one micro-task's stated verification command passed

Use `goal-verifier` before asserting feature, phase, sprint, or release completion:

- a feature is done
- a sprint shipped
- a phase is complete
- a release is ready
- the original user-visible goal has been satisfied

Passing tests prove only the assertions they exercise. They do not prove overall goal achievement unless `goal-verifier` maps every required goal truth to fresh proof.

## Workflow

1. Collect the claim in one sentence.
2. Decide whether the claim is task-local or goal-level using Claim Scope Routing.
3. For task-local claims, apply the Five-Step Protocol.
4. If any task-local step fails, return the work to the appropriate upstream skill (`tdd-engineer` for red tests, `root-cause-analyst` for unexpected behavior, `execution-planner` for scope gaps).
5. If every task-local step passes, emit a **verification attestation** block.
6. For feature, phase, sprint, or release claims, hand off to `goal-verifier` after task-local evidence is collected. Do not assert broad completion until `goal-verifier` returns a verified verdict.
7. Hand off to `branch-finisher` only after the required task-local or goal-level verification path has passed and this is the end of a development branch.

## Verification Attestation Template

```
Claim: <one sentence>
Proof command: <exact command>
Exit code: <0 or other>
Output evidence:
  - <line from output that maps to claim element 1>
  - <line from output that maps to claim element 2>
Time of run: <freshly now>
Attested by: verification-gate
```

## Red-flag phrases to refuse

- "Should work now."
- "I believe this resolves it."
- "Tests should still pass."
- "Based on the earlier run…"
- "The subagent reported success."
- "Looking at the code, it's obvious that…"
- "The tests passed, so the feature is done."
- "Done!", "Great!", "All set."

If you find any of these in a draft completion message, stop and restart from step 1.

## Insufficient vs. Sufficient evidence

| Insufficient | Sufficient |
|---|---|
| "I checked the code" | Fresh command output mapped to claim |
| "CI passed earlier" | Proof command re-run now against current state |
| "The test file exists" | Test file run and observed passing |
| "The build completed" | Build command produced the artifact and `file`/`ls` confirms it |
| "Subagent reports success" | You re-ran the proof command in the current context |

## Output

- A verification attestation block as above, or
- A bounce-back to the upstream skill with the specific step that failed and what evidence is missing.

## Non-goals

- Do not write or modify code to "help" the claim pass. That is tampering with evidence. Return the work to `tdd-engineer` or `root-cause-analyst`.
- Do not merge or push. That is `branch-finisher`.
- Do not revise scope. That is `spec-architect` / `execution-planner`.
