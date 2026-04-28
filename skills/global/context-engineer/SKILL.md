---
name: context-engineer
description: Compact broad tasks into the smallest artifact set that still preserves truth. Use when a session is growing, a handoff is needed, or a premium-model pass should leave behind cheaper-model-ready briefs.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Context Engineer

Turn raw session state into compact, durable operator artifacts.

## Responsibilities

1. Remove duplicated repo facts and repeated narrative.
2. Separate confirmed facts from assumptions and open questions.
3. Produce the smallest artifact set needed for the next worker.
4. Preserve source references and acceptance criteria.

## Preferred Outputs

- task brief
- evidence pack
- implementation brief
- handoff
- compaction note

## Rules

- optimize for restartability, not completeness-by-default
- keep unresolved uncertainty explicit
- prefer bullets and templates over prose blocks
- never hide a missing decision inside a summary
- if the next worker is a cheaper model, make the brief self-contained

## Example: Compacting a Research Session

Before (scattered across 2000 tokens of chat):
> "We looked at yt-dlp and spotDL. yt-dlp works for YouTube. spotDL had Spotify API issues so we switched to spotipy. The archive folder structure is playlists/{source}/{name}/. We need to handle rate limiting..."

After (compact task brief, ~200 tokens):
```
# Task Brief: playlist-archive download scripts

## Goal
Build idempotent download scripts for YouTube (yt-dlp) and Spotify (spotipy).

## Decisions Made
- YouTube: yt-dlp (proven, stable)
- Spotify: spotipy (spotDL dropped — Spotify API policy)
- Archive layout: playlists/{source}/{playlist-name}/

## Open Questions
- Rate limiting strategy for Spotify API
- Metadata format (JSON sidecar vs embedded tags)

## Acceptance Criteria
- yt-dlp script downloads a test playlist without errors
- spotipy script exports metadata for a test playlist
- Both scripts are idempotent (re-run produces no duplicates)
```

## Checkpoint Discipline

When a session is being compacted, also write a rolling handoff to `dev/active/<slug>/handoff.md` if the directory exists. The handoff captures the last verification-gate result, the next micro-task ID from the active plan, and any unresolved questions. The durable plan stays at `docs/plans/<slug>.md`; the handoff is a transient cursor only.

Pointer of record is `MEMORY.md active_tasks` (the only rewriteable section, owned by `memory-archivist`). The handoff file is local-only — the repo `.gitignore` excludes `dev/`. Do not promote handoff content to `docs/HANDOFF.md` until the task closes; that promotion is the `branch-finisher` or `sprint-harvester` step, not a compaction step.
