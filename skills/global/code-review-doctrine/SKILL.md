---
name: code-review-doctrine
description: Review code changes for doctrine violations, portability regressions, hidden risk, hardcoded secrets, premature infrastructure, and over-engineered abstractions. Use when the user asks for a review or pre-commit audit.
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
