---
plan_id: feat-sota-2026-deep-refactor
branch: feat/sota-2026-deep-refactor
status: approved
created: 2026-05-23T00:00:00Z
last_updated: 2026-05-23T00:00:00Z
spec_ref: null
task_count: 6
execution_mode: sequential
approved_at: 2026-05-23T00:00:00Z
approved_by: operator
title: SOTA 2026 ship-prep refactor
---

# SOTA 2026 Ship-Prep Refactor

## Durable Context

The operator approved a deep refactor focused on Windows ship readiness, multi-host continuity, and SOTA 2026 documentation drift. Branch from `master`; do not base this work on `fix-windows-powershell-suitcase`, but port useful Windows fixes from commit `4cdcfa8` deliberately. The existing dirty `.forge_state/distiller.log` is unrelated and must not be committed.

## Execution Tracks

### T-01 - Windows suitcase deployment

Create a Windows-native one-shot deployment path that unblocks ZIP payloads before extraction, validates required bundle contents, recursively unblocks the extracted tree, and invokes `deploy-factory.ps1`. Add a Windows workstation bootstrap counterpart and update bundle/quickstart/demo docs.

Verification: PowerShell script text tests, `python3 -m unittest tests.test_windows_powershell_scripts`, `python3 scripts/verify-agent-forge.py`.

### T-02 - Verifier and policy cleanup

Move dormant hook examples out of live policy, warn on empty governed projects, reject legacy `hosts:` skill frontmatter, warn on stale plan files and stale MEMORY plan pointers, document hook alias intent, and distinguish triad runtime sandbox skips from validation.

Verification: focused verifier/hook tests, `python3 -m unittest tests.test_verifier_coherence tests.test_hooks_v3`, `python3 scripts/verify-agent-forge.py`.

### T-03 - Continuity cursor hardening

Add cursor checkpoint and task-complete commands. Update `tdd-engineer` to inspect checkpoint state before execution and record task commit hashes after green verification.

Verification: `python3 -m unittest tests.test_continuity_cursor`, `python3 scripts/verify-agent-forge.py`.

### T-04 - Memory bridge continuity

Add memory bridge validation, a no-fail validation hook, and outbound Active Cursor State summaries so Codex/Gemini can see resume pointers without loading full plans.

Verification: `python3 -m unittest tests.test_memory_bridge tests.test_hooks_v3`, `python3 scripts/verify-agent-forge.py`.

### T-05 - SOTA documentation refresh

Append the 2026-05-23 deep audit delta, add prompt-caching explainer content, update research docs, and re-anchor CONOPS delivery surfaces and date.

Verification: doc grep for required dated sections and primary-source links, `python3 scripts/verify-agent-forge.py`.

### T-06 - Cross-platform validation and ship artifacts

Capture Linux validation output, write Mac/Windows checklists when physical hosts are unavailable, update the validation matrix, re-export the onboarding suitcase, and add sprint lessons/handoff entries.

Verification: `python3 -m unittest`, `python3 scripts/verify-agent-forge.py`, export COI grep returns 0 matches, validation artifacts exist.

## Final Gate

Before merge: all unit tests pass, structural verifier exits 0, triad runtime runs for the first governed project if one exists, the onboarding bundle includes Windows entry points, and no personal/COI grep pattern matches the export directory.
