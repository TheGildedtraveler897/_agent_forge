# Host Integrations

This document explains how the omni-factory maps canonical capability sources into native Claude, Codex, and Gemini surfaces.

## Native Boot Rules

Keep these filenames because the hosts load them natively:

- `CLAUDE.md`
- `AGENTS.md`
- `GEMINI.md`

Do not rename them to host-agnostic names. Rename secondary support docs instead.

## Canonical Inputs

The generator reads exactly these authoring surfaces:

- `skills/**/SKILL.md`
- `teams/*.json`
- `projects.json`
- `global-mcp.json`
- `policies/hooks.json`
- `policies/memory.json`

`registry.json` is compatibility output only.

## Claude

Generated surfaces:

- `~/.claude/agents/`
- `~/.claude/commands/`
- `<project>/.claude/agents/`
- `<project>/.claude/commands/`
- `<project>/.claude/skills/`
- `<project>/.mcp.json`

Host behavior:

- Claude Code auto-loads `CLAUDE.md` while walking up the directory tree.
- `_agent_forge/CLAUDE.md` stays thin and imports `AGENTS.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, and `docs/LESSONS_LEARNED.md`.
- Generated Claude agents and commands point back to the canonical `SKILL.md`.

## Codex

Generated surfaces:

- `~/.agents/skills/`
- `<project>/.agents/skills/`
- `<project>/.codex/agents/`
- `<project>/.codex/config.toml`
- `<project>/.codex/hooks.json`

Host behavior:

- Codex auto-loads `AGENTS.md` before work.
- Codex does not natively auto-load arbitrary docs paths the same way Claude and Gemini import files.
- The lesson ledger therefore stays canonical at `docs/LESSONS_LEARNED.md`, while `AGENTS.md`, generated Codex agents, and runtime-validation prompts explicitly point Codex to it when workaround history matters.

## Gemini

Generated surfaces:

- `~/.gemini/agents/`
- `~/.gemini/commands/`
- `~/.gemini/skills/`
- `~/.gemini/GEMINI.md`
- `<project>/GEMINI.md`
- `<project>/.gemini/agents/`
- `<project>/.gemini/commands/`
- `<project>/.gemini/skills/`
- `<project>/.gemini/settings.json`

Host behavior:

- Gemini CLI auto-loads `GEMINI.md` hierarchically.
- `@imports` keep the boot files thin while still loading shared doctrine and the lesson ledger.
- Workspace trust must be enabled before project-local Gemini settings and commands take effect.

## Knowledge Anchor

`docs/LESSONS_LEARNED.md` is the only canonical knowledge anchor for durable sprint lessons.

- Claude loads it through imports in `CLAUDE.md`.
- Gemini loads it through imports in `GEMINI.md`.
- Codex reaches it through `AGENTS.md`, generated agent instructions, and validation prompts.

## Sync Commands

Use the omni-factory engine directly for deterministic regeneration:

```bash
python3 scripts/omni_factory.py sync-claude --project <name>
python3 scripts/omni_factory.py sync-codex --project <name>
python3 scripts/omni_factory.py sync-gemini --project <name>
```

The shell wrappers remain convenience entrypoints only.

## Unified Hook Lifecycle

`policies/hooks.json` is the canonical authoring surface for hooks across all three hosts. The renderers compile each record into the host's native format, so one canonical hook propagates identically to Claude, Codex, and Gemini.

### Schema

Top-level structure (version 3):

```json
{
  "version": 3,
  "shared":  [ <hook-record>, ... ],
  "claude":  [ <hook-record>, ... ],
  "codex":   [ <hook-record>, ... ],
  "gemini":  [ <hook-record>, ... ]
}
```

- `shared` — hooks that should propagate to every host listed in the record's `targets` array. This is the preferred place for cross-host guardrails.
- `claude` / `codex` / `gemini` — host-specific hooks that only make sense on one host.

Each hook record:

```json
{
  "id": "pre-tool-execution-guardian",
  "description": "short human-readable purpose",
  "event": "pre_tool_use",
  "matcher": "Bash",
  "handler": {
    "type": "command",
    "command": "bash ~/Projects/_agent_forge/skills/global/telemetry-guardian/guardian.sh"
  },
  "targets": ["claude", "codex", "gemini"],
  "timeout_ms": 5000,
  "status_message": "optional short status line"
}
```

The v3 `handler.type` can be `command`, `http`, `mcp_tool`, `prompt`, or `agent`. Claude currently renders all five native handler types. Codex and Gemini currently render active `command` hooks only, matching their current public docs; non-command examples in `policies/hooks.json` stay disabled until a host-safe sentinel exists. Current triad artifacts prove active command-hook surface reachability, not live dispatch for dormant non-command handlers.

Event names use snake_case and are translated to each host's native casing by the renderer:

| Canonical event | Claude        | Codex           | Gemini         |
|-----------------|---------------|-----------------|----------------|
| `pre_tool_use`  | `PreToolUse`  | `PreToolUse`    | `BeforeTool`   |
| `post_tool_use` | `PostToolUse` | `PostToolUse`   | `AfterTool`    |
| `permission_request` | `PermissionRequest` | `PermissionRequest` | unsupported |
| `user_prompt_submit` | `UserPromptSubmit` | `UserPromptSubmit` | unsupported |
| `pre_commit`    | `PreToolUse`  | `PreToolUse`    | `BeforeTool`   |
| `post_edit`     | `PostToolUse` | `PostToolUse`   | `AfterTool`    |
| `session_start` | `SessionStart`| `SessionStart`  | `SessionStart` |
| `stop`          | `Stop`        | `Stop`          | `SessionEnd`   |

**Gemini event-name correctness note (Sprint 1, 2026-04-26):** Gemini CLI v0.39 expects PascalCase event names (`BeforeTool` / `AfterTool` / `BeforeAgent` / `AfterAgent` / `BeforeModel` / `AfterModel` / `BeforeToolSelection` / `SessionStart` / `SessionEnd` / `Notification` / `PreCompress`), not the camelCase pattern Claude uses. Earlier roadmap iterations had `preToolUse` / `postToolUse` here; those were silently broken (Gemini's hook dispatcher never recognized the keys) and the triad validator's `hook_surface_for` only passed because it did a substring command-path match. Both bugs are fixed: aliases corrected and `hook_surface_for` now also requires the per-host expected event key to be a top-level key in the rendered hooks payload. Live-invocation proof: `runtime/validation/hook-probe/20260426-035313/gemini/` (Gemini blocked `--no-verify` for real, exit 0).

**Codex event-name correctness note (Sprint 2, 2026-04-27):** Current Codex hook docs use PascalCase hook keys in `.codex/hooks.json` (`PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `Stop`). Earlier factory output used snake_case keys such as `pre_tool_use`, which was another silent-correctness risk. Sprint 2 corrected `_EVENT_ALIASES["codex"]`, regenerated all governed project surfaces, and tightened `hook_surface_for()` to check every active hook record's expected native key. Evidence: `runtime/validation/triad/20260427-085402/summary.json`.

### Rendered surfaces

Per sync, the factory writes:

- Claude → `<project>/.claude/settings.json` with a top-level `"hooks"` block.
- Codex → `<project>/.codex/hooks.json` (existing), plus `[features] codex_hooks = true` in `.codex/config.toml` when any hook applies.
- Gemini → `<project>/.gemini/settings.json` with a `"hooks"` block merged alongside `context` and `mcpServers`.

Global user-home hook surfaces (`~/.claude/settings.json`, `~/.gemini/settings.json`) are left alone by the factory; the canonical delivery is per-project.

### Adding a new hook

1. Author the record in `policies/hooks.json` (usually under `shared`).
2. If the command points to a script, put the script under the owning skill (for example, `skills/global/telemetry-guardian/guardian.sh`) and reference it with an absolute path or `~/Projects/_agent_forge/...`.
3. Re-run `sync-claude` / `sync-codex` / `sync-gemini` for every governed project.
4. Re-run `verify-agent-forge.py` — it checks handler shape, target host names, known canonical events, command script paths, and async rules.
5. Re-run `validate-triad-runtime.py` — it checks that each rendered host hook file contains every active hook record's expected native event key.

### Seeded hook: `pre-tool-execution-guardian`

The factory ships one standard hook: the `telemetry-guardian` pre-tool veto. It calls `skills/global/telemetry-guardian/guardian.sh`, which reads the tool invocation on stdin, matches against a short deny list (`--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777 on home), and exits 1 to block or 0 to allow. Set `AGENT_FORGE_GUARDIAN=off` to bypass for a single session; bypasses are logged to `~/.agent-forge/guardian.log`.

## Universal State Layer

`policies/memory.json` is the canonical authoring surface for the cross-host session-state layer. The renderers compile its sections into a per-project `MEMORY.md` plus a sibling `.forge_state/` directory. Host-native memory surfaces are synchronized around that canonical file; they are not treated as doctrine.

### Schema

```json
{
  "version": 2,
  "sections": [{ "id": "...", "name": "...", "append_only": true|false, "host_writers": [...], "host_readers": [...], "description": "..." }],
  "retention":      { "max_entries_per_section": 50, "warn_at": 40 },
  "secrets_policy": "deny",
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

Section ids are stable; renaming is a breaking change because section anchors (`<!-- section:<id> -->`) are addressed by id from the `memory-archivist` skill.

### Rendered surfaces

Per sync, the factory writes:

- `<project>/MEMORY.md` — managed markdown with one H2 per section, an HTML anchor comment, and `<!-- entries:start -->` / `<!-- entries:end -->` markers the archivist appends between.
- `<project>/.forge_state/README.md` — short explanation of the directory.
- `<project>/.forge_state/manifest.json` — `version`, project name, sections (id/name/append_only), retention, secrets_policy, `last_updated`.
- `<project>/.forge_state/archivist.log` — append-only audit trail produced when the archivist runs.
- `<project>/.forge_state/bridge.json` — host-local memory bridge state, native target paths, and last outbound/inbound hashes.
- `<project>/.forge_state/bridge.log` — append-only JSONL audit trail produced by `memory-bridge`.

### Host reachability

- **Claude / Codex:** the repo-root `AGENTS.md` Read Order names `<project>/MEMORY.md` as the universal session-state file. Both hosts already follow `AGENTS.md` (Claude via `CLAUDE.md` imports, Codex auto-loads `AGENTS.md`).
- **Gemini:** generated `<project>/GEMINI.md` adds `@MEMORY.md` to its import chain. Gemini loads it natively.

### Adding or removing a section

1. Edit `policies/memory.json`. Bump `version` if the change is breaking.
2. Re-run `sync-claude` / `sync-codex` / `sync-gemini` for every governed project.
3. Re-run `verify-agent-forge.py` — it now confirms every governed project's `MEMORY.md` carries every section anchor and that `.forge_state/manifest.json` is well-formed.
4. Re-run `validate-triad-runtime.py` — `memory_surface_for(host, project_root)` will fail for any project whose anchors don't match the new schema.

### `memory-archivist` skill

The companion capability that exercises the layer. Three subcommands: `append` (timestamped, one entry per call, secrets-deny on write), `validate` (confirms anchors and manifest are well-formed), `summary` (per-section counts and retention warnings). See `skills/global/memory-archivist/SKILL.md` for the contract; live invocation is `python3 ~/Projects/_agent_forge/skills/global/memory-archivist/archivist.py append --project <root> --section <id> --entry "<text>" --source claude|codex|gemini`.

### `memory-bridge` skill

The bridge capability synchronizes host-local memory files around canonical `<project>/MEMORY.md`:

- Outbound: `python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py outbound --project <root> --host claude|codex|gemini`
- Inbound: `python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py inbound --project <root> --host claude|codex|gemini`
- Status: `python3 ~/Projects/_agent_forge/skills/global/memory-bridge/bridge.py status --project <root>`

Native targets:

- Claude: `~/.claude/projects/<encoded-project-path>/memory/MEMORY.md` — true machine-local Claude auto memory.
- Codex: `<project>/.codex/memory/AGENTS_MEMORY.md` — project sidecar; do not mutate generated `~/.codex/memories/` state.
- Gemini: `<project>/.gemini/memory/MEMORY.md` — project sidecar; Gemini Auto Memory currently extracts procedural skills, while facts still flow through `GEMINI.md` context.

Bridge hooks are host-specific records in `policies/hooks.json`: `memory-bridge-outbound-<host>` on canonical `session_start`, and `memory-bridge-inbound-<host>` on canonical `stop` (`SessionEnd` on Gemini). They run async, are idempotent by content hash, and reapply the memory secrets-deny policy before export or import.
