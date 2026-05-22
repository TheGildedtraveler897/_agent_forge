---
name: code-review-doctrine
description: Review code changes for doctrine violations, portability regressions, hidden risk, hardcoded secrets, premature infrastructure, and over-engineered abstractions. Use when the user asks for a review or pre-commit audit.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
delivery_projects: ["*"]
claude_command_name: doctrine-review
gemini_command_name: doctrine-review
---

# Code Review Doctrine

Review diffs or changed files against practical engineering doctrine.

## Review Priorities

1. Hardcoded secrets or credentials
2. Security regressions
3. Portability regressions
4. Destructive or risky behavior without clear operator control
5. Over-engineered abstractions with no real caller
6. Premature infra or dependency expansion

## Workflow

1. Inspect staged and unstaged diffs when git is available.
2. If git is not available, review the provided files directly.
3. Prefer bug/risk findings over style commentary.
4. Keep findings concise and actionable.

## Output Format

- One finding per bullet
- Lead with file and line when available
- If nothing is wrong, say `Doctrine aligned. Ready to commit.`

## Non-Goals

- Do not rewrite the code during review unless the user asks for fixes.
- Do not pad the output with summaries when the findings are the important part.

## Receiving Review Feedback

When this skill is used on the receiving side (your own code has been reviewed), the discipline flips.

### Hard Gates (receiving)

1. **Unclear feedback stops implementation.** If a review comment is ambiguous, stop. Ask one clarifying question. Do not guess the reviewer's intent and act on the guess.
2. **Verify against the current codebase.** Before accepting or pushing back on a finding, check whether it reflects the current state of the code. Reviewers sometimes comment on stale diffs.
3. **One item at a time.** Address review items individually, not in a sweep. Each addressed item becomes its own small change with its own verification.
4. **Technical reasoning, not social performance.** If you disagree with a finding, disagree with a technical reason grounded in the code. "I'll fix it" without understanding is worse than a reasoned pushback.

### Receiving workflow

1. **Read completely.** Read the entire review before starting. Do not react to the first finding in isolation.
2. **Restate.** In your own words, restate each finding. If you cannot, ask for clarification on that item.
3. **Categorize.** Sort findings into Critical (blocks progression), Important (must resolve before advancing), and Minor (address when convenient or defer with explicit note).
4. **Verify each finding against the current code.** A finding that no longer applies becomes a reply, not a change.
5. **Address one at a time.** Produce a small, focused change per item. Re-verify (hand off to `verification-gate`) before moving to the next.
6. **Respond explicitly.** For each finding: accepted and addressed (with commit or change reference), pushed back (with technical reason), or deferred (with explicit rationale).

### Red-flag patterns to refuse (receiving)

- Silently applying a change without understanding why the reviewer asked for it.
- Bundling multiple review items into one change, so it becomes unclear which fix addressed which finding.
- Claiming a finding is "fixed" without re-running the proof command — route that through `verification-gate`.
- Treating reviewer authority as a substitute for technical reasoning.
