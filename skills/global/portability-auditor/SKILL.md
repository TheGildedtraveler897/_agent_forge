---
name: portability-auditor
description: Audit a repo, script set, or configuration for portability risks such as hardcoded paths, machine-specific assumptions, missing env indirection, and fragile host-specific behavior. Use when the user wants a suitcase-doctrine check or wants fixes for portability drift.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
delivery_projects: ["*"]
claude_command_name: portability-audit
gemini_command_name: portability-audit
---

# Portability Auditor

Audit the target for portability drift, then produce a concise fix plan or patch set.

## Core Checks

1. Hardcoded absolute paths
2. User-specific home directories
3. Host-specific mount assumptions
4. Inline credentials or inline environment-specific URLs
5. Missing usage guards in scripts that are meant to run on fresh machines
6. Setup steps that assume globally installed tools or packages without documenting them

## Workflow

1. Identify the primary runtime surfaces: scripts, configs, compose files, manifests, and docs.
2. Search for path drift:
   - `/home/`
   - `/Users/`
   - machine-specific mount points
3. Check whether secrets and endpoints are pulled from `.env` or other env-driven config.
4. Check whether the project documents required bootstrap steps and isolated dependency setup.
5. Report findings first, ordered by severity.
6. If the user wants changes, prefer the smallest set of edits that restores portability.

## Output Rules

- Lead with concrete findings.
- Tie each finding to a file and line where possible.
- Distinguish between:
  - portability blockers
  - portability warnings
  - docs gaps
- If everything is clean, say so explicitly.
