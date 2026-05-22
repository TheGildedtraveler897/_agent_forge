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

### 2026-05-22 - MCP stdio transport must not use sh-c on Windows

- `Date:` 2026-05-22
- `Context:` Windows VM readiness pass for NRC ship. `global-mcp.json` originally used `"command": "sh", "args": ["-c", "exec python3 \"$HOME/...\""]` to get shell-side `$HOME` expansion. Native Windows (no WSL) has no `sh`, so the MCP server would fail to start on coworker workstations.
- `Lesson:` The canonical authoring file (`global-mcp.json`) should not embed shell wrappers for env-var expansion. The renderer must expand `${HOME}` / `$HOME` / `~` at render time so the rendered host config contains an absolute path and a direct binary invocation. This decouples canonical portability (the file is operator-machine-agnostic) from rendered-config concreteness (the host config is operator-machine-specific by design).
- `Architectural Decision:` `omni_factory.normalize_mcp_server` now passes the transport dict through `_expand_transport_paths` which calls `os.path.expanduser` and `os.path.expandvars` on `command`, `args`, and `cwd`. Canonical files use `${HOME}/...` style placeholders. No `sh -c` wrappers permitted in the canonical.
- `Evidence:` `global-mcp.json:21-26` (canonical change), `scripts/omni_factory.py:_expand_transport_paths` (new helper), `scripts/verify-agent-forge.py` exits 0 after the change, `docs/plans/feat-windows-vm-readiness.md` (Track I plan).
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § MCP rendering rules — once the lesson holds across the first real Windows VM smoke test.
- `Status:` active

### 2026-05-22 - Line endings must be platform-specific by file type

- `Date:` 2026-05-22
- `Context:` Same Windows readiness pass. The repo had no `.gitattributes`, so a Windows operator cloning the repo could get auto-converted line endings that break `.sh` shebang parsing (LF expected) or generate spurious "no newline at end of file" warnings in PowerShell tooling (CRLF expected).
- `Lesson:` Cross-platform repos must explicitly state expected line endings per file type. Default `text=auto` behavior is not deterministic across operating systems.
- `Architectural Decision:` Added `.gitattributes` at repo root. POSIX scripts, Python, JSON, TOML, YAML, and Markdown enforce `eol=lf`. PowerShell, CMD, and BAT enforce `eol=crlf`. Archive types marked binary.
- `Evidence:` `.gitattributes` at repo root.
- `Promotion Target:` None — this is a one-time fix; the file documents the policy on disk.
- `Status:` active

### 2026-05-22 - Plan persistence layer survived its first multi-merge cycle

- `Date:` 2026-05-22
- `Context:` Track F (2026-05-22) introduced `docs/plans/<branch-slug>.md` plan persistence with status frontmatter and `branch-finisher` Step 5b archival on merge. Within the same day, three merges exercised the path: `feat/ship-prep`, `feat/onboarding-overhaul`, and (pending) `feat/windows-vm-readiness`. Each plan transitioned `awaiting-approval` → `approved` → `in-progress` → `completed` and archived to `docs/archive/PLANS_COMPLETED.md`.
- `Lesson:` The new layer is durable under real-world multi-track sprint pressure. The frontmatter status field plus the archive-on-merge contract is enough to let a peer agent re-ground from disk after a session glitch. No additional MCP tool, no policy schema, no validator extension was needed; the layer is pure project-governance convention.
- `Architectural Decision:` Treat plan persistence as the reference pattern for future agent-governance primitives that don't need host-native rendering. The five-step omni-factory pattern (policy + renderers + verifier + validator + skill) is reserved for primitives that are surfaced into host-native config; project-governance concerns get a lighter pattern.
- `Evidence:` `docs/archive/PLANS_COMPLETED.md` entries; commits in master: c5807bf (Track F implementation), c9732a6 (first persisted plan), and the subsequent merge archives.
- `Promotion Target:` `docs/CONOPS.md` § Plan Persistence Layer — already promoted in Track F.
- `Status:` promoted
