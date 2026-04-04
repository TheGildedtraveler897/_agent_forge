# Agent Forge Governance

This document defines the two layers that keep projects aligned with the shared multi-agent architecture.

## 1. Governance Audit

Purpose:

- inspect governed projects for drift
- confirm required files exist
- confirm Claude and Codex native delivery still point to canonical `_agent_forge` sources
- confirm projects remain portable and agent-agnostic

Primary artifacts:

- `skills/global/multi-agent-governor/`
- `claude/global/commands/multi-agent-governor.md`
- `scripts/verify-agent-forge.py`
- `registry.json`

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
- `claude/global/commands/project-bootstrap.md`
- `scripts/bootstrap-project.sh`

Default bootstrap footprint:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/CONOPS.md`
- `docs/HANDOFF.md`
- `.claude/CLAUDE.md`
- `.claude/agents/`
- `.claude/commands/`

## 3. Canonical Versus Generated

Always edit canonical sources in `_agent_forge`.

- skills -> `skills/`
- Claude adapters -> `claude/`
- governance expectations -> `registry.json`
- deterministic setup logic -> `scripts/`

Tool-home directories and per-project `.claude/` outputs are delivery targets only.

## 4. Agents And Teams

Agent Forge now also carries a canonical distinction between:

- skills
- agents
- agent teams

Primary artifacts:

- `docs/AGENTS_AND_TEAMS.md`
- `teams/*.json`
- `registry.json` team entries

Teams remain conceptual and portable first. Deep swarm automation is intentionally deferred.
