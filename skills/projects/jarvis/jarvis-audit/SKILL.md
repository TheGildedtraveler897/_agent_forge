---
name: jarvis-audit
description: System health and dependency auditor. Ensures the Suitcase Doctrine is intact.
context_cost: medium
model_tier: any
capability_class: workflow
---

# jarvis-audit

When invoked, perform a full dependency and doctrine audit of the repo. Output a structured report, propose fixes, and wait for user approval before touching any files.

## How to invoke

```
/jarvis-audit
```

## Audit Steps

### 1. Map Python dependencies

Use the Grep tool to find all import statements in `scripts/*.py`:

- Pattern: `^import (\S+)` — captures top-level imports
- Pattern: `^from (\S+)` — captures `from X import Y` package names
- Strip submodules (e.g., `from pathlib.Path` → `pathlib`)
- Exclude stdlib modules: `sys`, `os`, `json`, `subprocess`, `pathlib`, `datetime`, `re`, `shutil`, `typing`

### 2. Map bash dependencies

Use the Grep tool to find `pip install` calls in `scripts/*.sh`:

- Pattern: `pip install (\S+)`
- Collect any packages explicitly installed in shell scripts

### 3. Load the requirements manifest

Read `docs/requirements.txt`. Parse package names by stripping version pins (e.g., `openai==1.2.3` → `openai`). Build a set of declared packages.

### 4. Check for bootstrap.sh

Use the Glob tool to check if `scripts/bootstrap.sh` exists. If absent, flag it.

### 5. Diff and report

Produce a structured report with three sections:

```
=== JARVIS AUDIT REPORT ===

[MISSING] Packages imported in code but not declared in docs/requirements.txt:
- <package>  (found in: <file>)

[UNUSED] Packages declared in docs/requirements.txt but not imported anywhere:
- <package>

[BOOTSTRAP STATUS]
- scripts/bootstrap.sh: PRESENT | ABSENT
  → If absent: propose creating a stub that runs `.venv/bin/pip install -r docs/requirements.txt`

[DOCTRINE CHECKS]
- Hardcoded absolute paths:  PASS | FAIL (list offending files)
- Hardcoded secrets/URLs:    PASS | FAIL (list offending files)
- .env committed to git:     PASS | FAIL

=== END REPORT ===
```

### 6. Propose fixes

After the report, list the exact proposed changes:

```
Proposed fixes (awaiting approval):
1. Add 'openai' to docs/requirements.txt
2. Create scripts/bootstrap.sh with venv pip install stub
3. [any other fixes]
```

### 7. Wait for approval

**Do not write any files until the user explicitly approves.** Ask:

```
Approve these changes? (yes / no / edit)
```

Only proceed if the user confirms. Apply fixes one at a time and confirm each.

## Output rules

- No fluff. Report only findings.
- Lead each finding with the file and line number where possible.
- If everything is clean: output `Doctrine aligned. Repo is healthy.`
