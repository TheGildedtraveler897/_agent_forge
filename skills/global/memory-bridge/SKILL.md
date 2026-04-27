---
name: memory-bridge
description: Use when synchronizing canonical project MEMORY.md with host-local Claude, Codex, or Gemini memory sidecars through session start and stop hooks.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Memory Bridge

Synchronize host-local memory surfaces around canonical `<project>/MEMORY.md` without making any host's generated memory files the source of truth.

## Mission

Run as a hook handler at session start and session stop. On start, export canonical `MEMORY.md` into the host-local memory target. On stop, import new host-local notes back through `memory-archivist` so canonical memory remains append-first, timestamped, source-tagged, and secrets-filtered.

## Subcommands

The helper is `bridge.py` next to this file.

```bash
python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py outbound --project <root> --host claude|codex|gemini
python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py inbound  --project <root> --host claude|codex|gemini
python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py status   --project <root>
```

## Rules

1. **Canonical wins for export.** Outbound copies canonical `MEMORY.md` into a managed block in the host-local target.
2. **Append-first for import.** Inbound never deletes canonical entries. New host notes are appended through `memory-archivist`.
3. **Idempotent.** Content hashes prevent duplicate native writes and duplicate inbound imports.
4. **No secrets.** The bridge applies the same deny patterns as `memory-archivist` before export or import.
5. **Generated memory caution.** Codex generated memories under `~/.codex/memories/` are read-only generated state. The bridge writes a project sidecar instead of mutating those files.
6. **Gemini caution.** Gemini Auto Memory currently extracts skills, not a stable project fact-memory file. The bridge writes a project sidecar while generated `GEMINI.md` continues to import canonical `MEMORY.md`.
7. **Audit everything.** Every action writes JSONL to `<project>/.forge_state/bridge.log`.

## Native Targets

- Claude: `~/.claude/projects/<encoded-project-path>/memory/MEMORY.md`
- Codex: `<project>/.codex/memory/AGENTS_MEMORY.md`
- Gemini: `<project>/.gemini/memory/MEMORY.md`

## Non-Goals

- Do not edit anchor lines in canonical `MEMORY.md`; use `memory-archivist`.
- Do not rewrite project `AGENTS.md` from hook execution.
- Do not claim host-generated memory internals are stable unless current official docs say so.
