---
name: lesson-distiller
description: Compact docs/LESSONS_LEARNED.md by archiving entries whose lessons have already been promoted into doctrine. Use after a sprint or RC milestone when the lesson ledger has grown beyond its session-load threshold and many entries are status=promoted. Verifies each promotion claim before archival; preserves wisdom verbatim in docs/archive/LESSONS_PROMOTED.md and leaves a one-line index pointer in the main ledger. Reversible via the restore subcommand.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Lesson Distiller

Bounded-decay counterpart to `sprint-harvester`. Where the harvester captures, this skill compacts.

## Mission

`docs/LESSONS_LEARNED.md` is auto-loaded into every Claude and Gemini session. Append-first discipline keeps it complete; without bounded decay it also keeps growing unbounded. Once a lesson is promoted into doctrine (`AGENTS.md` Rules, `docs/CONOPS.md`, an enforced check in code), the original ledger entry continues to ride along on every session as redundant context. This skill is the cleanup pass that closes that loop.

## Boundary With Sibling Skills

| Skill | Scope | Direction | Target file |
|---|---|---|---|
| `sprint-harvester` | Capture durable lessons at sprint end | Append | `docs/LESSONS_LEARNED.md` |
| `lesson-distiller` | Compact ledger after lessons are promoted | Archive + index | `docs/LESSONS_LEARNED.md` ↔ `docs/archive/LESSONS_PROMOTED.md` |
| `memory-archivist` | Append session-state across hosts | Append | `<project>/MEMORY.md` |
| `handoff-archiver` | Compact `HANDOFF.md` sprint history | Archive + table | `docs/HANDOFF.md` ↔ `docs/archive/SPRINTS.md` |

`sprint-harvester` does not delete or rewrite. `lesson-distiller` only acts on entries the harvester (or operator) has already marked `Status: promoted`. The two skills do not share code paths; one is upstream-append, the other is downstream-compact.

## Subcommands

The skill ships an executable Python helper at `distiller.py` next to this file. Invoke with:

```
python3 ~/Projects/_agent_forge/skills/global/lesson-distiller/distiller.py <subcommand>
```

### `dry-run`

```
distiller.py dry-run [--target lessons|triad|all]
```

- Reports which entries would be archived, which would fail promotion-claim verification, and the projected byte delta. No files modified.
- Default target: `lessons`. `triad` prunes timestamped runs under `runtime/validation/triad/`. `all` runs both.

### `distill`

```
distiller.py distill [--target lessons|triad|all] [--yes]
```

- Performs the archival. Without `--yes`, prints the dry-run output and exits non-zero (operator must confirm explicitly).
- Verifies every promotion claim before moving an entry. An entry whose claimed doctrine reference cannot be located is **not** archived; it is reported and skipped.
- Writes one audit line per action to `<project>/.forge_state/distiller.log` (or `<repo>/.forge_state/distiller.log` when run against the factory itself).

### `verify`

```
distiller.py verify
```

- Confirms `policies/distillation.json` parses, archive files (when present) are well-formed, and every one-line index pointer in the main ledger resolves to an entry in the archive file.

### `restore`

```
distiller.py restore --date YYYY-MM-DD --title "<short title>"
```

- Reverses an archival: moves the named entry back from the archive to `docs/LESSONS_LEARNED.md`. Used when distillation archived an entry whose promotion later turned out to be wrong.

## Promotion-Claim Verification

The integrity gate. Each promoted entry's `Status:` line carries a parenthetical naming the doctrine paths/sections that now hold the rule, e.g.:

```
- `Status:` promoted (`AGENTS.md` Rules + `docs/CONOPS.md` §Authoring Pattern)
```

The verifier extracts every backtick-quoted path from that parenthetical and confirms each exists on disk. If even one path resolves, verification passes. If the parenthetical is empty, malformed, or no path resolves, the entry is **flagged** and **left in place** — never silently archived.

This is conservative on purpose. Distillation is reversible, but a wrongly-archived entry is friction. Better to leave a still-relevant lesson loaded than to archive a lesson whose doctrine reference was never written.

## Rules

1. **Only act on `Status: promoted` entries.** `active` and `superseded` entries are out of scope.
2. **Preserve wisdom verbatim.** Archive entries are byte-for-byte copies; never summarized.
3. **Replace, do not delete.** Each archived entry leaves a one-line index pointer in the main ledger so a reader can still see the entry existed.
4. **Idempotent.** A second `distill` run with no new promotions is a no-op.
5. **Restorable.** Every archival can be undone via `restore`.
6. **Audit log.** Every action (including `dry-run`) writes one line to `.forge_state/distiller.log`.
7. **Non-goal:** the distiller is not the harvester. It does not promote entries; promotion is the harvester's job.

## Cadence

Bind to RC/milestone events via the `branch-finisher` skill (Step 6 — milestone hook). Operator approval is required before the `distill` subcommand applies changes; the dry-run gates it.

## Output Contract

- `dry-run`: structured JSON with `would_archive`, `verification_failures`, `byte_delta_estimate`.
- `distill`: structured JSON with `archived`, `skipped`, `byte_delta`, plus updated archive file and trimmed main ledger.
- `verify`: exit 0 if all index pointers resolve and the archive file is well-formed; exit 1 otherwise.
- `restore`: structured JSON with `restored: true` and the restored entry's date/title.
