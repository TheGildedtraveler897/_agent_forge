---
description: Audit the current repo or change set for suitcase-doctrine and portability drift
argument-hint: [optional path or focus]
---

Audit this codebase or target area for portability drift.

Focus:
- hardcoded absolute paths
- machine-specific assumptions
- inline secrets or env-specific URLs
- missing env indirection
- missing bootstrap or setup guidance
- repo moves or host migration risks

Use the current project doctrine and report:
1. portability blockers
2. portability warnings
3. docs or bootstrap gaps

If useful, use this focus hint: $ARGUMENTS
