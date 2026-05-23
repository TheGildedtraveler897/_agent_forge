# Agent Forge CONOPS
Last updated: 2026-04-28 (RC milestone — doctrine promotion pass)

## Mission

Operate `_agent_forge` as the canonical governance factory for portable Claude, Codex, Gemini, and MCP-based project work under `~/Projects`.

## Why Omni-Factory

The old model spread truth across `SKILL.md`, `registry.json`, and hand-authored Claude adapters. That made the repo Claude-heavy, Codex-partial, Gemini-light, and brittle to update. Omni-factory collapses capability, team, and MCP changes into one canonical authoring surface each and generates host-native delivery outward.

## Canonical Source-Of-Truth Rules

- Capabilities are authored in `skills/**/SKILL.md`.
- Governed project expectations are authored in `projects.json`.
- Teams are authored in `teams/*.json`.
- MCP servers are authored in `global-mcp.json`.
- Hook policy is authored in `policies/hooks.json`.
- Universal cross-host memory layer (sections, retention, secrets policy) is authored in `policies/memory.json`. Renderers translate it into `<project>/MEMORY.md` and `<project>/.forge_state/` for every governed project.
- `registry.json` is generated compatibility output, not an authoring surface.

## Capability Model

Each capability lives in its own skill directory with one `SKILL.md`. Frontmatter now carries the host-agnostic metadata needed to decide:

- workflow vs expert behavior
- project delivery targets
- host delivery targets
- command naming overrides
- Codex sandbox defaults
- MCP dependencies

The skill body remains the durable instruction contract.

## Authoring Pattern: Policy + Renderers + Capability

New cross-host primitives follow a five-step rhythm. The pattern is load-bearing as of the RC milestone, having shipped clean across hooks (2026-04-24), the universal state layer (2026-04-25), the memory bridge (2026-04-27), MCP namespace prefixing (2026-04-27), and the user-prompt advisory (2026-04-28).

1. **Canonical schema** in `policies/<name>.json` (or `global-mcp.json` for MCP). Versioned. Sections, retention, trust posture, and `targets` are first-class fields.
2. **Three host renderers** in `scripts/omni_factory.py` — one per host. Curated allow-lists translate canonical names to native names. `targets: [...]` controls which hosts receive a record; renderers drop records whose canonical event aliases to `None` for a given host.
3. **Verifier extension** in `scripts/verify-agent-forge.py` — schema validation plus on-disk evidence checks.
4. **Triad validator extension** in `scripts/validate-triad-runtime.py` — per-host surface check that derives expected native keys or aliases from every active record. Pass requires reachable rendered surface, not just JSON parse.
5. **Capability skill** under `skills/global/<name>/` that exercises the layer end-to-end. One skill, one purpose; do not bolt new responsibilities onto existing skills.

Cross-host parity is enforced at the alias / event-key boundary, not by pretending one literal name renders identically on all hosts. When a host lacks an equivalent native primitive, exclude it explicitly via `targets` and record the exclusion in `docs/LESSONS_LEARNED.md` so the next operator re-verifies against current host CLI release notes.

## Team Model

Teams remain portable JSON manifests. They describe role contracts, collapse/escalation rules, and host mapping hints. Team manifests are still conceptual rather than executable orchestration plans.

## Host Delivery Surfaces

Claude:

- `~/.claude/agents`
- `~/.claude/commands`
- `~/.claude/skills`
- `<project>/.claude/agents`
- `<project>/.claude/commands`
- `<project>/.claude/skills`
- `<project>/.mcp.json`

Codex:

- `~/.agents/skills`
- `<project>/.agents/skills`
- `<project>/.codex/agents`
- `<project>/.codex/config.toml`
- `<project>/.codex/hooks.json`

Gemini:

- `~/.gemini/agents`
- `~/.gemini/commands`
- `~/.agents/skills`
- `~/.gemini/GEMINI.md`
- `<project>/GEMINI.md`
- `<project>/.gemini/agents`
- `<project>/.gemini/commands`
- `<project>/.gemini/skills`
- `<project>/.gemini/settings.json`

### Native vs Sidecar Surfaces

Not every host exposes equivalent native primitives. The factory uses native paths where they exist and clearly-named sidecars where they don't. Bridge surfaces in particular split this way:

- **Native** (the host CLI auto-loads these): Claude `~/.claude/projects/<encoded>/memory/MEMORY.md` (true machine-local auto memory); Claude/Gemini `CLAUDE.md` / `GEMINI.md` boot files via hierarchical walk; Codex `AGENTS.md` auto-load.
- **Sidecar** (canonical surface that the host does not auto-load, but is governed in lockstep with the native surface): Codex `<project>/.codex/memory/AGENTS_MEMORY.md`; Gemini `<project>/.gemini/memory/MEMORY.md`. These are bridge-evidence files, not claims of native auto-loading.

Do not fake parity. When a host lacks a stable native target, validate the sidecar as bridge evidence and document the conservatism rather than claiming equivalence.

## Hook Governance

`policies/hooks.json` (schema v3) is the canonical authoring surface for hooks across Claude, Codex, and Gemini. The seeded `pre-tool-execution-guardian` is the universal pre-tool veto; subsequent records have shipped for memory bridge lifecycle and the user-prompt advisory.

- The schema supports five handler types (`command`, `http`, `mcp_tool`, `prompt`, `agent`); only command handlers are currently live across all three hosts.
- Canonical events translate to host-native event names through a curated allow-list in `scripts/omni_factory.py:_EVENT_ALIASES`. Drift in this allow-list is a silent-correctness class: surface JSON parse alone does not catch it, which is why `validate-triad-runtime.py` derives expected native event keys from every active record.
- A canonical event whose alias is `None` for a given host is dropped by that host's renderer; the record's `targets` array must reflect the same exclusion explicitly so intent is documented.

Full rendering rules, the canonical event translation table, and the add-a-hook workflow live in `docs/HOST_INTEGRATIONS.md` §Unified Hook Lifecycle.

## Universal State Layer And Memory Bridge

`policies/memory.json` (schema v2) authors the cross-host session-state layer. Renderers compile its sections into a per-project `MEMORY.md` plus a sibling `.forge_state/` directory containing manifest, archivist log, bridge state, and bridge log.

- `<project>/MEMORY.md` is the canonical session-state file. It is the only rewriteable surface in the universal state layer, owned by the `memory-archivist` skill; never edit anchor lines by hand.
- The bridge synchronizes canonical `MEMORY.md` to host-local memory targets via async session lifecycle hooks (`session_start` outbound, `stop` / `SessionEnd` inbound). Inbound imports re-apply the secrets-deny policy and append through the archivist.
- Bridge targets follow the native-vs-sidecar split above. The validator records `memory_pass` (universal layer reachable) and `bridge_pass` (host-local target written and hash-recorded) as separate gates.

Full schema, rendered surface paths, and the add-or-remove-a-section workflow live in `docs/HOST_INTEGRATIONS.md` §Universal State Layer.

## Knowledge Anchor

`docs/LESSONS_LEARNED.md` is the append-first knowledge ledger for validated workarounds, host quirks, and promotion candidates.

- Claude and Gemini load it through thin host boot files with native imports.
- Codex reaches it through `AGENTS.md`, generated agent instructions, and runtime-validation prompts.
- Harvesters append normalized entries there first; doctrine files only change when a lesson is broad enough to promote.

## Knowledge Distillation (Bounded Decay)

Append-first ledgers grow unbounded over time. Auto-loaded knowledge files (`docs/LESSONS_LEARNED.md`, `docs/HANDOFF.md`) need a paired bounded-decay pass so their session-load footprint stays small while wisdom is preserved verbatim.

`policies/distillation.json` (schema v1) authors the retention contract. Two skills implement it:

- `lesson-distiller` archives `Status: promoted` entries from the lesson ledger to `docs/archive/LESSONS_PROMOTED.md`, replacing each in the main file with a one-line index pointer. The integrity gate is **promotion-claim verification**: every backtick-quoted file path in the entry's promotion parenthetical must resolve on disk. If verification fails, the entry stays in the main ledger and is reported as a flag.
- `handoff-archiver` moves older `### Sprint:` sections from `docs/HANDOFF.md` to `docs/archive/SPRINTS.md`, leaving a compact summary table at the top of `## What Changed`. The latest N (default 1) sprints stay; operator-state sections (`## Current State`, `## Remaining Weaknesses`, `## Next Evolution`, `## Final Verdict`) are never archived.

The validator records `distillation_pass` per host. Pass requires policy parses, all targets exist, no auto-loaded ledger exceeds `session_load_thresholds.fail_at_bytes`, and every one-line index pointer resolves to an entry in the corresponding archive file. Distillation cadence binds to RC/milestone events via the `branch-finisher` skill; both skills require `--yes` to apply changes (dry-run otherwise).

This is the bounded-decay counterpart to append-first: the harvester captures, the archivist appends, and the distiller compacts once doctrine has absorbed the lesson.

## Unified MCP Governance

`global-mcp.json` is the only place shared MCP servers are declared. The sync engine translates those declarations into:

- Claude project `.mcp.json`
- Codex `.codex/config.toml`
- Gemini `.gemini/settings.json`

The file now uses schema v2 and includes the seeded local stdio `forge-factory` server. Canonical records carry semantic prefixes, host-safe aliases, transport/auth/trust metadata, project routing, and tool filters. The runtime gate validates MCP by checking rendered host config plus a direct stdio `tools/list` smoke; host-native MCP management UIs are useful spot checks but are not the canonical proof surface.

## Plan Persistence Layer

`execution-planner` writes its output to `docs/plans/<branch-slug>.md` with frontmatter that tracks plan status across the approval and execution lifecycle. This is the durable artifact that enables multi-agent plan continuity: a Claude session can produce a plan, glitch, and a peer Codex or Gemini agent can pick up from the on-disk file without losing the iteration context that produced it.

The layer is intentionally lightweight. There is no `policies/plans.json`, no renderer pipeline, no validator extension. It's project-governance convention enforced by the relevant skills, not a host-rendered primitive. Hosts (Claude, Codex, Gemini) do not have native plan formats; only skills (`execution-planner`, `tdd-engineer`, `subagent-dispatcher`, `branch-finisher`) read plan files. So the omni-factory five-step pattern does not apply.

### Three-Tier State Model

- **Plan file** (`docs/plans/<branch-slug>.md`) — Full task breakdown with status frontmatter. Committed with the branch. Never auto-loaded by any host.
- **MEMORY.md pointer** — One-line entry in the `active_tasks` section. Auto-loaded by all three hosts on session start via the memory bridge. Approximately 100 bytes; bounded.
- **Continuity cursor** (`dev/active/<slug>/cursor.json`) — Per-task position state, managed by `scripts/continuity_cursor.py`. Created only when plan status transitions to `approved` (cursor state implies execution intent).

### Status Lifecycle

```
awaiting-approval → approved → in-progress → completed
                  ↓
              superseded   (rejected or re-planned)
```

Transitions are driven by skills, not by hosts:
- `execution-planner` writes `awaiting-approval`; advances to `approved` or `superseded` at the human gate.
- `tdd-engineer` (and `subagent-dispatcher`) advance `approved → in-progress` on first task start.
- `branch-finisher` advances `in-progress → completed` on successful merge, then archives the plan.

### Cleanup Policy

`branch-finisher` archives the plan file to `docs/archive/PLANS_COMPLETED.md` on merge (one-line summary per plan) and deletes the active file. One plan per branch maximum; re-planning the same branch overwrites the file. There is no `docs/plans/.history/` directory — the git log is the iteration history.

Stale plans (orphaned by deleted branches) are flagged by `scripts/verify-agent-forge.py` as warnings, not failures. Operator decides whether to mark `superseded`, archive, or delete.

### Token Hygiene

Plan files are never auto-loaded. Only the `MEMORY.md` pointer (~100 bytes) loads on session start. Agents read the full plan on demand when executing or handing off. This keeps the working context lean while the durable artifact remains reachable to any peer agent on any host.

### Coexistence With Existing Primitives

The plan persistence layer does not replace `dev/active/<slug>/cursor.json` — the cursor remains the per-task continuity surface, but only for approved plans. The plan file is upstream of the cursor: cursor creation is gated on plan approval, and cursor deletion is part of `branch-finisher` cleanup. `MEMORY.md active_tasks` is the cross-host pointer of record; never write plan content into `MEMORY.md` itself.

## Bootstrap And Sync Flow

1. `bootstrap-project.sh` creates the thinnest complete governed project scaffold.
2. The bootstrap immediately runs Claude, Codex, and Gemini syncs.
3. `scripts/omni_factory.py` discovers canonical sources and renders host-native surfaces.
4. `verify-agent-forge.py` validates canonical coherence and governed project expectations.

## Runtime Validation Matrix

`runtime/validation-matrix.json` is the tracked coverage ledger for:

- Claude user and project surfaces
- Codex project skills, agents, config, and runtime execution
- Gemini user and project surfaces
- project bootstrap and workstation bootstrap paths

It is a planning and coverage artifact, not a session log.

## Eval Scorecards

`evals/scorecard.schema.json` defines the reusable evaluation contract for instruction load, discovery, runtime safety, MCP readiness, portability, doctrine alignment, and operator usability.

## Security, Trust, And Secrets

- Never commit `.env` or auth state.
- MCP secrets must flow through environment variables, not repo-tracked literals.
- User-home configs should only be touched when canonical governance actually declares shared servers.
- Project-local surfaces take precedence over user-global convenience overlays.

## Migration And Compatibility Notes

- `registry.json` remains for compatibility, but it is derived from canonical sources.
- Secondary docs can be renamed to host-agnostic names without affecting host-native boot behavior.
- Existing governed projects are not all migrated yet to the new Gemini and project-first Codex layout; the factory now has the machinery to do that safely.
