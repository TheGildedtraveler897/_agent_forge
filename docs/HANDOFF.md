# Agent Forge Handoff

Last updated: 2026-04-04

## What Changed

### Claude Validation Run — Full Remediation (2026-04-04)

Claude independently validated the full ZorroForge multi-agent workspace, then executed all remediations.

#### Phase 1: Audit + Initial Fixes
- Promoted 3 unregistered skills (`zorroforge-brand`, `zorroforge-legal`, `zorroforge-procurement`) from `jarvis/.claude/skills/` into canonical `_agent_forge` sources
- Created canonical SKILL.md files under `skills/global/` for each
- Created Claude adapter files under `claude/global/agents/` for each
- Added all 3 to `registry.json`
- Created symlinks in `~/.claude/agents/` for delivery
- Updated `docs/CLAUDE_NATIVE.md` to list the new subagents

#### Phase 2: Full Governance of .claude/skills/
- **Policy decision:** `_agent_forge` now governs `.claude/skills/` delivery as a third target alongside agents/commands
- Promoted rich SKILL.md content from `jarvis/.claude/skills/` to canonical `_agent_forge/skills/` locations for all 7 skills that had drifted (jarvis-system, jarvis-coder, jarvis-audit, jarvis-healthcheck, jarvis-reviewer, zorroforge-finance, zorroforge-infra)
- Updated `sync-claude-adapters.sh` to deploy `.claude/skills/` symlinks (global + project-local) when `--project` is used
- Replaced all 12 non-symlink copies in `jarvis/.claude/skills/` with symlinks to canonical sources
- Added `skills_synced` field to registry.json for projects with managed skills delivery
- Updated `verify-agent-forge.py` to check `.claude/skills/` symlinks for `skills_synced` projects
- Added Codex targets for brand/legal/procurement (symlinks in `~/.codex/skills/`)
- Registry updated: all 3 new skills now target both codex and claude

#### Phase 3: Git Initialization
- `_agent_forge`: git init + initial commit (49 files, 3302 lines)
- `homelab`: git init + initial commit (52 files, 5180 lines), with `.gitignore` updated to exclude runtime application data (`configs/`)

## Current State

- **Registry:** v3, 17 skills (9 global, 3 Claude-only governance roles, 5 jarvis project-local)
- **Verification:** 120 checks, 0 failures
- **Delivery targets:** `~/.claude/agents/` (8 symlinks), `~/.claude/commands/` (4 symlinks), `~/.codex/skills/` (14 symlinks), `jarvis/.claude/skills/` (14 symlinks), `jarvis/.claude/agents/` (2 symlinks), `jarvis/.claude/commands/` (3 symlinks)
- **Git repos:** All 8 workspaces under version control (_agent_forge, jarvis, RoboNaaz, ZorroClaw, homelab, factory, playlist-archive, plus Projects root)

## Three-Layer Delivery Model

```
_agent_forge/skills/global/*/SKILL.md     -> rich skill content (Skill tool)
_agent_forge/claude/global/agents/*.md    -> thin adapter prompts (Agent tool)
_agent_forge/claude/global/commands/*.md  -> thin adapter prompts (slash commands)
```

Sync deploys:
- `~/.claude/agents/` and `~/.claude/commands/` = always (global)
- `<project>/.claude/skills/` = per-project via `--project` flag
- `<project>/.claude/agents/` and `<project>/.claude/commands/` = per-project via `--project` flag
- `~/.codex/skills/` = via `sync-codex-skills.sh`

## Clean Restart Point

All gaps identified during validation have been resolved. Run `verify-agent-forge.py` to confirm. To bootstrap a new project with full skill delivery:

```bash
./scripts/sync-claude-adapters.sh --project <name>
./scripts/sync-codex-skills.sh --project <name>
```
