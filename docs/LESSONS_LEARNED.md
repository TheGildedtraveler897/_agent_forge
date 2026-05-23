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

### 2026-05-22 - Host-specific canonical hook events are intentional, not drift

- `Date:` 2026-05-22
- `Context:` SOTA 2026 drift audit (Track 4b of `feat-sota-2026-alignment`). The Phase 1 research found Gemini CLI fires `BeforeAgent`, `AfterAgent`, `BeforeToolSelection`, `AfterModel`, `BeforeModel` lifecycle events that have no Claude / Codex equivalent — they are semantically distinct lifecycle points, not just renames. Audit flagged this as a drift risk: if the canonical schema only represents Claude/Codex's event set, authors cannot write hook records that fire on Gemini-only events.
- `Lesson:` Verification showed all five events were already wired into `scripts/omni_factory.py:_EVENT_ALIASES` by an earlier SOTA pass — `None` aliases for Claude and Codex, PascalCase native names for Gemini. The canonical schema represents the events; the renderer drops them silently for hosts whose alias is `None`. The asymmetric design is intentional: not every canonical event needs all-three coverage. Per-host depth wins over forced symmetry.
- `Architectural Decision:` Document the asymmetry explicitly so future contributors don't try to "fix" it. CONOPS § Hook Governance gains a bullet stating host-specific canonical events are explicitly allowed. `policies/hooks.json` top-level description gains a sentence naming the Gemini-only events as an example of the pattern.
- `Evidence:` `scripts/omni_factory.py:869-873` (Claude `None` aliases), `:909-913` (Codex `None` aliases), `:930-934` (Gemini native aliases). `docs/CONOPS.md` § Hook Governance (new bullet). `policies/hooks.json` description string (updated).
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Unified Hook Lifecycle — already references `_EVENT_ALIASES`; should explicitly list the Gemini-only events with a one-line "no Claude / Codex equivalent" note.
- `Status:` active

### 2026-05-22 - Codex subagents already render as TOML (verified non-drift)

- `Date:` 2026-05-22
- `Context:` SOTA 2026 drift audit (Track 4a of `feat-sota-2026-alignment`). The primary-source research agent inferred that Codex subagents require a `[agent]` TOML section based on Codex 2026 vendor docs, but did not read an actual rendered file. Audit flagged this as a potential drift surface to verify.
- `Lesson:` On verification, `omni_factory.py` already renders `.codex/agents/<skill>.toml` files with the required Codex schema (`agent_forge_managed = true`, top-level `name`, `description`, `sandbox_mode`, `developer_instructions`, and a `[[skills.config]]` table for the referenced `SKILL.md` path). The audit's `[agent]` section guess was a stylistic inference; flat top-level keys are also valid TOML and match Codex's documented expected schema. No drift.
- `Architectural Decision:` Keep the current renderer behavior. If Codex's vendor docs ever explicitly require a `[agent]` wrapper section, that's a deeper rewrite gated on primary-source confirmation; not warranted by inference.
- `Evidence:` `tomllib.load()` succeeds on every `.codex/agents/*.toml` in five different governed projects (`RoboNaaz`, `playlist-archive`, `homelab`, `ZorroClaw`, `jarvis`). All files have the same five top-level keys plus `[[skills.config]]`. Per-file inspection: `/home/pheonixprotocol/Projects/RoboNaaz/.codex/agents/brand-guardian.toml`.
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md` § Codex subagent rendering — document the actual schema so future contributors don't re-investigate.
- `Status:` active

### 2026-05-22 - Plan persistence layer survived its first multi-merge cycle

- `Date:` 2026-05-22
- `Context:` Track F (2026-05-22) introduced `docs/plans/<branch-slug>.md` plan persistence with status frontmatter and `branch-finisher` Step 5b archival on merge. Within the same day, three merges exercised the path: `feat/ship-prep`, `feat/onboarding-overhaul`, and (pending) `feat/windows-vm-readiness`. Each plan transitioned `awaiting-approval` → `approved` → `in-progress` → `completed` and archived to `docs/archive/PLANS_COMPLETED.md`.
- `Lesson:` The new layer is durable under real-world multi-track sprint pressure. The frontmatter status field plus the archive-on-merge contract is enough to let a peer agent re-ground from disk after a session glitch. No additional MCP tool, no policy schema, no validator extension was needed; the layer is pure project-governance convention.
- `Architectural Decision:` Treat plan persistence as the reference pattern for future agent-governance primitives that don't need host-native rendering. The five-step omni-factory pattern (policy + renderers + verifier + validator + skill) is reserved for primitives that are surfaced into host-native config; project-governance concerns get a lighter pattern.
- `Evidence:` `docs/archive/PLANS_COMPLETED.md` entries; commits in master: c5807bf (Track F implementation), c9732a6 (first persisted plan), and the subsequent merge archives.
- `Promotion Target:` `docs/CONOPS.md` § Plan Persistence Layer — already promoted in Track F.
- `Status:` promoted
