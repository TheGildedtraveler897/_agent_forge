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

Current state (2026-04-28):
- The omni-factory engine is canonical. `scripts/omni_factory.py` generates Claude / Codex / Gemini surfaces from `skills/**/SKILL.md`, `teams/*.json`, `projects.json`, `global-mcp.json`, `policies/hooks.json`, and `policies/memory.json`.
- `docs/LESSONS_LEARNED.md` is the canonical knowledge anchor; both `CLAUDE.md` and `GEMINI.md` import it natively, Codex reaches it via `AGENTS.md`.
- `<project>/MEMORY.md` is the universal cross-host session-state layer. Use the `memory-archivist` skill (`skills/global/memory-archivist/archivist.py`) to append entries; never edit anchor lines by hand.
- `memory-bridge` synchronizes canonical `MEMORY.md` to host-local targets. Claude uses its true machine-local auto-memory path; Codex and Gemini use explicit project sidecars because no equivalent stable project fact-memory primitive is exposed.
- `global-mcp.json` v2 is live with the seeded local stdio `forge-factory` server. MCP correctness is validated through rendered host aliases plus direct stdio `tools/list`, not by assuming host MCP management UIs are equivalent.
- `scripts/validate-triad-runtime.py --project <name>` is the mandatory final gate after any canonical change. It probes Claude / Codex / Gemini live CLIs, escalates to filesystem evidence on Codex sandbox blocks, and gates overall pass on skill enumeration, hook surface, memory surface, bridge surface, and MCP surface presence.
- Pathfinder Architectural Upgrade #2 + Capability #3 shipped 2026-04-24 (unified hook lifecycle + telemetry-guardian).
- Pathfinder Architectural Upgrade #1 + Capability #1 shipped 2026-04-25 (universal state layer + memory-archivist). Evidence: `runtime/validation/triad/20260425-174222/summary.json` — `overall_pass: true`, all hosts `hook_pass: true memory_pass: true`, 28 expected skills.
- Pathfinder Architectural Upgrade #1 extension + Capability #2 shipped 2026-04-27 (cross-host memory bridge). Evidence: `runtime/validation/triad/20260427-203021/summary.json`.
- Pathfinder Architectural Upgrade #3 shipped 2026-04-27 (MCP namespace prefixing and routing). Evidence: `runtime/validation/triad/20260427-234006/summary.json`.
- Codex sandbox markers in `host_sandbox_blocked()` were expanded on 2026-04-25 to recognize newer error wording; if Codex changes its error output again, add the new phrase to the marker list rather than weakening the validator.

Pathfinder roadmap status:
- Architectural Upgrade #1 (Universal State Layer + Memory Bridge) — shipped 2026-04-25 and extended 2026-04-27.
- Architectural Upgrade #2 (Unified Hook Lifecycle) — shipped 2026-04-24 and hardened through 2026-04-27.
- Architectural Upgrade #3 (MCP Namespace Prefixing & Routing) — shipped 2026-04-27.
- Architectural Upgrade #4 (Continuous Evolution / Anti-Rot) — not started; depends on `routine-auditor`.
- Capability #1 (`memory-archivist`) — shipped 2026-04-25.
- Capability #2 (`memory-bridge`) — shipped 2026-04-27.
- Capability #3 (`telemetry-guardian`) — shipped 2026-04-24.
- Capability B3 (`cost-warden`) — not started.
- Capability B4 (`forge-shell`) — not started.
- Capability B5 (`routine-auditor`) — not started.
- Later capabilities (`router-overseer`, `auto-loop`, `wiki-compiler`, `crew-director`, `a2a-bridge`) — not started.

Recommended next pair: Sprint 5, Architectural #4 + Capability B3 (audit-grade orchestration log + cost-warden), matching `docs/PATHFINDER_ROADMAP.md`. The proven pattern is: canonical schema/protocol layer, three host renderers, skill that exercises it, verifier extension, triad runtime gate, lesson ledger entry.

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
- `runtime/validation/triad/20260427-234006/summary.json` (latest Sprint 4 green proof artifact)

Desired final output:
- confirmed working surfaces per host
- new lesson ledger entry with concrete evidence paths
- triad validator green with any new per-host surface checks
- explicit verdict on whether the new layer is reachable at runtime, not just on disk
```
