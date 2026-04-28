# Next Agent Prompt

Use this prompt to continue the `_agent_forge` Pathfinder roadmap pass in Claude, Codex, or Gemini without relying on prior chat history.

```text
You are continuing a paired-sprint Pathfinder roadmap pass under `~/Projects/_agent_forge`.

Read first, in this order:
1. ~/Projects/AGENTS.md
2. ~/Projects/_agent_forge/AGENTS.md
3. ~/Projects/_agent_forge/docs/CONOPS.md
4. ~/Projects/_agent_forge/docs/HANDOFF.md
5. ~/Projects/_agent_forge/docs/LESSONS_LEARNED.md
6. ~/Projects/_agent_forge/docs/HOST_INTEGRATIONS.md
7. ~/Projects/_agent_forge/docs/TRIAD_RUNTIME_VALIDATION.md
8. ~/Projects/_agent_forge/docs/PATHFINDER_ROADMAP.md

Current state (2026-04-28, Release Candidate):
- The omni-factory engine is canonical. `scripts/omni_factory.py` generates Claude / Codex / Gemini surfaces from `skills/**/SKILL.md`, `teams/*.json`, `projects.json`, `global-mcp.json`, `policies/hooks.json`, and `policies/memory.json`.
- `docs/LESSONS_LEARNED.md` is the canonical knowledge anchor; both `CLAUDE.md` and `GEMINI.md` import it natively, Codex reaches it via `AGENTS.md`. Triaged 2026-04-28: 9 of 16 entries promoted, 7 active, 0 superseded.
- `<project>/MEMORY.md` is the universal cross-host session-state layer. Use the `memory-archivist` skill (`skills/global/memory-archivist/archivist.py`) to append entries; never edit anchor lines by hand.
- `memory-bridge` synchronizes canonical `MEMORY.md` to host-local targets. Claude uses its true machine-local auto-memory path; Codex and Gemini use explicit project sidecars because no equivalent stable project fact-memory primitive is exposed.
- `global-mcp.json` v2 is live with the seeded local stdio `forge-factory` server. MCP correctness is validated through rendered host aliases plus direct stdio `tools/list`, not by assuming host MCP management UIs are equivalent.
- `scripts/validate-triad-runtime.py --project <name>` is the mandatory final gate after any canonical change. It probes Claude / Codex / Gemini live CLIs, escalates to filesystem evidence on Codex sandbox blocks, and gates overall pass on skill enumeration, hook surface, memory surface, bridge surface, and MCP surface presence.
- **Sprint 5 / RC milestone shipped 2026-04-28** (SOTA-2026 overhaul + lessons-ledger triage). Two new global skills (`token-optimizer` and `prompt-auto-activator`); first cross-host record bound to canonical event `user_prompt_submit` (Claude + Codex; Gemini alias is `None` — re-verify against current Gemini CLI release notes before extending targets); checkpoint discipline added to `context-engineer` and `execution-planner`. Evidence: `runtime/validation/triad/20260428-190104/summary.json` — `overall pass=true`, Claude `cli` 33/33, Codex `filesystem-escalated` 33/33 (`sandbox_blocked: true`), Gemini `filesystem` 32/32 (one fewer, as expected — `prompt-auto-activator` excludes Gemini).
- Pathfinder Architectural Upgrade #2 + Capability #3 shipped 2026-04-24 (unified hook lifecycle + telemetry-guardian).
- Pathfinder Architectural Upgrade #1 + Capability #1 shipped 2026-04-25 (universal state layer + memory-archivist).
- Pathfinder Architectural Upgrade #1 extension + Capability #2 shipped 2026-04-27 (cross-host memory bridge).
- Pathfinder Architectural Upgrade #3 shipped 2026-04-27 (MCP namespace prefixing and routing).
- Codex sandbox markers in `host_sandbox_blocked()` were expanded on 2026-04-25 to recognize newer error wording; if Codex changes its error output again, add the new phrase to the marker list rather than weakening the validator.

Pathfinder roadmap status:
- Architectural Upgrade #1 (Universal State Layer + Memory Bridge) — shipped 2026-04-25 and extended 2026-04-27.
- Architectural Upgrade #2 (Unified Hook Lifecycle) — shipped 2026-04-24 and hardened through 2026-04-28 (now exercises two canonical events: `pre_tool_use` and `user_prompt_submit`).
- Architectural Upgrade #3 (MCP Namespace Prefixing & Routing) — shipped 2026-04-27.
- Architectural Upgrade #4 (Continuous Evolution / Anti-Rot) — not started; depends on `routine-auditor`.
- Capability #1 (`memory-archivist`) — shipped 2026-04-25.
- Capability #2 (`memory-bridge`) — shipped 2026-04-27.
- Capability #3 (`telemetry-guardian`) — shipped 2026-04-24.
- SOTA-2026 set: `token-optimizer`, `prompt-auto-activator`, checkpoint discipline — shipped 2026-04-28.
- Capability B3 (`cost-warden`) — not started.
- Capability B4 (`forge-shell`) — not started.
- Capability B5 (`routine-auditor`) — not started.
- Later capabilities (`router-overseer`, `auto-loop`, `wiki-compiler`, `crew-director`, `a2a-bridge`) — not started.

Recommended next pair (operator-stated intent — OSS extraction): extract `obra/superpowers`, `gsd-build/get-shit-done`, and the Reddit "Get Shit Done" framework as native skills under canonical Omni-Factory governance. Per the 2026-04-23 PROMOTED lesson "Assimilate Workflow Discipline Natively", methodology is the asset; do not take plugin dependencies. Process: inventory each source for unique methodology that is not already covered by the existing 8-skill workflow chain; author each new methodology as a discrete `skills/global/<name>/SKILL.md` with canonical frontmatter; run the proven sprint pattern (canonical layer → renderers → verifier extension → triad gate → lesson ledger entry).

Alternative next pair (if operator pivots back to Pathfinder roadmap): Architectural #4 + Capability B3 (audit-grade orchestration log + cost-warden), matching `docs/PATHFINDER_ROADMAP.md`.

Your mission, if picking up this thread:
1. Confirm current state with read-only inspection (`git status`, run `python3 scripts/verify-agent-forge.py` and `python3 scripts/validate-triad-runtime.py --project jarvis`; both must already be green).
2. If any audit-polish work is still uncommitted, preserve it as one cleanup commit before starting new feature work.
3. Implement the next roadmap pair using the doctrine in `AGENTS.md` (canonical first, renderers second, verifier extension, triad validator extension, lesson ledger entry).
4. Do not reinvent the propagation default (global skills omitting `delivery_projects` already mirror to all governed projects).
5. Do not silently rewrite `AGENTS.md` or `docs/CONOPS.md` to harvest lessons; append to `docs/LESSONS_LEARNED.md` first.
6. Do not bypass the guardian itself (`AGENT_FORGE_GUARDIAN=off` is auditable but signals you're skipping a designed gate).
7. Update `docs/HANDOFF.md` only after the next pair is genuinely shipped and triad-green.

Specific constraints:
- Work in `_agent_forge` first; sync outward. Treat governed projects under `projects.json` as delivery targets, not refactor targets.
- Do not rename native boot files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`).
- Do not weaken the triad validator. Sandbox-blocked Codex passes only when paired with filesystem evidence and `sandbox_blocked: true`.
- Prefer sandbox-compatible fixes over bypasses.

Useful files and artifacts:
- `scripts/omni_factory.py` (canonical generator; `_hooks_for_host`, `_EVENT_ALIASES`, host-specific renderers)
- `scripts/validate-triad-runtime.py` (`hook_surface_for`, `memory_surface_for`, `memory_bridge_for`, and `mcp_surface_for` are the patterns to copy when adding new surface checks)
- `policies/hooks.json`, `policies/memory.json`, and `global-mcp.json` (current schema examples)
- `skills/global/telemetry-guardian/`, `skills/global/memory-bridge/`, and `scripts/mcp/forge_factory_server.py` (reference implementations for skills/servers that exercise a new policy layer)
- `runtime/validation-matrix.json` (triad coverage ledger)
- `runtime/validation/triad/20260428-190104/summary.json` (latest RC green proof artifact, Sprint 5)
- `runtime/validation/triad/20260427-234006/summary.json` (Sprint 4 MCP green proof, retained for diff)
- `docs/specs/2026-04-27-sota-2026-overhaul.md` (Sprint 5 spec — example of archived relayed brief)
- `docs/plans/2026-04-27-sota-2026-overhaul.md` (Sprint 5 micro-plan — example of execution-planner output shape)
- `skills/global/token-optimizer/SKILL.md` and `skills/global/prompt-auto-activator/SKILL.md` (most recent skill authorings; canonical frontmatter examples)

Desired final output:
- confirmed working surfaces per host
- new lesson ledger entry with concrete evidence paths
- triad validator green with any new per-host surface checks
- explicit verdict on whether the new layer is reachable at runtime, not just on disk
```
