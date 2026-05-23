# Agents, Skills, And Teams

This document defines the current omni-factory model for reusable capabilities, specialized agents, and starter teams.

## Skills

Skills are canonical capability packs stored under `skills/`.

Use a skill when:

- the work is procedural or repeatable
- the capability should stay portable across hosts
- the same workflow repeats across repos

Properties:

- one folder, one `SKILL.md`
- metadata in frontmatter
- durable instructions in the body
- host delivery generated outward from canonical metadata

## Agents

Agents are specialized workers with bounded scope and separate context.

Use an agent when:

- the role needs a narrow responsibility
- the work benefits from a separate context window
- the stopping condition and handoff artifact should stay explicit

Host mapping:

- Claude: generated Agents
- Codex: generated custom agents plus skills
- Gemini: generated Agents plus commands and skills

## Teams

Teams are named multi-agent patterns with explicit role boundaries, collapse rules, escalation rules, and handoff artifacts.

Use a team when:

- one capability is not enough
- one worker would become a god agent
- planning, execution, review, or improvement should stay separate

## Design Rules

- specialists stay narrow
- canonical truth stays in repo docs and `_agent_forge`
- generated host surfaces are never hand-edited
- use handoff artifacts over hidden memory
- treat lesson harvesting as a first-class follow-on step

## Host Mapping

Claude:

- boot file: `CLAUDE.md`
- generated surfaces: `.claude/agents`, `.claude/commands`, `.claude/skills`, `.claude/settings.json` (hooks), `.mcp.json`

Codex:

- boot file: `AGENTS.md`
- generated surfaces: `.agents/skills`, `.codex/agents`, `.codex/config.toml`, `.codex/hooks.json`

Gemini:

- boot file: `GEMINI.md`
- generated surfaces: `.gemini/agents`, `.gemini/commands`, `.gemini/skills`, `.gemini/settings.json` (hooks + MCP)

Cross-host (one file per governed project, reachable from all three hosts via the AGENTS chain or a Gemini `@import`):

- `MEMORY.md` — universal session-state layer with sections defined in `policies/memory.json`.
- `.forge_state/` — companion directory with `README.md`, `manifest.json`, and the `archivist.log` audit trail.

## Core Teams

Governance Team:

- purpose: audit drift in canonical sources and generated host surfaces
- handoff artifacts: findings report, remediation checklist

Bootstrap Team:

- purpose: create or standardize governed projects correctly
- handoff artifacts: scaffold summary, verification result, follow-up checklist

Delivery Team:

- purpose: do product work without collapsing planning, build, and review into one role
- handoff artifacts: implementation plan, code/result summary, findings or test report

Research Team:

- purpose: gather evidence without flooding downstream workers
- handoff artifacts: evidence pack, source table, unresolved questions

Planning Team:

- purpose: convert evidence into decision-complete briefs
- handoff artifacts: implementation brief, assumptions list, acceptance criteria

Assessment Team:

- purpose: decide whether a result is correct and worth keeping
- handoff artifacts: findings report, scorecard, keep/revise/reject recommendation

Improvement Team:

- purpose: prioritize follow-on improvements, update doctrine, and harvest durable lessons
- handoff artifacts: prioritized improvement list, remediation plan, doctrine/doc checklist, lesson ledger append block, promotion candidates

## Context Discipline

- prefer handoff artifacts over replaying full chat history
- keep project-local delivery selective
- split context only when role boundaries are real
- harvest durable lessons into `docs/LESSONS_LEARNED.md` instead of re-deriving them next sprint

## What We Are Not Doing Yet

- fully automated swarms
- persistent unsupervised teams
- deep orchestration runtimes
- equal-depth automated runtime validators for every host
