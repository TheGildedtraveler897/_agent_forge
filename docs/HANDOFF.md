# Agent Forge Handoff

Last updated: 2026-04-04

## What Changed

### Claude Validation Run (2026-04-04)

Claude independently validated the full ZorroForge multi-agent workspace.

Changes made:
- Promoted 3 unregistered skills (`zorroforge-brand`, `zorroforge-legal`, `zorroforge-procurement`) from `jarvis/.claude/skills/` into canonical `_agent_forge` sources
- Created canonical SKILL.md files under `skills/global/` for each
- Created Claude adapter files under `claude/global/agents/` for each
- Added all 3 to `registry.json` as Claude-only global subagents
- Created symlinks in `~/.claude/agents/` for delivery
- Updated `docs/CLAUDE_NATIVE.md` to list the new subagents
- Created this HANDOFF.md

### Findings Documented

1. **`.claude/skills/` dual-delivery model** — Claude Code discovers skills via `.claude/skills/` (Skill tool) AND `.claude/agents/` (Agent tool). These serve different runtime purposes. The `_agent_forge` governance model currently only covers the agents/commands delivery path. The `.claude/skills/` directory in jarvis contains richer, more detailed versions of skills that also exist as compressed adapters in `_agent_forge`. This is a design tension that needs a policy decision.

2. **Content drift between `.claude/skills/` and `_agent_forge` canonical sources** — The jarvis `.claude/skills/` copies of zorroforge-finance, zorroforge-infra, and jarvis-* skills have diverged from their `_agent_forge` canonical sources. The `.claude/skills/` versions are more detailed; the `_agent_forge` versions are compressed. Neither is wrong, but they serve the same logical skill through different mechanisms with different content.

3. **`_agent_forge` is not a git repo** — The canonical source of truth has no version control.

4. **`homelab` is not a git repo** — Governance drift from the expected model.

## Open Items

- Decide policy: should `_agent_forge` govern `.claude/skills/` delivery alongside agents/commands? If so, update sync scripts and registry.json schema.
- Resolve content drift between jarvis `.claude/skills/` and `_agent_forge` canonical sources.
- Consider git-initializing `_agent_forge` and `homelab`.
- The 3 newly promoted skills (brand, legal, procurement) are Claude-only (no Codex targets). Add Codex targets if Codex needs them.

## Clean Restart Point

All 17 registered skills pass verification. All 6 governed projects pass verification. Sync scripts are dynamic and handle the expanded inventory.
