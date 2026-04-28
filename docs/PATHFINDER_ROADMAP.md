# Omni-Factory Pathfinder Roadmap

**Last regenerated:** 2026-04-28 (Stop The Line production audit polish).

## Read order

This roadmap is the **actionable plan**. It does not include sprawling research or musing. For:
- **Why** any decision was made → read `docs/PATHFINDER_LEDGER.md` (the raw research archive).
- **What** to build next → continue reading this file.
- **How** to start the next sprint → read `docs/SPRINT_BACKLOG.md` (copy-pasteable Codex execution prompts).
- **What** just shipped → read `docs/HANDOFF.md`.
- **Validated lessons** that bind future work → read `docs/LESSONS_LEARNED.md`.

The shipped-status footnotes for prior items are preserved at the bottom of this file. Everything above the footnotes is forward-looking.

---

## SOTA 2026 horizon — brief summary

Synthesized from the deep research in `docs/PATHFINDER_LEDGER.md`. Five axes the SOTA has converged on:

1. **Hooks are a 26-event lifecycle, not a single pre/post pair.** Five handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent`. `async` and `async_rewake` flags decouple from the main loop. Permission updates can be applied from a hook at runtime.
2. **Memory is two layers, native + cross-host.** Each host's auto-memory writes locally; the cross-host shared brain is built *on top of* the native layers, not in place of them.
3. **MCP namespace prefixing is canonical.** `<service>.<verb>` (e.g., `github.list_repos`). Streamable HTTP transport with bearer-token auth + per-client audit logging is now standard. Project-scoped MCP servers gated on trusted-workspace state.
4. **Multi-agent orchestration has settled into the Conductor + Swarm hybrid.** Central conductor decomposes and routes; specialized swarm workers execute in parallel; results merge back. Production-grade frameworks enforce proof-of-work + cost tracking + explainable routing + audit-grade logging.
5. **Interactive bash control beats one-shot tool use.** Persistent shell state across turns (cwd tracking, allowlist runtime validation, HITL confirm). Substrate for autonomous loops, TDD micro-runs, multi-step workflows.

**Our differentiator.** None of the Triad coding CLIs ships all five. The factory's **canonical-first omni-factory model** is unique: one schema authored once in `_agent_forge/`, three host-native renderings, runtime-validated. Where the SOTA today is "Claude does it well, Codex does part of it, Gemini does some of it", we ship "all three identically, audited, and provably reachable from each host's CLI."

---

## Architectural upgrades (A1–A7)

Each upgrade is a self-contained schema/renderer change. Detailed execution specs live in `docs/SPRINT_BACKLOG.md` for the next three; later upgrades have summary entries here that the Sprint Backlog will expand when their turn arrives.

### A1. Hook Lifecycle V2 — full 26-event coverage with handler diversity

Render every canonical hook into all 26 native event names per host. Add 5 handler types (`command`, `http`, `mcp_tool`, `prompt`, `agent`). Add `async` + `async_rewake` flags. Add `permission_updates[]` for runtime permission rule mutation.

Schema bump: `policies/hooks.json` v2 → v3.

**Status:** ✅ Shipped 2026-04-27. `policies/hooks.json` v3, Codex PascalCase event-key fix, v3 handler schema, full curated event allow-list, per-record `hook_surface_for` validation. Evidence: `runtime/validation/triad/20260427-084059/`. **Known incomplete:** non-command handler live-dispatch sentinels are not yet real cross-host proof; Codex and Gemini currently render command hooks only per current docs.

### A2. Cross-Host Auto-Memory Bridge

Bridge canonical `<project>/MEMORY.md` to host-local memory surfaces: Claude's true machine-local auto-memory index, plus Codex and Gemini project sidecars where no stable project fact-memory file exists. Outbound (canonical → host-local) injects on `SessionStart`. Inbound (host-local → canonical) harvests on `Stop` / `SessionEnd`. Append-first; `active_tasks` rewriteable through `memory-archivist`; secrets-deny re-applied at the bridge layer.

Schema additions: `policies/memory.json` gains a `bridge` block. New `<project>/.forge_state/bridge.json` for state.

**Status:** ✅ Shipped 2026-04-27. `policies/memory.json` v2, `memory-bridge` skill, host-specific async SessionStart/Stop hook records, per-project `.forge_state/bridge.json` + `bridge.log`, bridge-aware verifier, and triad `bridge_pass` gate. Evidence: `runtime/validation/triad/20260427-203021/`.

### A3. MCP Namespace Prefixing & Routing — canonical-first

Render canonical `policies/mcp.json` server records as namespaced tools (`forge.<service>.<tool>`) into all three host configs. Trust-gated project-scoped servers. Bearer-token + audit-log discipline for streamable-HTTP transport.

Schema bump: `global-mcp.json` v2.

**Status:** ✅ Shipped 2026-04-27. `global-mcp.json` v2, seeded local stdio `forge-factory` server, `trusted_workspace` project gating, host-safe server aliases, verifier MCP inventory checks, and triad `mcp_pass` gate. Evidence: `runtime/validation/triad/20260427-234006/`. **Known limitation:** host MCP management subcommands are not equivalent proof surfaces; `mcp_pass` currently means rendered surface + direct stdio `tools/list` smoke, not universal `mcp get/list` parity.

### A4. Audit-Grade Orchestration Log

Per-session orchestration log capturing routing decisions, model tier requested vs used, token spend, artifacts produced, verification results, cost roll-up. JSONL append-only at `<project>/.forge_state/orchestration.log`. Cost budget enforcement at session and subagent granularity.

Schema additions: `policies/orchestration.json` v1.

**Status:** Sprint 5+ (post-MCP-prefix). Depends on A1 (Subagent / Task lifecycle hooks).

### A5. The `forge-shell` Persistent-Bash Primitive

Long-lived subprocess wrapping `/bin/bash` with cwd tracking via `{cmd};echo __END__;pwd` delimiter. Allowlist runtime validation. HITL approval gated by env var. State persisted in `<project>/.forge_state/shell-<session>.json`. Telemetry-guardian still runs as the deny half.

Surface: `forge-shell run/state/reset/allowlist` subcommands.

**Status:** Sprint 6+. Depends on A1 + A4. Unlocks `auto-loop`, real Claude live-probing, multi-step TDD cycles.

### A6. Continuous Evolution / Anti-Rot — the factory governs itself

`routine-auditor` capability runs on three triggers: local schedule (cron / `/loop`), remote watchdog (post-GitHub-push), sprint-harvest re-recon. Re-validates verifier + triad + lesson-ledger freshness. Promotion of doctrine requires an `routine-auditor` clean run within prior 24 hours.

Schema additions: `policies/auditor.json` v1.

**Status:** Sprint 7+. Depends on A4 + a git remote.

### A7. Cross-Framework Interop — A2A protocol minimal compliance

Expose minimal A2A (Agent-to-Agent) endpoint so external frameworks (Google ADK, LangGraph, CrewAI, AutoGen agents) can call our skills. Skills marked `a2a_exposed: true` in frontmatter become callable.

Schema additions: `policies/a2a.json`.

**Status:** Sprint 8+. Defensive + future-proofing. Defer until A4 ships so external calls land in the orchestration log.

---

## Capability backlog (B1–B12)

Skills and agents that exercise the architectural upgrades. Cross-references each architectural dependency.

| ID | Skill | Depends on | Priority | Status |
|---|---|---|---|---|
| **B1** | `live-hook-prober` | A1 | Highest | ✅ Shipped 2026-04-26 |
| **B2** | `memory-bridge` | A1 + A2 | High | ✅ Shipped 2026-04-27 |
| **B3** | `cost-warden` | A4 | High | Sprint 5+ |
| **B4** | `forge-shell` | A2 + telemetry-guardian | High | Sprint 6+ |
| **B5** | `routine-auditor` | A4 + A6 | High | Sprint 7+ |
| **B6** | `router-overseer` | A4 + B3 | High | Sprint 8+ |
| **B7** | `auto-loop` | B4 + A4 + B3 | Medium-high | Sprint 9+ |
| **B8** | `wiki-compiler` | B4 + A2 | Medium | Sprint 10+ |
| **B9** | `crew-director` | A1–A6 + B3 + B5 + B6 + B7 | Medium-low | Endgame |
| **B10** | `path-scoped-rules` | none structural | Medium | Whenever; small scope |
| **B11** | `host-quirk-translator` | A4 + A6 | Medium | Sprint 7+ |
| **B12** | `a2a-bridge` | A7 | Low | Defensive; defer |
| **B13** | `onboarding-guide` | none structural | Operator-facing | ✅ Shipped 2026-04-27 (side branch `feat/onboarding-guide`) |

### B13. `onboarding-guide` — ✅ Shipped 2026-04-27

Operator-facing guided tour for first-time operators. Lives at `skills/global/onboarding-guide/`. Three modes via `onboard.py`: `tour` (interactive five-section walkthrough with experience-aware adaptations), `tour --quick` (non-interactive 90-second summary), `check` (machine-state report), `explain <topic>` (single-concept explainer covering 12 topics including `validation-pyramid`, `governed-project`, `suitcase`, `mcp`, `hook`, `memory`, `sandbox`, `triad-validator`, `guardian`, `factory`, `skill`, `bootstrap`).

Read-only and observational. Does not modify canonical sources, host surfaces, or `bootstrap-project.sh`. Audience-tone discipline encoded in the SKILL.md (no sycophancy, no condescension, jargon-translated-on-first-use). Designed to be invoked directly by the operator after `bootstrap-project.sh`; an integration-hook seam is documented in `docs/OPERATOR_TEMPLATES.md` for a future Codex sprint to wire `bootstrap-project.sh --guided`.

Current branch state: this factory line is on `feat/onboarding-guide` with Sprint 3 and Sprint 4 work already layered on top. Finish through the normal branch-finisher path rather than treating onboarding as a separate pending side branch.

### B1. `live-hook-prober` — ✅ Shipped 2026-04-26

Surface: `bash skills/global/live-hook-prober/prober.sh --host <claude|codex|gemini> --project <root> --command <test> --expect <block|allow>`. Validator integration via `validate-triad-runtime.py --probe-invocations`.

**Status:** Three escalation modes (`sandbox_blocked`, `trust_blocked`, `headless_permission_constraint`) match the existing escalation doctrine. Live verification: Gemini probe blocked `--no-verify` for real (exit 0, `verdict: pass`, `observed: block`). Codex correctly escalated to `sandbox_blocked`. Claude correctly escalated to `headless_permission_constraint` (real Claude live-probing requires `forge-shell` from B4). **Known limitation:** do not invoke transitively through an agent harness's bash tool — leftover-subprocess-tree stalls. Run from a real terminal or as a Routine.

### B2. `memory-bridge`

Bidirectional bridge between canonical `<project>/MEMORY.md` and each host's native auto-memory. Outbound on `SessionStart`; inbound on `Stop` / `SessionEnd`. Idempotent and append-first.

Surface: hook handler, not a slash command. Visible via `<project>/.forge_state/bridge.json` + `bridge.log`.

**Status:** ✅ Shipped 2026-04-27. Surface: `bridge.py outbound|inbound|status`; state in `<project>/.forge_state/bridge.json`; audit in `bridge.log`. Codex and Gemini targets are project sidecars, not claims of native auto-memory loading.

### B3. `cost-warden`

Reads orchestration log (A4), enforces token + cost budgets at session / subagent / per-skill granularity. Three actions on cap hit: `warn`, `prompt` (HITL), `halt`. Reports cost roll-ups at end of session.

Surface: slash command `/cost`; runs as `SubagentStart` hook.

### B4. `forge-shell`

See A5. Used by `auto-loop`, `crew-director`, and any skill needing multi-turn shell state.

### B5. `routine-auditor`

See A6. Three triggers; opens local tasks / GitHub issues / lesson-ledger candidates as appropriate.

### B6. `router-overseer`

Agent-as-a-Tool dispatcher. Reads `policies/orchestration.json` `routing_decisions`, picks the right specialist (or set of specialists in parallel), records routing rationale, merges results, surfaces a single coherent answer.

Surface: `/route "<prompt>"` slash command in all three hosts.

### B7. `auto-loop`

Karpathy-autoresearch-style loop: propose → edit → run test → evaluate → ratchet. Interactive wizard at startup so non-experts define `program.md` goals + identify failing tests + set hard success metrics before iteration starts.

Surface: `/auto-loop init` (wizard) → `/auto-loop run --max-iterations N --cost-cap $X`.

### B8. `wiki-compiler`

Compile raw inputs (PDF API specs, large codebases, doc dumps) into structured, densely-hyperlinked Markdown that all agents read directly. End reliance on brittle RAG.

Surface: `/wiki-compile --source <path>` produces `<project>/.forge_state/wiki/`. Re-compilable on source change.

### B9. `crew-director`

Capstone swarm orchestrator. Conductor + swarm fan-out for declared multi-stage operations ("Release a new software version" → spawns `auto-loop` for tests, `wiki-compiler` for changelog, `brand-guardian` for graphics, merges results).

Surface: `/crew-direct "<high-level-goal>"`. Operator approves the plan; conductor dispatches; swarm executes; cost-warden enforces; orchestration log records every decision.

### B10. `path-scoped-rules`

Bring Claude Code's `.claude/rules/*.md` with YAML `paths:` glob to all three hosts. Renderer scopes a skill to specific file globs so its body only loads when relevant. Cuts context cost.

### B11. `host-quirk-translator`

Meta-skill that detects host-specific surface mismatches (event-name drift, sandbox-marker drift) and proposes a hotfix to `_EVENT_ALIASES` / `host_sandbox_blocked()`. Runs after `routine-auditor` weekly; generates a PR-equivalent diff.

### B12. `a2a-bridge`

Minimal-compliance A2A protocol exposure (see A7). Lets external frameworks call our skills and our skills call external A2A endpoints.

---

## Sprint sequencing

The dependency graph imposes the following order. Each sprint follows the established rhythm: canonical schema → three host renderers → skill that exercises it → triad runtime gate → lesson ledger entry.

| Sprint | Title | Key deliverables |
|---|---|---|
| **Sprint 1** | C1 Hotfix + B1 live-hook-prober | ✅ Shipped 2026-04-26 (commits `f2cea42` + `a15200f`) |
| **Sprint 2** | A1 Hook Lifecycle V2 | ✅ Shipped 2026-04-27 (`policies/hooks.json` v3 + Codex event-key fix + per-record hook surface gate) |
| **Sprint 3** | A2 + B2 Memory Bridge | ✅ Shipped 2026-04-27 (`bridge_pass` green on Claude/Codex/Gemini) |
| **Sprint 4** | A3 MCP Namespace Prefixing | ✅ Shipped 2026-04-27 (`mcp_pass` green on Claude/Codex/Gemini) |
| **Sprint 5** | SOTA-2026 Overhaul (`token-optimizer` + `prompt-auto-activator` + checkpoint discipline) | ✅ Shipped 2026-04-28 (RC milestone; first cross-host record on canonical event `user_prompt_submit`; Gemini excluded by design) |
| **Sprint 6** | A4 + B3 Orchestration Log + Cost Warden | Audit-grade per-session log + budget enforcement |
| **Sprint 7** | A5 + B4 forge-shell | Persistent bash primitive |
| **Sprint 8** | A6 + B5 routine-auditor | Self-governance |
| **Sprint 9** | B6 router-overseer | Agent-as-a-Tool dispatcher |
| **Sprint 10** | B10 path-scoped-rules + B11 host-quirk-translator | Operator quality-of-life pass |
| **Sprint 11+** | B7 + B8 + B9 + B12 (`auto-loop`, `wiki-compiler`, `crew-director`, `a2a-bridge`) | Endgame; do not start until dependencies are solid |

**Sprint 2 / 3 / 4 are detailed with copy-pasteable Codex execution prompts in `docs/SPRINT_BACKLOG.md`. Sprint 5 SOTA-2026 spec and micro-plan are archived at `docs/specs/2026-04-27-sota-2026-overhaul.md` and `docs/plans/2026-04-27-sota-2026-overhaul.md`.**

---

## Previously shipped — preserved status footnotes

**Architectural Upgrade #1 — Cross-Agent Memory Exchange.** ✅ Shipped 2026-04-25, extended 2026-04-27. `policies/memory.json` v2; `MEMORY.md` + `.forge_state/` rendered into all six governed projects; Gemini `@MEMORY.md` import; AGENTS.md Read Order entry #5 covers Claude/Codex; `memory_surface_for` and `memory_bridge_for` triad gates. Evidence: `runtime/validation/triad/20260425-174222/` and `runtime/validation/triad/20260427-203021/`.

**Architectural Upgrade #2 — Unified Hook Lifecycle.** ✅ Shipped 2026-04-24, hardened 2026-04-26 and 2026-04-27. Gemini event-name correctness BLOCKER (C1) is fixed (Sprint 1, commit `f2cea42`); `_EVENT_ALIASES["gemini"]` corrected to PascalCase per Gemini CLI v0.39. Sprint 2 then fixed Codex event-key casing to PascalCase and replaced the one-key hook surface check with per-active-record expected event-key validation. Live invocation gate via `live-hook-prober` (B1) closes vulnerability C2 for command hooks. Evidence: `runtime/validation/triad/20260424-205818/` + `runtime/validation/triad/20260426-035206/` + `runtime/validation/hook-probe/20260426-035313/gemini/` + `runtime/validation/triad/20260427-084059/`. **Still incomplete:** non-command handler live-dispatch sentinels are not yet cross-host proof; Codex and Gemini currently render command hooks only per current docs.

**Capability #1 — `memory-archivist`.** ✅ Shipped 2026-04-25. `append`/`validate`/`summary` subcommands; secrets-deny patterns; audit log; wired into `improvement-team`; now reused by `memory-bridge` inbound imports with file locking and atomic writes.

**Capability #3 — `telemetry-guardian`.** ✅ Shipped 2026-04-24. POSIX `guardian.sh`; deny-list; bypass via `AGENT_FORGE_GUARDIAN=off` logged to `~/.agent-forge/guardian.log`. **Known incomplete:** allow-list pair (Nemotron pattern); persistent-cwd; HITL confirm — all land with `forge-shell` (B4 / A5, Sprint 6).

**Capability B1 — `live-hook-prober`.** ✅ Shipped 2026-04-26 (commit `a15200f`). `SKILL.md` + `prober.sh`. Triad validator integration via `--probe-invocations`. Evidence: `runtime/validation/hook-probe/20260426-035313/gemini/` (Gemini blocked `--no-verify` for real, exit 0). **Known limitation:** do not invoke transitively through an agent harness's bash tool. See `docs/SPRINT_BACKLOG.md` for the resolution path (B4 forge-shell).
