<!-- Managed by Agent Forge omni-factory. Do not edit by hand. -->

# .forge_state

Local working state for the universal memory layer. Companion to the project's `MEMORY.md`.

- `manifest.json` — schema version, section list, and last-updated timestamp.
- `archivist.log` — append-only audit trail produced by the `memory-archivist` skill.
- `bridge.json` — mutable memory bridge state for host-local synchronization.
- `bridge.log` — append-only JSONL audit trail produced by the `memory-bridge` skill.

This directory is factory-managed. Do not edit `manifest.json` by hand; use the `memory-archivist` skill or re-run `python3 scripts/omni_factory.py sync-claude --project <name>` (or `sync-codex` / `sync-gemini`).
