# Agent Forge Governance

This document defines the layers that keep projects aligned with the shared omni-factory architecture.

## 1. Governance Audit

Purpose:

- inspect governed projects for drift
- confirm canonical sources are internally coherent
- confirm generated Claude, Codex, and Gemini delivery surfaces can be rebuilt deterministically
- confirm projects remain portable and agent-agnostic
- confirm harvested lessons are recorded in the knowledge anchor before doctrine is promoted

Primary artifacts:

- `skills/global/multi-agent-governor/`
- `skills/global/sprint-harvester/`
- `skills/global/memory-archivist/`
- `scripts/omni_factory.py`
- `scripts/verify-agent-forge.py`
- `scripts/validate-triad-runtime.py`
- `projects.json`
- `global-mcp.json`
- `policies/hooks.json`
- `policies/memory.json`
- `runtime/validation-matrix.json`
- `docs/LESSONS_LEARNED.md`

Default behavior:

- audit only
- findings first
- exact remediation second

## 2. Project Bootstrap

Purpose:

- stamp new projects with the minimum complete governance footprint
- make future projects agent-ready from day one

Primary artifacts:

- `skills/global/project-bootstrap/`
- `scripts/bootstrap-project.sh`

Default bootstrap footprint:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `MEMORY.md`
- `.forge_state/README.md`
- `.forge_state/manifest.json`
- `docs/CONOPS.md`
- `docs/HANDOFF.md`
- `.claude/CLAUDE.md`
- `.claude/agents/`
- `.claude/skills/`
- `.claude/skills/`
- `.claude/settings.json`
- `.gemini/agents/`
- `.gemini/skills/`
- `.gemini/skills/`
- `.gemini/settings.json`
- `.agents/skills/`
- `.codex/agents/`
- `.codex/config.toml`
- `.codex/hooks.json`
- `.mcp.json`

## 3. Skill Delivery Governance

The factory now has three governed host families plus a cross-host layer:

- Claude:
- `~/.claude/agents/`
- `~/.claude/skills/`
- `~/.claude/skills/`
- `<project>/.claude/agents/`
- `<project>/.claude/skills/`
- `<project>/.claude/skills/`
- `<project>/.claude/settings.json`
- `<project>/.mcp.json`

- Codex:
- `~/.agents/skills/`
- `<project>/.agents/skills/`
- `<project>/.codex/agents/`
- `<project>/.codex/config.toml`
- `<project>/.codex/hooks.json`

- Gemini:
- `~/.gemini/skills/`
- `~/.gemini/agents/`
- `~/.agents/skills/`
- `<project>/GEMINI.md`
- `<project>/.gemini/skills/`
- `<project>/.gemini/agents/`
- `<project>/.gemini/skills/`
- `<project>/.gemini/settings.json`

- Cross-host (one file per governed project, reachable from all three hosts):
- `<project>/MEMORY.md`
- `<project>/.forge_state/README.md`
- `<project>/.forge_state/manifest.json`

Rules:

- host-native delivery surfaces are generated from canonical metadata
- project skill delivery is selective, not automatic
- `registry.json` is compatibility output, not a source of truth
- user-home surfaces are convenience overlays; project-local governed surfaces take precedence
- host boot files keep native names (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`)
- harvested lessons land in `docs/LESSONS_LEARNED.md` before any doctrine promotion

## 4. Canonical Versus Generated

Always edit canonical sources in `_agent_forge`.

- skills -> `skills/`
- governed project catalog -> `projects.json`
- MCP inventory -> `global-mcp.json`
- hook policy -> `policies/hooks.json`
- memory section schema -> `policies/memory.json`
- deterministic setup logic -> `scripts/`

Tool-home directories and per-project host outputs are delivery targets only.

## 5. Agents And Teams

Agent Forge now also carries a canonical distinction between:

- skills
- agents
- agent teams

Primary artifacts:

- `docs/AGENTS_AND_TEAMS.md`
- `docs/TEAM_SELECTION.md`
- `docs/CONTEXT_ENGINEERING.md`
- `docs/OPERATOR_TEMPLATES.md`
- `docs/EVALUATION.md`
- `teams/*.json`
- generated `registry.json` team entries

Teams remain conceptual and portable first. Deep swarm automation is intentionally deferred.

## 6. Knowledge Harvesting

Agent Forge treats anti-entropy as governance work, not as an informal note-taking habit.

Rules:

- end-of-sprint lessons are harvested into `docs/LESSONS_LEARNED.md`
- normalized entries capture evidence, architectural decision, and promotion target
- doctrine promotion is explicit and separate from harvesting
- lessons that become obsolete should be marked `superseded`, not silently deleted
