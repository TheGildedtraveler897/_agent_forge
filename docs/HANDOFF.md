# Agent Forge Handoff

Last updated: 2026-05-01 (RC Polish + audit-reconciliation sprint)

## What Changed
_Older sprints have been distilled into the archive to keep this file's session-load footprint small. Wisdom is preserved verbatim._

| Date | Sprint | Archive |
|---|---|---|
| 2026-04-28 | Sprint 5 / RC Milestone: SOTA-2026 Overhaul + Lessons-Ledger Triage (2026-04-28, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-27 | Sprint 4: MCP Namespace Prefixing & Routing (2026-04-27, Codex) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-27 | Sprint 3: Cross-Host Auto-Memory Bridge (2026-04-27, Codex) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-27 | Sprint 2: Hook Lifecycle V2 + Codex Event-Key Drift Fix (2026-04-27, Codex) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-25 | Sprint 1: Gemini Hook-Alias Hotfix + live-hook-prober (2026-04-25/26, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-25 | Workflow Discipline Post-Mortem: Stalled Tool-Result Delivery (2026-04-25, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-25 | Workflow Discipline Post-Mortem: Stalled Tool-Result Delivery (2026-04-25, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-25 | Universal State Layer + Memory Archivist (2026-04-25, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-24 | Unified Hook Lifecycle + Telemetry Guardian (2026-04-24, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-24 | Triad Runtime Validator + Global Skill Propagation Default (2026-04-24, Claude) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |
| 2026-04-23 | Omni-Factory Phase 3: Wargame, Purge, And Knowledge Anchor (2026-04-23, Codex) | [docs/archive/SPRINTS.md](docs/archive/SPRINTS.md) |

### Sprint: RC Polish + Audit-Reconciliation (2026-04-29, Claude Opus 4.7)

A polish-and-audit sprint following the RC milestone. Closed three doc-drift items, recorded two new lessons, and exercised the bootstrap-project.sh `--existing` path that had been pending operator validation.

#### Changes Made

1. **Doc reconciliation (Track C, commit `9604e74`).** `docs/PATHFINDER_ROADMAP.md` Sprint 5 row updated from "A4 + B3 Orchestration Log + Cost Warden" to "SOTA-2026 Overhaul" (the actual shipped Sprint 5); cascading renumbering for Sprints 6–11+. `docs/SPRINT_BACKLOG.md` status table updated: Sprints 3, 4, 5 marked shipped. `docs/TECH_DEBT.md` adds Sprint 5 + lessons-ledger triage to "Recently Resolved" and removes the now-completed ledger-triage item from "Follow-On Work"; header refreshed to RC milestone.
2. **`feat/onboarding-guide` branch deleted.** Was 0 commits ahead, 2 behind master. Work fully integrated via commit `2a573a6` ("feat: onboarding-guide build-out"). Used `git branch -d` (safe variant) which confirmed integration before deleting.
3. **Track B3: `dev/active/` cleanup reference added to `branch-finisher`.** Step 5 — Cleanup now explicitly names `dev/active/<slug>/` deletion at task close, closing the lifecycle loop documented in `execution-planner` § Checkpoint Discipline.
4. **Track B1: defensive Codex sandbox marker added.** `host_sandbox_blocked()` in `validate-triad-runtime.py` gains `"Codex's Linux sandbox uses bubblewrap"` as a stable warning-header detector. The current marker list correctly caught Codex v0.125.0's bwrap blocker on the 2026-04-28 run; the new marker is preventive maintenance against future wording drift in the rest of the sentence.
5. **Track B2: bootstrap-project.sh `--existing` exercised against a fake project.** Test artifact `~/Projects/bootstrap-test-existing/` (cleaned up after) confirmed the script's `--existing` mode unconditionally overwrites `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`. Custom files (e.g. `src/main.py`) preserved correctly. This is a real footgun for any operator running `--existing` against a curated tree; recorded as 2026-04-29 lesson "bootstrap-project.sh --existing Unconditionally Overwrites Governance Docs".
6. **Two new lessons recorded.** 2026-04-29 entries added to `docs/LESSONS_LEARNED.md`: (a) the bootstrap finding above, with promotion targets in the script and the operator runbook; (b) the audit-reconciliation pattern that caught real sprint-numbering drift one day after the RC milestone. Header counts now 15 promoted, 3 active, 0 superseded.
7. **Track A (watchdog activation) deferred.** Operator-gated on GitHub repo creation. The watchdog routine spec at `docs/TECH_DEBT.md:44-126` is ready to schedule once the operator pushes `_agent_forge` to a GitHub remote.

Evidence:
- Commit `9604e74` "Reconcile sprint docs with shipped RC state" (Track C).
- Verifier: `python3 scripts/verify-agent-forge.py` exit 0.
- Tests: `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge tests.test_mcp_namespace -v` 17 OK.
- Triad runtime artifact: `runtime/validation/triad/20260429-223331/summary.json` (`overall pass=true`, Claude `cli` 33/33, Codex `filesystem-escalated` 33/33 with `sandbox_blocked: true`, Gemini `filesystem` 32/32).
- Bootstrap test artifact captured md5 deltas before cleanup.

## Current State

- **Milestone:** Release Candidate (2026-04-28). All shippable backlog cleared; only platform-blocked items remain (see below).
- **Registry:** generated compatibility artifact derived from canonical sources; refreshed 2026-04-28.
- **Capabilities:** 30 canonical global skills with host-agnostic metadata. Sprint 5 added `token-optimizer` and `prompt-auto-activator`.
- **Teams:** canonical team manifests, with improvement-team now including lesson harvesting and memory-archivist.
- **Hosts:** Claude, Codex, and Gemini delivery all wired through one sync engine.
- **Knowledge anchor:** `docs/LESSONS_LEARNED.md` holds durable lessons; 9 of 16 entries promoted, 7 remain active.
- **Hooks:** four active cross-host records (`pre-tool-execution-guardian`, six `memory-bridge` per-host records, and `prompt-auto-activator`). Two canonical events exercised: `pre_tool_use` (all hosts), `user_prompt_submit` (Claude+Codex only). `session_start` and `stop` carry the memory-bridge records.
- **MCP:** canonical governance layer is live with one seeded shared stdio server (`forge-factory`) and host-safe alias rendering.
- **Validation:** structural verifier green; triad validation records `hook_pass`, `memory_pass`, `bridge_pass`, and `mcp_pass` per host. Latest jarvis run 33/33 Claude+Codex, 32/32 Gemini (correct — `prompt-auto-activator` excludes Gemini).
- **Suitcase status:** export/deploy path present and host-agnostic; not yet exercised on a real fresh Debian VM or macOS host.
- **Pickup path:** `docs/NEXT_AGENT_PROMPT.md` is the intended operator handoff artifact for Claude or Gemini.

## Remaining Weaknesses (Platform-Blocked)

These items are not in-engineering reach within this generation. They need real machines, kernel-level changes, upstream CLI behavior changes, or operator-driven proof runs. They are documented here so the next-evolution sprint does not block on them.

1. **Host-native MCP management UIs are not equivalent proof surfaces** — project-local `mcp get/list` behavior still differs across Claude, Codex, and Gemini even when the rendered surfaces and direct stdio smoke are correct. The triad validator's `mcp_pass` is the canonical gate; host UIs are spot-check only.
2. **No real Debian VM proof** — export/deploy/bootstrap flows still need a full fresh-machine operator run on a real VM.
3. **No real macOS proof** — MacPorts bootstrap path remains untested.
4. **Claude live hook probing is constrained by headless CLI behavior** — per the 2026-04-26 doctrine, headless `claude -p` cannot prove hooks without bypassing them or stalling on interactive permission. Real Claude live-probe needs an interactive session or the `forge-shell` capability (post-RC roadmap).
5. **Gemini live hook probing is opt-in** — `--probe-invocations` fires actual CLI tool calls and is operator-driven, not a default-on triad gate.
6. **This machine has a Codex sandbox blocker** — `bwrap: loopback: Failed RTM_NEWADDR` prevents Codex from inspecting local shell/file surfaces. The triad validator escalates to filesystem evidence per the 2026-04-23 doctrine.
7. **Team manifests are still conceptual** — orchestration remains manual/operator-driven. Real team-as-runtime is a next-generation capability, not RC polish.

## Resolved Backlog Items

- ~~Content freshness~~ — audited 2026-04-28; expert skills correctly delegate to runtime web search, no embedded stale facts.
- ~~Periodic ledger triage~~ — done 2026-04-28; 9 entries promoted, 7 active, 0 superseded.

## Manual Follow-Up Items (Operator-Driven)

1. Exercise `bootstrap-project.sh --existing` against a real existing repo.
2. Run a real Debian VM proof and a real macOS proof.
3. Broaden MCP proof depth from direct stdio smoke to true host-native tool invocation parity where the CLIs expose a stable project-local MCP inspection path.
4. Resolve the Codex `bwrap` sandbox issue on this machine and rerun the strict `jarvis` probe.
5. Improve Claude and Gemini live-invocation proof depth without relying on headless CLI behavior that bypasses or stalls hooks.

## Next Evolution (Post-RC Sprint)

Extract `obra/superpowers`, `gsd-build/get-shit-done`, and the Reddit "Get Shit Done" framework as native skills under canonical Omni-Factory governance. Per the 2026-04-23 promoted lesson, methodology is the asset; do not take plugin dependencies. Native extraction preserves cross-host portability across Claude, Codex, and Gemini, which is the explicit design goal.

Scope sketch (separate clean pass, not in this RC):

1. Inventory the three sources for unique methodology that is not already in the existing 8-skill workflow chain.
2. Author each new methodology as a discrete `skills/global/<name>/SKILL.md` with canonical frontmatter.
3. Extend the validator and tests for any new canonical patterns introduced.
4. Sync to governed projects, run triad gate, ledger-triage the lessons that came out of the extraction.

## Final Verdict

**Agent Forge has reached its Release Candidate milestone.** The canonical authoring surfaces are stable, the cross-host renderer is hardened, the validation gate is multi-layered, the knowledge anchor is groomed, and the operator handoff is current. The remaining weaknesses are platform-blocked, not in-engineering reach. The factory is ready for the OSS-extraction sprint that the operator's stated end-goal requires.
