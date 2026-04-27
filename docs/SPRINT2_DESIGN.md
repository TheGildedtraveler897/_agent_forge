# Sprint 2 Design: Hook Lifecycle V2

Date: 2026-04-27

## Goal

Move `policies/hooks.json` from implicit command-only v2 records to explicit v3 handler records while tightening host event-name allow-lists so hook surfaces cannot pass with stale native event keys.

## Current-doc findings

- Claude Code hooks expose a broad lifecycle and five handler types: `command`, `http`, `mcp_tool`, `prompt`, and `agent`. Command hooks support `async` and `asyncRewake`.
- Gemini CLI hooks use PascalCase event keys such as `BeforeTool`, `AfterTool`, `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeToolSelection`, `SessionStart`, `SessionEnd`, `Notification`, and `PreCompress`. Gemini currently supports `command` handlers only.
- Codex hooks are behind `codex_hooks = true`, load from `hooks.json` or inline TOML, and use PascalCase event keys such as `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, and `Stop`. Codex currently documents `command` handlers.

## Schema v3

`policies/hooks.json` remains:

```json
{
  "version": 3,
  "shared": [],
  "claude": [],
  "codex": [],
  "gemini": []
}
```

Each active hook record uses:

```json
{
  "id": "stable-id",
  "description": "human-readable purpose",
  "event": "pre_tool_use",
  "matcher": "Bash",
  "handler": { "type": "command", "command": "bash ..." },
  "targets": ["claude", "codex", "gemini"],
  "timeout_ms": 5000,
  "status_message": "short status",
  "enabled": true
}
```

Supported handler shapes:

- `command`: `{ "type": "command", "command": "bash ..." }`
- `http`: `{ "type": "http", "url": "https://...", "headers": {}, "allowed_env_vars": [] }`
- `mcp_tool`: `{ "type": "mcp_tool", "server": "server_id", "tool": "tool_name", "input": {} }`
- `prompt`: `{ "type": "prompt", "prompt": "...", "model": "optional" }`
- `agent`: `{ "type": "agent", "prompt": "..." }`

Legacy v2 records with top-level `command` are accepted by the renderer as command handlers, but the verifier warns that v2 is deprecated.

## Rendering rules

- Claude renders all five handler types using Claude-native handler fields.
- Codex renders active `command` hooks only. Non-command hooks targeting Codex are verifier warnings unless disabled.
- Gemini renders active `command` hooks only. Non-command hooks targeting Gemini are verifier warnings unless disabled.
- `timeout_ms` converts to seconds for Claude and Codex, and remains milliseconds for Gemini.
- `async` and `async_rewake` render only for Claude `command` handlers. `async_rewake` implies `async`.
- `permission_updates` is retained as canonical metadata for scripts that emit `updatedPermissions`; it is not rendered into settings because current Claude docs define permission updates as hook output, not hook configuration.

## Event allow-list

The renderer owns a curated canonical-event table. Each host maps a canonical event id to a native event key or `null` when unsupported. Active hooks with unsupported host/event pairs are skipped with a verifier warning rather than rendered into invalid host config.

Legacy canonical aliases remain:

- `pre_commit` merges into `pre_tool_use`
- `post_edit` merges into `post_tool_use`
- `stop` remains supported and maps to Gemini `SessionEnd`

## Validation

- `tests/test_hooks_v3.py` asserts Codex now renders `PreToolUse`, v2 records normalize to command handlers, and the host event allow-list has the known high-risk mappings.
- `python3 scripts/verify-agent-forge.py` validates schema v3, handler shape, command script existence, targets, event ids, and async rules.
- `python3 scripts/validate-triad-runtime.py --project jarvis` checks every active hook record's expected native event key on each rendered host surface.

## Runtime verdict

Default triad validation proves runtime reachability of generated skill, hook, and memory surfaces. Optional live invocation remains separate because Claude and Codex have documented headless/sandbox constraints in this environment; Gemini live invocation remains the deepest hook-dispatch proof.
