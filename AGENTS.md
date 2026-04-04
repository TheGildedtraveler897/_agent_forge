# Agent Forge

This workspace is the canonical source of truth for portable multi-agent skills under `~/Projects`.

## Purpose

- Store shared skill content in a suitcase-friendly repo path
- Separate global reusable skills from project-local skills
- Keep tool-home folders such as `~/.codex/skills` as delivery targets, not source of truth

## Layout

- `skills/global/`: portable cross-project skills
- `skills/projects/<project>/`: project-local skills
- `teams/`: canonical starter team definitions and role contracts
- `claude/`: canonical Claude-native subagent and slash-command adapters
- `registry.json`: machine-readable skill registry
- `scripts/`: sync/export helpers
- `docs/`: portability and maintenance notes

## Rules

- Each skill lives in its own folder with `SKILL.md`
- Each team lives as a canonical manifest under `teams/`
- Keep `SKILL.md` concise; move heavy reference material into sidecar files later if needed
- Promote a skill from project-local to global only after removing repo-specific assumptions
- Update canonical skills and adapters here first, then sync outward to tool-native locations
