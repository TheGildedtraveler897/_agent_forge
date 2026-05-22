---
plan_id: feat-windows-vm-readiness
branch: feat/windows-vm-readiness
status: completed
created: 2026-05-22T17:15:00Z
last_updated: 2026-05-22T17:45:00Z
spec_ref: null
task_count: 6
execution_mode: sequential
approved_at: 2026-05-22T17:15:00Z
approved_by: operator
ship_target: NRC clean-slate bundle, Monday 2026-05-25
title: Windows VM Deploy-Readiness Test (Track I)
parent_plan: ~/.claude/plans/yeah-do-the-final-dapper-creek.md
---

# Plan: Windows VM Deploy-Readiness Test (Track I)

Extract of Track I from the parent sprint plan. Status `in-progress` because the audit (I-1) and the fixes (I-2) ran in this session; the VM smoke test (I-4) is handed off to the operator with a documented verification checklist.

## Context

NRC coworkers run native Windows Claude Code (WSL blocked on the NRC network). This is the final readiness pass before the Monday 2026-05-25 ship.

## Audit findings (I-1)

Punch list from the portability audit:

- **P0** — `global-mcp.json` `forge-factory` server used `sh -c "exec python3 ..."`. No `sh` on native Windows. **Fixed in I-2.**
- **P0** — `policies/hooks.json` uses `~/Projects/` paths. All three host CLIs expand `~` at hook invocation time on Windows (documented behavior). **No action; verified via host CLI docs.**
- **P0** — `bootstrap-project.sh` uses `ln -sfn` (symlinks). `bootstrap-project.ps1` already uses plain-file stubs for Windows. **No action; .ps1 path is correct for Windows.**
- **P1** — No `.gitattributes` enforcing line endings. **Fixed in I-2.**
- **P1/P2** — Various minor polish items. **Deferred to future sprint or no action.**

## Tasks completed

### I-2. P0 fixes
- `global-mcp.json` transport: `sh -c "exec python3 ..."` → `python3 ${HOME}/.../forge_factory_server.py`. Direct invocation, no shell wrapper.
- `scripts/omni_factory.py:_expand_transport_paths` added. Expands `${HOME}`, `$HOME`, and `~` in transport `command`, `args`, and `cwd` at render time via `os.path.expandvars` + `os.path.expanduser`. Called from `normalize_mcp_server`.
- `.gitattributes` at repo root enforces `*.sh/*.py/*.json/*.toml/*.yml/*.md` as `eol=lf` and `*.ps1/*.psm1/*.cmd/*.bat` as `eol=crlf`. Archive types marked binary.

### I-3. Demo path doc
- `docs/DEMO_PATH.md` created. Six-step scripted walkthrough referenced from `BUNDLE_README.md`. Platform-aware (Linux/macOS/PowerShell). Read-only except where explicitly noted. Hits the "amazes you" payoff: same canonical skill, three host-native shapes, one safety policy.

### I-5. Lessons captured
- `docs/LESSONS_LEARNED.md` gained two active entries:
  - `MCP stdio transport must not use sh-c on Windows` — the root cause and the architectural fix.
  - `Line endings must be platform-specific by file type` — why `.gitattributes` is now repo policy.
- And one promoted entry retrospectively confirming the Track F plan-persistence layer worked under three real merges.

## Tasks deferred to operator handoff

### I-4. Smoke test on a Windows VM (operator-gated)
This session has no Windows VM access. Handoff checklist for the operator:

1. Boot a fresh Windows 10 or 11 VM with Python 3.10+ and Git installed.
2. Copy or download the latest bundle from `exports/agent-forge-suitcase-<timestamp>.zip`.
3. `Expand-Archive` the zip into a working directory.
4. In PowerShell: `pwsh -File .\_agent_forge\scripts\deploy-factory.ps1`.
5. Run `python .\_agent_forge\skills\global\onboarding-guide\onboard.py tour` — answer the experience/role prompts and walk through all six sections.
6. Run `python .\_agent_forge\skills\global\onboarding-guide\onboard.py check` — confirm probes return green or yellow (red on host CLIs is expected if the host CLIs aren't installed yet).
7. If Claude Code is installed: open a session in a governed project and confirm slash commands like `/onboarding-guide tour` resolve.
8. Walk through `docs/DEMO_PATH.md` end-to-end. Note any step that needs clarification.

Findings from this smoke test should be appended to `docs/LESSONS_LEARNED.md` as a new entry.

### I-6. Final NRC bundle re-export (after I-4 passes)
- `bash scripts/factory-export.sh --mode onboarding`
- COI scrub grep on the bundle returns zero matches.
- Confirm `BUNDLE_README.md`, `START_HERE.txt`, and `MANIFEST.json` are present at the bundle root.
- Confirm `_agent_forge/docs/DEMO_PATH.md` exists in the bundle.

## Verification

- `python3 scripts/verify-agent-forge.py` exits 0 with zero `[FAIL]` and zero `[WARN]` after every I-2 change.
- The MCP canonical now invokes Python directly; no `sh` reference remains in `global-mcp.json`.
- The renderer expansion path is exercised at every sync (next operator on Windows will validate end-to-end).

## Acceptance

- [x] I-1 audit completed via portability-audit subagent; punch list captured above
- [x] I-2 P0 fixes applied (MCP transport portable, .gitattributes added)
- [x] I-3 demo path doc written
- [x] I-5 lessons captured
- [ ] I-4 Windows VM smoke test — operator handoff
- [ ] I-6 final bundle re-export — gated on I-4
