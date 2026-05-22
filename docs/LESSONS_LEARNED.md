# Lessons Learned

This file is the append-first knowledge anchor for Agent Forge. Validated workarounds, host quirks, and durable lessons land here before any change to canonical doctrine.

## Rules

- Add normalized entries here before changing durable doctrine.
- Do not overwrite `AGENTS.md` or `docs/CONOPS.md` as part of harvesting.
- Promote a lesson into doctrine only when it is durable, broad, and worth loading by default.
- Keep secrets, local-only residue, and one-off operator trivia out of this ledger.
- Once an entry's `Status:` is `promoted` and its named doctrine reference resolves on disk, the `lesson-distiller` skill is eligible to archive it to `docs/archive/LESSONS_PROMOTED.md`, leaving a one-line index pointer in this file.

## Entry Template

### <date> - <short title>

- `Date:` YYYY-MM-DD
- `Context:` where the issue appeared and why it mattered
- `Lesson:` the reusable learning
- `Architectural Decision:` what Agent Forge should do going forward
- `Evidence:` changed files, commands, or validation artifacts that proved it
- `Promotion Target:` doc or capability to update later, if any
- `Status:` `active`, `promoted`, or `superseded`

## Entries

_No lessons have been recorded yet on this fresh install. Add your first entry below using the template above._
