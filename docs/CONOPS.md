# Agent Forge CONOPS
Last updated: 2026-04-25

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

## Team Model

Teams remain portable JSON manifests. They describe role contracts, collapse/escalation rules, and host mapping hints. Team manifests are still conceptual rather than executable orchestration plans.

## Host Delivery Surfaces

Claude:

- `~/.claude/agents`
- `~/.claude/commands`
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
- `~/.gemini/skills`
- `~/.gemini/GEMINI.md`
- `<project>/GEMINI.md`
- `<project>/.gemini/agents`
- `<project>/.gemini/commands`
- `<project>/.gemini/skills`
- `<project>/.gemini/settings.json`

## Knowledge Anchor

`docs/LESSONS_LEARNED.md` is the append-first knowledge ledger for validated workarounds, host quirks, and promotion candidates.

- Claude and Gemini load it through thin host boot files with native imports.
- Codex reaches it through `AGENTS.md`, generated agent instructions, and runtime-validation prompts.
- Harvesters append normalized entries there first; doctrine files only change when a lesson is broad enough to promote.

## Unified MCP Governance

`global-mcp.json` is the only place shared MCP servers are declared. The sync engine translates those declarations into:

- Claude project `.mcp.json`
- Codex `.codex/config.toml`
- Gemini `.gemini/settings.json`

The file is currently intentionally empty. The injection logic exists before the first real shared server is added so the governance path is established early.

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
