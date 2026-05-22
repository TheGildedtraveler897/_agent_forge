---
name: handoff-archiver
description: Compact docs/HANDOFF.md by archiving historical sprint sections beyond a configurable retention window. Use after a sprint or RC milestone when HANDOFF.md exceeds its session-load threshold and only the most recent sprints are operationally current. Moves older sections verbatim to docs/archive/SPRINTS.md and replaces them with a compact summary table. Reversible via git history; preserves all wisdom byte-for-byte.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Handoff Archiver

Bounded-decay companion for `docs/HANDOFF.md`, paired with `lesson-distiller` for `docs/LESSONS_LEARNED.md`.

## Mission

`docs/HANDOFF.md` is auto-loaded into every Claude and Gemini session. It accumulates one detailed section per sprint, each carrying full evidence (commit hashes, validation artifact paths, test outputs). The most recent sprint or two are operationally current; everything older is reference material that should not pay session-load tax. This skill archives older sprint sections to `docs/archive/SPRINTS.md` and leaves a compact summary table in `HANDOFF.md`.

## Boundary With Sibling Skills

- `lesson-distiller` owns `docs/LESSONS_LEARNED.md` compaction.
- `handoff-archiver` owns `docs/HANDOFF.md` compaction.
- Both are downstream-only: they do not invent content; they only relocate content already written by humans, sprints, or `sprint-harvester`.
- Both inherit policy from `policies/distillation.json`.

## Subcommands

```
python3 ~/Projects/_agent_forge/skills/global/handoff-archiver/archiver.py <subcommand>
```

### `dry-run`

```
archiver.py dry-run [--keep N]
```

- Reports which sprint sections would move, the projected byte delta, and the summary-table preview. No files modified.
- `--keep` overrides `policies/distillation.json` `targets[handoff_log].keep`.

### `archive`

```
archiver.py archive [--keep N] [--yes]
```

- Performs the archival. Without `--yes`, prints the dry-run output and exits non-zero.
- Preserves the top header, "## Current State", "## Remaining Weaknesses", "## Manual Follow-Up Items", "## Next Evolution", and "## Final Verdict" sections untouched.
- Replaces the moved sections with a compact summary table at the top of "## What Changed".
- Writes one audit line per action to `<repo>/.forge_state/distiller.log` (shared with lesson-distiller; same audit surface).

## Sprint Detection

Sprint sections are identified as `### ` headings inside the `## What Changed` block. The date used for sorting is the first `YYYY-MM-DD` token found inside the heading's parenthetical. Sections with no parseable date are sorted to the end (treated as oldest) and only moved if the operator confirms — they are reported as warnings in dry-run output.

## Rules

1. **Preserve wisdom verbatim.** Archived sections are byte-for-byte copies; never summarized.
2. **Keep the most recent N (default 1).** Configurable per call or via the policy file.
3. **Leave the operator-state sections alone.** "Current State", "Remaining Weaknesses", "Resolved Backlog", "Manual Follow-Up", "Next Evolution", and "Final Verdict" are operationally current; they are never archived.
4. **Idempotent.** A second `archive` run with no new sprints beyond the keep window is a no-op.
5. **Audit log.** Every action writes one line to `.forge_state/distiller.log`.
6. **Restore via git.** Unlike lessons (where individual entries can be restored), sprint sections are reverted via standard git history. The archive file is the canonical on-disk source for archived sprints.

## Cadence

Bind to RC/milestone events via the `branch-finisher` skill (Step 6 — milestone hook). Operator approval is required before `archive` applies changes.

## Output Contract

- `dry-run`: structured JSON with `would_archive` (date + heading), `would_keep`, `byte_delta_estimate`, and a preview of the new summary table.
- `archive`: structured JSON with `archived` count, `kept` count, `byte_delta`, plus updated archive file and trimmed `HANDOFF.md`.
