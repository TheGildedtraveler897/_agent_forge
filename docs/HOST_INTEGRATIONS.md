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

Top-level structure (version 2):

```json
{
  "version": 2,
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
  "command": "bash ~/Projects/_agent_forge/skills/global/telemetry-guardian/guardian.sh",
  "targets": ["claude", "codex", "gemini"],
  "timeout_ms": 5000,
  "status_message": "optional short status line"
}
```

Event names use snake_case and are translated to each host's native casing by the renderer:

| Canonical event | Claude       | Codex         | Gemini        |
|-----------------|--------------|---------------|---------------|
| `pre_tool_use`  | `PreToolUse` | `pre_tool_use`| `preToolUse`  |
| `post_tool_use` | `PostToolUse`| `post_tool_use`| `postToolUse`|
| `pre_commit`    | `PreToolUse` | `pre_tool_use`| `preToolUse`  |
| `post_edit`     | `PostToolUse`| `post_tool_use`| `postToolUse`|
| `session_start` | `SessionStart`| `session_start`| `sessionStart`|
| `stop`          | `Stop`       | `stop`        | `stop`        |

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
4. Re-run `verify-agent-forge.py` — it now checks that every referenced script path exists.
5. Re-run `validate-triad-runtime.py` — it now checks that each rendered host hook file contains the expected guardian entry.

### Seeded hook: `pre-tool-execution-guardian`

The factory ships one standard hook: the `telemetry-guardian` pre-tool veto. It calls `skills/global/telemetry-guardian/guardian.sh`, which reads the tool invocation on stdin, matches against a short deny list (`--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777 on home), and exits 1 to block or 0 to allow. Set `AGENT_FORGE_GUARDIAN=off` to bypass for a single session; bypasses are logged to `~/.agent-forge/guardian.log`.

## Universal State Layer

`policies/memory.json` is the canonical authoring surface for the cross-host session-state layer. The renderers compile its sections into a per-project `MEMORY.md` plus a sibling `.forge_state/` directory, so Claude Auto-Memory, Codex Chronicle, and Gemini Memory v2 all read and write the same brain.

### Schema

```json
{
  "version": 1,
  "sections": [{ "id": "...", "name": "...", "append_only": true|false, "host_writers": [...], "host_readers": [...], "description": "..." }],
  "retention":      { "max_entries_per_section": 50, "warn_at": 40 },
  "secrets_policy": "deny"
}
```

Section ids are stable; renaming is a breaking change because section anchors (`<!-- section:<id> -->`) are addressed by id from the `memory-archivist` skill.

### Rendered surfaces

Per sync, the factory writes:

- `<project>/MEMORY.md` — managed markdown with one H2 per section, an HTML anchor comment, and `<!-- entries:start -->` / `<!-- entries:end -->` markers the archivist appends between.
- `<project>/.forge_state/README.md` — short explanation of the directory.
- `<project>/.forge_state/manifest.json` — `version`, project name, sections (id/name/append_only), retention, secrets_policy, `last_updated`.
- `<project>/.forge_state/archivist.log` — append-only audit trail produced when the archivist runs.

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
