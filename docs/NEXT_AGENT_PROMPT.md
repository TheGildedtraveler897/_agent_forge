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

Current state (2026-04-24):
- The omni-factory engine is canonical. `scripts/omni_factory.py` generates Claude / Codex / Gemini surfaces from `skills/**/SKILL.md`, `teams/*.json`, `projects.json`, `global-mcp.json`, and `policies/hooks.json`.
- `docs/LESSONS_LEARNED.md` is the canonical knowledge anchor; both `CLAUDE.md` and `GEMINI.md` import it natively, Codex reaches it via `AGENTS.md`.
- `scripts/validate-triad-runtime.py --project <name>` is the mandatory final gate after any canonical change. It probes Claude / Codex / Gemini live CLIs, escalates to filesystem evidence on Codex sandbox blocks, and now also gates overall pass on hook-surface presence.
- Pathfinder Architectural Upgrade #2 (Unified Hook Lifecycle) and Capability #3 (`telemetry-guardian`) shipped together on 2026-04-24. Evidence: `runtime/validation/triad/20260424-205818/summary.json` shows `overall_pass: true` with `hook_pass: true` on all three hosts and 27 expected skills.
- The Codex sandbox blocker on this machine (`bwrap: loopback: Failed RTM_NEWADDR`) is documented; the validator falls back to filesystem-escalated proof per the 2026-04-23 escalation lesson.

Pathfinder roadmap status:
- Architectural Upgrade #1 (Cross-Agent Memory Exchange — `MEMORY.md` Universal State Layer) — not started.
- Architectural Upgrade #2 (Unified Hook Lifecycle) — shipped 2026-04-24.
- Architectural Upgrade #3 (MCP Namespace Prefixing & Routing) — not started; `global-mcp.json` still empty.
- Architectural Upgrade #4 (Continuous Evolution / Anti-Rot) — not started; depends on `routine-auditor`.
- Capability #1 (`memory-archivist`) — not started; pairs with Architectural #1.
- Capability #2 (`router-overseer`) — not started.
- Capability #3 (`telemetry-guardian`) — shipped 2026-04-24.
- Capability #4 (`routine-auditor`) — not started.
- Capability #5 (`auto-loop`) — not started.
- Capability #6 (`wiki-compiler`) — not started.
- Capability #7 (`crew-director`) — not started.

Recommended next pair: Architectural #1 + Capability #1 (Universal State Layer + memory-archivist). The previous pair followed the same rhythm — ship one schema/protocol layer plus one skill that exercises it, validated end-to-end through the triad runtime gate.

Your mission, if picking up this thread:
1. Confirm current state with read-only inspection (`git status`, run `python3 scripts/verify-agent-forge.py` and `python3 scripts/validate-triad-runtime.py --project jarvis`; both must already be green).
2. If the unified-hook-lifecycle work is still uncommitted, preserve it as one feature commit before starting new work.
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
- `scripts/validate-triad-runtime.py` (`hook_surface_for` is the pattern to copy when adding new surface checks)
- `policies/hooks.json` (reference template for the upcoming `policies/memory.json`)
- `skills/global/telemetry-guardian/` (reference implementation for "skill that exercises a new policy layer")
- `skills/global/sprint-harvester/SKILL.md` (closest existing analogue to `memory-archivist`)
- `runtime/validation-matrix.json` (expand `triad_runtime.<project>.per_host` with `memory_pass` when adding the memory layer)
- `runtime/validation/triad/20260424-205818/summary.json` (last green proof artifact)

Desired final output:
- confirmed working surfaces per host
- new lesson ledger entry with concrete evidence paths
- triad validator green with new per-host surface checks
- explicit verdict on whether the new layer is reachable at runtime, not just on disk
```
