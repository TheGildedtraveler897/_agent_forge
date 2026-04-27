# Sprint 3 Design: Cross-Host Auto-Memory Bridge

Date: 2026-04-27

## Goal

Ship Architectural Upgrade A2 + Capability B2 by adding an append-first bridge between canonical `<project>/MEMORY.md` and host-local memory surfaces, then prove the bridge is reachable through the triad validator.

## Current Host Facts

- Claude Code documents auto memory as machine-local at `~/.claude/projects/<project>/memory/`, with a `MEMORY.md` index and optional topic files. The first 200 lines or 25KB of that index load at session start. `autoMemoryDirectory` is accepted from user/local/policy settings, not project settings.
- Gemini CLI Auto Memory is experimental and extracts repeated procedures into reviewable `SKILL.md` drafts. It complements, but does not replace, the `save_memory` tool, which appends facts to `~/.gemini/GEMINI.md`. Project context still flows through `GEMINI.md` and `@file.md` imports.
- Codex memories are opt-in and generated under `~/.codex/memories/`. OpenAI docs say these files are generated state and should not be hand-edited as the primary control surface. Codex's authoritative checked-in project context remains `AGENTS.md`.

## Policy Shape

`policies/memory.json` moves to version 2 by adding an additive `bridge` block:

```json
{
  "bridge": {
    "enabled": true,
    "hosts": ["claude", "codex", "gemini"],
    "outbound_event": "session_start",
    "inbound_event": "stop",
    "conflict_policy": "append-first",
    "secrets_policy_inheritance": "deny"
  }
}
```

The inbound event uses canonical `stop` because Sprint 2 maps it to Claude/Codex `Stop` and Gemini `SessionEnd`.

## Bridge State

Each governed project gets mutable local bridge state at `<project>/.forge_state/bridge.json`:

```json
{
  "version": 1,
  "last_outbound": {},
  "last_inbound": {},
  "last_outbound_hash": {},
  "last_inbound_diff_hash": {},
  "imported_entry_hashes": {},
  "native_targets": {},
  "last_errors": {}
}
```

`bridge.log` is append-only JSONL beside it. Neither file is canonical doctrine.

## Native Targets

- Claude outbound target: `~/.claude/projects/<absolute-project-path-with-slashes-replaced-by-dashes>/memory/MEMORY.md`. This matches the local observed slug shape, for example `/home/.../Projects/jarvis` -> `-home-...-Projects-jarvis`.
- Gemini outbound target: `<project>/.gemini/memory/MEMORY.md`. This is a bridge sidecar, not a claim that Gemini Auto Memory loads this file. Gemini already sees canonical `MEMORY.md` through the generated root `GEMINI.md @MEMORY.md` import.
- Codex outbound target: `<project>/.codex/memory/AGENTS_MEMORY.md`. This avoids mutating OpenAI-generated `~/.codex/memories/` files or rewriting project `AGENTS.md` on every session start.

## Hook Wiring

Use host-specific hook records instead of a shared `$HOST_TAG` command. The public hook docs do not guarantee a common host-tag environment variable, and relying on one would recreate silent-correctness risk.

For each host:

- `memory-bridge-outbound-<host>`: event `session_start`, command `python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py outbound --project . --host <host>`, async true.
- `memory-bridge-inbound-<host>`: event `stop`, command `python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py inbound --project . --host <host>`, async true.

Claude renders async natively. Codex/Gemini command hooks remain fast and idempotent; if a host ignores async metadata, the bridge still avoids perceptible latency when hashes are unchanged.

## Inbound Rules

Inbound reads the host target, removes the bridge-managed block if present, computes a diff hash, and imports new bullet/paragraph lines only once per host. Each imported line is classified into the existing memory sections with conservative heuristics:

- commands/tests/build/lint -> `build_commands`
- failure/error/blocker -> `known_failures`
- decision/chose/decided -> `recent_decisions`
- active/todo/current -> `active_tasks`
- fallback -> `project_quirks`

The bridge reuses the memory-archivist writer so timestamps, source tags, retention warnings, and audit logs stay centralized.

## Verification

- `bridge.py outbound/inbound/status` unit tests cover idempotent outbound, inbound import, and secrets rejection.
- `scripts/verify-agent-forge.py` validates memory policy v2, bridge policy fields, hook command script paths, and bridge state files under every governed project.
- `scripts/validate-triad-runtime.py` adds `memory_bridge_for(host, root)` and requires `bridge_pass: true` per host. Pass means the bridge policy is enabled, bridge state exists, the host has a native target path, and either outbound or inbound has run for that host.

## Non-Goals

- Do not edit Codex generated memory files under `~/.codex/memories/`.
- Do not rewrite project `AGENTS.md` from a session hook.
- Do not claim Gemini experimental Auto Memory loads `.gemini/memory/MEMORY.md`; it is a bridge sidecar until the public docs expose a stable project fact-memory file.

## Shipped Verification

Sprint 3 shipped on 2026-04-27 with these proof points:

- `python3 -m py_compile scripts/omni_factory.py scripts/validate-triad-runtime.py skills/global/memory-bridge/bridge.py skills/global/memory-archivist/archivist.py` exit 0.
- `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge` exit 0.
- `python3 scripts/verify-agent-forge.py` exit 0.
- `python3 skills/global/memory-bridge/bridge.py outbound --project /home/pheonixprotocol/Projects/jarvis --host claude|codex|gemini` produced native target files and matching content hash `5413aa8cb72de0e691f4b7c77b8926879f589b2fa86e133c5af00e4232861eef`.
- `python3 scripts/validate-triad-runtime.py --project jarvis` exit 0 with artifact `runtime/validation/triad/20260427-203021/summary.json`; all three hosts reported `hook+ mem+ bridge+`.
