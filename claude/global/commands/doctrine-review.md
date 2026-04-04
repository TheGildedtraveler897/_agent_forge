---
description: Review current changes for doctrine, security, portability, and overengineering risks
argument-hint: [optional focus]
---

Review the current changes or relevant files against practical engineering doctrine.

Priorities:
- hardcoded secrets or credentials
- security regressions
- portability regressions
- risky destructive behavior
- premature infrastructure
- over-engineered abstractions with no real caller

Output findings first, ordered by severity, with file references when possible.

If no findings exist, say so clearly.

Optional focus: $ARGUMENTS
