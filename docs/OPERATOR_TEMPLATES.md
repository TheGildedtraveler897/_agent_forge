# Operator Templates

> **Note on examples:** Each template below is followed by a worked example. The worked examples — including any script names like `scripts/download-youtube.sh` — are **illustrative**, not real shipping artifacts in this repo. They show what a fully-filled template should look like; do not copy the example commands expecting them to run.

## First-Run Onboarding

When a fresh operator finishes `./scripts/bootstrap-project.sh --name <name>` and isn't sure what just happened, point them at the `onboarding-guide` skill:

```bash
python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py tour
# or, for the 90-second non-interactive summary:
python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py tour --quick
# or, to look up a single concept:
python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py explain <topic>
```

Read-only and observational. Five guided sections (what the folder is, three tools / one source of truth, the seatbelt, the shared brain, what to do next). Adapts to operator experience via a one-question prompt. Plain-English translations of every agentic-vocabulary term (MCP, hook, sandbox, memory layer) on first mention.

**Future integration hook (deferred to a Codex sprint):** `scripts/bootstrap-project.sh` could grow a `--guided` flag that invokes `onboard.py tour` automatically at the end of bootstrap. The skill is intentionally read-only so the integration is a one-line addition to the bootstrap script, with no risk to the suitcase doctrine. Documented here so a future operator implementing the wire-up has the seam clearly named.

## Task Brief

```md
# Task Brief

## Goal

## Success Criteria

## Constraints

## Current Repo State

## Relevant Docs To Read First

## Out Of Scope

## Stop Condition
```

### Example

```md
# Task Brief: YouTube download script for playlist-archive

## Goal
Create an idempotent yt-dlp wrapper script that downloads a YouTube playlist to the local archive.

## Success Criteria
- Script accepts a playlist URL and downloads all videos
- Output structure: playlists/youtube/{playlist-name}/{video-title}.{ext}
- Re-running the script skips already-downloaded videos
- Metadata saved as JSON sidecar per video

## Constraints
- No API keys (yt-dlp uses public endpoints)
- Must work on both personal and work laptop (suitcase doctrine)
- Use .venv Python if any Python is needed; bash preferred

## Current Repo State
- playlist-archive/ exists with AGENTS.md, CONOPS.md, HANDOFF.md
- No scripts/ directory yet

## Relevant Docs To Read First
- playlist-archive/docs/CONOPS.md
- playlist-archive/docs/HANDOFF.md

## Out Of Scope
- Spotify downloads (separate task)
- Web UI or scheduling

## Stop Condition
Script runs successfully on a test playlist, output structure is correct, re-run is idempotent.
```

## Evidence Pack

```md
# Evidence Pack

## Question

## Sources

## Confirmed Findings

## Conflicts Or Uncertainty

## Practical Implications

## Recommended Next Step
```

### Example

```md
# Evidence Pack: yt-dlp archive mode options

## Question
What is the correct yt-dlp flag combination for idempotent playlist archiving?

## Sources
| Source | Type | Key Claim |
|---|---|---|
| yt-dlp README (GitHub) | Official | --download-archive file tracks completed downloads |
| yt-dlp man page | Official | --output template controls file naming |
| r/DataHoarder thread | Community | --write-info-json saves metadata as .info.json sidecar |

## Confirmed Findings
- `--download-archive archive.txt` records video IDs; skips on re-run
- `--output "%(playlist_title)s/%(title)s.%(ext)s"` gives clean folder structure
- `--write-info-json` saves metadata without extra API calls

## Conflicts Or Uncertainty
- `--embed-metadata` vs `--write-info-json`: embedding modifies the file; sidecar is non-destructive. Sidecar preferred for archival.

## Practical Implications
- Combine: `yt-dlp --download-archive archive.txt --write-info-json -o "playlists/youtube/%(playlist_title)s/%(title)s.%(ext)s" URL`

## Recommended Next Step
Write the wrapper script using these flags. Test on a small playlist first.
```

## Implementation Brief

```md
# Implementation Brief

## Outcome

## Decisions Already Made

## Files Or Surfaces In Scope

## Acceptance Criteria

## Verification Plan

## Risks
```

### Example

```md
# Implementation Brief: yt-dlp download script

## Outcome
A single bash script at `scripts/download-youtube.sh` that downloads a YouTube playlist idempotently.

## Decisions Already Made
- bash, not Python (simpler, no .venv needed)
- yt-dlp with --download-archive for idempotency
- JSON sidecar metadata (--write-info-json), not embedded
- Output: playlists/youtube/{playlist-name}/{title}.{ext}

## Files Or Surfaces In Scope
- scripts/download-youtube.sh (new)
- playlists/youtube/ (created by script)
- docs/HANDOFF.md (update after completion)

## Acceptance Criteria
- `./scripts/download-youtube.sh "https://youtube.com/playlist?list=TEST"` exits 0
- Files appear in playlists/youtube/{name}/
- Re-run downloads 0 new files
- archive.txt contains video IDs

## Verification Plan
```bash
./scripts/download-youtube.sh "https://www.youtube.com/playlist?list=PLtest123"
ls playlists/youtube/
cat playlists/youtube/*/archive.txt | wc -l
./scripts/download-youtube.sh "https://www.youtube.com/playlist?list=PLtest123"  # should skip
```

## Risks
- Large playlists may hit rate limits (mitigate with --sleep-interval 2)
- Playlist titles with special characters may break paths (mitigate with --restrict-filenames)
```

## Handoff

```md
# Handoff

## Current State

## What Changed

## What Is Verified

## Open Questions

## Next Clean Restart Point
```

### Example

```md
# Handoff: playlist-archive YouTube download script

## Current State
YouTube download script is complete and tested. Spotify download is not started.

## What Changed
- Created scripts/download-youtube.sh
- Uses yt-dlp with --download-archive for idempotency
- Output: playlists/youtube/{playlist-name}/{title}.{ext} + .info.json sidecars
- Tested on PLtest123 (5 videos) — all downloaded, re-run skipped correctly

## What Is Verified
- Idempotency works (archive.txt tracks downloaded IDs)
- Metadata JSON sidecars are created
- Script exits 0 on success, non-zero on yt-dlp errors

## Open Questions
- Should we add --sleep-interval for large playlists? (not needed for small tests)
- Spotify download approach still TBD (spotipy for metadata, but audio source unclear)

## Next Clean Restart Point
Read this handoff, then start on Spotify download script using the same output structure pattern.
```
