---
name: memory-archivist
description: Append normalized session-state entries (build commands, project quirks, active tasks, recent decisions, known failures) to a project's MEMORY.md so the next host or session sees the same brain. Use whenever a verified fact, decision, or workaround should outlive the current session but is not yet durable enough for the lesson ledger.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Memory Archivist

Capture session-scoped state in the universal cross-host memory layer so the next host or session inherits it.

## Mission

Translate verified facts, in-flight tasks, and short-lived decisions into normalized `MEMORY.md` entries under the appropriate section. Append-first by default; never silently rewrite prior entries (except in `active_tasks` where rewrite is the contract).

## Complement To Sprint Harvester

| Skill | Scope | Target file | Discipline |
|---|---|---|---|
| `sprint-harvester` | Durable, broad lessons that may promote into doctrine | `docs/LESSONS_LEARNED.md` | Append-first; promotion-gated |
| `memory-archivist` | Session-scoped state shared across hosts | `<project>/MEMORY.md` | Append-first; retention-bounded |

If a finding is durable, broad, and worth loading by default → `sprint-harvester`. If it is session-scoped, host-relevant, or short-lived → `memory-archivist`.

## Subcommands

The skill ships an executable Python helper at `archivist.py` next to this file. Invoke with `python3 ~/Projects/_agent_forge/skills/global/memory-archivist/archivist.py <subcommand>`.

### `append`

```
archivist.py append --project <root> --section <id> --entry "<text>" [--source claude|codex|gemini]
```

- Refuses if `--section` is not in `policies/memory.json`.
- Refuses if `--entry` matches a secrets-deny pattern (private keys, AWS creds, tokens, etc.).
- Appends a single timestamped line under the named section anchor.
- For `active_tasks` (the only rewriteable section), `--replace` may be passed to overwrite the body instead of appending.

### `validate`

```
archivist.py validate --project <root>
```

- Confirms `MEMORY.md` parses, every required section anchor is present, `.forge_state/manifest.json` is well-formed.
- Warns when any section approaches `retention.warn_at` (default 40 of 50 entries).
- Exits 0 on green.

### `summary`

```
archivist.py summary --project <root>
```

- Emits structured JSON: per-section counts, latest entry timestamp, retention warnings, last_updated from manifest.

## Rules

1. **Append-first, except `active_tasks`.** Past decisions and failures are durable for the session; rewriting them silently destroys context for the next host.
2. **No secrets.** The skill rejects entries that look like private keys, tokens, or credentials. `policies/memory.json` declares `secrets_policy: deny`.
3. **Time-stamp every entry** in UTC ISO-8601 so other hosts can reason about ordering.
4. **Tag the source host** when known (`--source claude|codex|gemini`) so cross-host provenance is visible.
5. **One entry per call.** Do not batch multiple semantic facts into one entry — they should be retrievable independently.
6. **Audit log.** Every append/replace writes one line to `<project>/.forge_state/archivist.log`.
7. **Non-goal:** the archivist is not the sprint-harvester. It does not promote entries into `LESSONS_LEARNED.md`. Promotion is a separate, deliberate action.
8. **Non-goal:** the archivist is not the lesson ledger. Doctrine candidates should still go through `sprint-harvester`.

## Section Reference

- `build_commands` — verified shell commands (test runners, lint, build, deploy). Append-only.
- `project_quirks` — non-obvious behaviors, traps, host-specific or env-specific gotchas. Append-only.
- `active_tasks` — short-lived in-flight work; the only rewriteable section.
- `recent_decisions` — choices made this session that should propagate but are not yet doctrine. Append-only.
- `known_failures` — current blockers, reproducer notes, workarounds awaiting promotion. Append-only.

## Output Contract

- Single appended (or replaced, for `active_tasks`) entry under the correct section anchor.
- One audit-log line in `<project>/.forge_state/archivist.log`.
- Manifest `last_updated` timestamp refreshed.
