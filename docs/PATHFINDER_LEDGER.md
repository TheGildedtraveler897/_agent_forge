# Pathfinder Ledger

## Reading Guide

**What this file is.** The raw research archive of the Omni-Factory. Sprawling brain-dumps from reconnaissance sprints, architectural musings, SOTA CLI surveys, gap analyses, and post-mortems. Append-only. Earlier entries are never rewritten — supersede with a new dated entry instead.

**What this file is not.** It is **not** an actionable plan. It is **not** the durable doctrine surface. Findings here mature through three stages:
1. Raw recon → this ledger.
2. Synthesized actionable work → `docs/PATHFINDER_ROADMAP.md` (Architectural Upgrades + Capability Backlog).
3. Concrete sprint with exact Codex/Claude execution prompts → `docs/SPRINT_BACKLOG.md`.

**Where to go for each need:**
- I want context on *why* a decision was made → read this Ledger.
- I want to know *what's next to build* → read `docs/PATHFINDER_ROADMAP.md`.
- I want to *start working right now* → read `docs/SPRINT_BACKLOG.md`.
- I want to know *what was just shipped* → read `docs/HANDOFF.md`.
- I want validated lessons that should bind future work → read `docs/LESSONS_LEARNED.md`.

**Append-only discipline.** When new research arrives:
- Add a new dated, titled section at the bottom.
- Do not edit prior sections in place.
- If a prior finding is superseded, write a new "supersedes" entry naming the prior section.
- Promote durable findings into the Roadmap or Lesson Ledger rather than letting them rot here.

---

## Origin Note

This ledger was created during the 2026-04-25 Token-Burn Reconnaissance sprint that gathered the SOTA reference baseline for Claude Code, OpenAI Codex, Gemini CLI, and the NVIDIA Nemotron bash-computer-use paradigm, plus three independent web searches on multi-agent orchestration, LLM-agnostic frameworks, and advanced MCP routing. That sprint's full output is preserved verbatim below in Sections 1 through 3 (Phase 1 baseline, Phase 2 recon entries, Phase 3 Crucible).

The 2026-04-26 Sprint 1 execution surfaced additional research-shaped findings that did not fit cleanly into the prior structure; those are appended in Section 4.

---

Append-only reconnaissance ledger for the 2026-04-25 Token-Burn Recon sprint.
This file records raw findings as they are gathered, before any synthesis.
Do not rewrite earlier entries — append only.

---

## Session Header

- **Operator:** Claude Opus 4.7 (acting as Chief Systems Architect)
- **Date:** 2026-04-25
- **Constraints:** No code or script modifications. Append-only ledger. Checkpoint after every major recon step.
- **Source repo state:** seven feature commits on `master` ending at `d402d3a`. Verifier EXIT=0. Triad validator green at 28 skills with `hook_pass: true memory_pass: true` across Claude / Codex / Gemini.

---

## Phase 1 — Local Baseline Summary (ingested 2026-04-25)

### What the Omni-Factory currently is

`_agent_forge` is a single canonical authoring repo that generates host-native delivery surfaces for three coding agent CLIs (Claude Code, OpenAI Codex, Gemini CLI) plus a cross-host shared brain. Author once, render outward, validate via runtime probe.

### Canonical authoring sources

- `skills/**/SKILL.md` — 28 capability packs (workflow discipline, domain experts, meta-skills).
- `teams/*.json` — team manifests with role contracts, collapse/escalation rules.
- `projects.json` — six governed projects (`jarvis`, `RoboNaaz`, `ZorroClaw`, `homelab`, `ZorroForge/factory`, `playlist-archive`).
- `global-mcp.json` — shared MCP server inventory (currently intentionally empty until first real shared server).
- `policies/hooks.json` — schema v2 hook records with `shared` array + per-host arrays.
- `policies/memory.json` — schema v1 universal-memory section schema (5 sections, retention 50/warn-at-40, secrets_policy=deny).
- `registry.json` — generated compatibility output, never authoring.

### Generator (`scripts/omni_factory.py`)

Discovers canonical sources, renders host-native surfaces:
- Claude: `~/.claude/{agents,commands}`, `<project>/.claude/{agents,commands,skills,settings.json}`, `<project>/.mcp.json`.
- Codex: `~/.agents/skills`, `<project>/.agents/skills`, `<project>/.codex/{agents,config.toml,hooks.json}`.
- Gemini: `~/.gemini/{agents,commands,skills,GEMINI.md}`, `<project>/{GEMINI.md,.gemini/{agents,commands,skills,settings.json}}`.
- Cross-host: `<project>/MEMORY.md`, `<project>/.forge_state/{README.md,manifest.json}`.

### Validation gates

- `verify-agent-forge.py` — structural verifier: file presence, schema coherence, hook script existence, memory anchors, manifest fields. EXIT=0 currently.
- `validate-triad-runtime.py` — runtime gate: probes live `claude` / `codex` / `gemini` CLIs, gets enumerated skill list, falls back to filesystem-escalated when bubblewrap blocks Codex shell. Now also gates on `hook_surface_for` and `memory_surface_for`. Last green: `runtime/validation/triad/20260425-174222/`, all three hosts `hook_pass: true memory_pass: true`, 28 skills.

### Universal pre-tool guardrail

- `telemetry-guardian` skill (POSIX `guardian.sh`) wired via `policies/hooks.json` shared record.
- Deny list: `--no-verify`, `--no-gpg-sign`, force-push to protected branches, `git reset --hard <ref>`, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777.
- Bypass via `AGENT_FORGE_GUARDIAN=off`; bypasses logged to `~/.agent-forge/guardian.log`.

### Universal state layer

- Per-project `MEMORY.md` with 5 sections (build_commands, project_quirks, active_tasks [rewriteable], recent_decisions, known_failures).
- Reachable from all three hosts: Gemini `@MEMORY.md` import, Claude/Codex via `AGENTS.md` Read Order entry #5.
- `memory-archivist` skill provides `append`/`validate`/`summary` subcommands with secrets-deny patterns; audit log per project.

### Knowledge anchor

- `docs/LESSONS_LEARNED.md` — append-first, normalized entries (Date / Context / Lesson / Architectural Decision / Evidence / Promotion Target / Status).
- 9 entries currently. Recent: workflow-discipline assimilation, triad validator promotion, propagation-default fix, hook lifecycle, memory layer, sandbox-marker drift, compound-bash stall.

### Workflow discipline chain (from AGENTS.md)

`spec-architect` → `execution-planner` → `tdd-engineer` → `subagent-dispatcher` → `verification-gate` → `branch-finisher`. Escape hatches: `root-cause-analyst`, `code-review-doctrine`, `skill-author`.

### Pathfinder roadmap status (pre-recon)

Architectural Upgrades:
- #1 Universal State Layer — ✅ shipped 2026-04-25
- #2 Unified Hook Lifecycle — ✅ shipped 2026-04-24
- #3 MCP Namespace Prefixing & Routing — not started
- #4 Continuous Evolution / Anti-Rot — not started

Capability Backlog:
- #1 `memory-archivist` — ✅ shipped 2026-04-25
- #2 `router-overseer` — not started
- #3 `telemetry-guardian` — ✅ shipped 2026-04-24
- #4 `routine-auditor` — not started
- #5 `auto-loop` — not started
- #6 `wiki-compiler` — not started
- #7 `crew-director` — not started

### Known open debts

- No real shared MCP server in `global-mcp.json` (governance wired, operationally unproven).
- Codex live-CLI probe blocked by `bwrap` on this machine; escalation works but cleaner sandbox path desired.
- `bootstrap-project.sh --existing` and `--with-local-skills` need live exercise.
- No real Debian VM or macOS suitcase proof yet.
- Team manifests are conceptual only — no executable orchestration.
- Repo has no git remote → weekly watchdog routine blocked.
- Triad validator confirms enumeration, not invocation correctness.

### Doctrinal posture

- Append-first: lessons land in `docs/LESSONS_LEARNED.md` before any doctrine moves.
- Promotion-gated: CONOPS §Hook Governance and §Capability Model both gated on a third paired sprint succeeding.
- Native boot files stay native (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`).
- Canonical-first; generated surfaces never hand-edited.
- Triad validator is the mandatory final gate after any canonical change.
- Compound shell commands are bridge-fragile; prefer narrow tool calls.

---

## Phase 2 — SOTA Live Reconnaissance (entries appended below as gathered)

### 2.1 — Claude Code (https://code.claude.com/docs/en/overview, /memory, /hooks) — fetched 2026-04-25

**Surfaces & install.** Five first-class surfaces: Terminal, VS Code, JetBrains, Desktop app (macOS/Windows), Web (claude.ai/code), iOS Claude app. Native installers: shell script, Homebrew, WinGet, apt/dnf/apk. Same engine across all surfaces; CLAUDE.md, settings, MCP servers shared.

**CLAUDE.md memory model (mature 2026 shape).**
- Two complementary systems loaded every session: **CLAUDE.md** (human-authored) and **auto memory** (Claude-authored).
- CLAUDE.md scopes: Managed policy (`/Library/Application Support/ClaudeCode/CLAUDE.md`, `/etc/claude-code/CLAUDE.md`, `C:\Program Files\ClaudeCode\CLAUDE.md`), project (`./CLAUDE.md` or `./.claude/CLAUDE.md`), user (`~/.claude/CLAUDE.md`), local (`./CLAUDE.local.md`).
- `.claude/rules/*.md` — modular topic files. **YAML frontmatter `paths:` glob field path-scopes a rule** so it only loads when Claude reads matching files. Saves context dramatically.
- Symlinks supported in `.claude/rules/`. Circular detection. Cross-project shared rule libraries.
- `@path/to/import` syntax expands at launch, recursive depth ≤ 5. Both `~/` and relative paths.
- `claudeMdExcludes` setting (glob list) skips ancestor CLAUDE.md files in monorepos.
- `--add-dir` + `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` loads memory from extra dirs.
- Block-level HTML comments in CLAUDE.md are stripped from context (token savings).
- AGENTS.md is NOT auto-loaded by Claude. Bridge: `@AGENTS.md` from CLAUDE.md.
- `--append-system-prompt` for true system-prompt-level instructions (vs CLAUDE.md which is delivered as a user message after the system prompt).

**Auto memory (v2.1.59+).**
- Per-project memory dir: `~/.claude/projects/<project>/memory/`.
- Project path is derived from git repository root → all worktrees of one repo share auto memory.
- First **200 lines or 25KB** of `MEMORY.md` auto-loaded every session. Topic files (`debugging.md`, `api-conventions.md`) load on demand.
- Toggle: `/memory` command, `autoMemoryEnabled` setting, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` env var.
- `autoMemoryDirectory` setting (rejected from project settings to prevent shared-project redirect attacks).
- "Writing memory" / "Recalled memory" UI indicators.
- Subagents can have their own auto memory (`enable-persistent-memory`).
- Survives `/compact` only at project-root CLAUDE.md level; nested CLAUDE.mds reload lazily.

**Hooks lifecycle (26 events).**
- Session: `SessionStart`, `SessionEnd`, `InstructionsLoaded`.
- User input: `UserPromptSubmit`, `UserPromptExpansion` (slash command expansion).
- Tool loop: `PreToolUse`, `PermissionRequest`, `PermissionDenied` (auto-mode classifier denial), `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`.
- Agents/tasks: `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`.
- Context/config: `ConfigChange`, `CwdChanged`, `FileChanged`, `PreCompact`, `PostCompact`.
- MCP: `Elicitation`, `ElicitationResult`.
- Notifications/worktrees: `Notification`, `Stop`, `StopFailure`, `WorktreeCreate`, `WorktreeRemove`.
- Stdin: structured JSON (session_id, transcript_path, cwd, permission_mode, hook_event_name, agent_id, agent_type) plus event-specific payload (tool_name/tool_input/tool_use_id/duration_ms).
- Stdout: rich JSON with `decision: "block"`, `hookSpecificOutput.permissionDecision: "allow|deny|ask|defer"`, `updatedInput`, `additionalContext`, `updatedPermissions[]` with `addRules|replaceRules|removeRules|setMode|addDirectories|removeDirectories`, `destination: session|localSettings|projectSettings|userSettings`.
- Exit codes: 0 success (parse stdout JSON), 2 blocking error (show stderr to Claude, prevent action), 1/3+ non-blocking (first line of stderr in transcript).
- 5 hook handler types: `command`, `http` (POST endpoint with header env-var interpolation + `allowedEnvVars` allow-list), `mcp_tool` (call MCP server tool with `${tool_input.file_path}` substitution), `prompt` (yes/no via Claude model), `agent` (spawn subagent with Read/Grep/Glob).
- Async hooks: `async: true` (run in background, don't block), `asyncRewake: true` (background + wake Claude on exit code 2 with stderr as system reminder). Parallel hook deduplication (identical command/URL run once).
- Matcher syntax: `*` / empty / omitted = all; letters/digits/`_`/`|` = exact tool name list; other chars = JS regex. Per-event matcher targets vary (tool name, session source, notification type, agent type, compaction trigger, config layer, error type, load reason, command name, MCP server name).
- Conditional filtering with `if` field using permission rule syntax: `"Bash(git *)"`, `"Edit(*.ts)"`.
- Skill/Agent frontmatter can declare hooks scoped to that component's lifetime.
- Plugin hooks at `<plugin>/hooks/hooks.json`. `allowManagedHooksOnly: true` blocks user/project/plugin hooks (admin enforcement).
- `/hooks` slash command: read-only browse all configured hooks by event with source attribution (`User`, `Project`, `Local`, `Plugin`, `Session`, `Built-in`).
- Output capped at 10,000 chars; overflow saved to file with preview.

**Skills system.**
- Skills (`/en/skills`) are slash-commandable workflow packages, distinct from CLAUDE.md (always loaded) and rules (path-scoped). Loaded on demand or when relevance is detected.
- `--setting-sources` controls which settings layers participate.

**Subagents / Agent SDK.**
- Native `Task` tool / lead-agent model: spawn multiple Claude Code agents that work in parallel; lead coordinates and merges.
- `Agent SDK` (`/en/agent-sdk/overview`) — build custom agents using Claude Code tooling with full orchestration/tool/permission control.

**Routines (Claude scheduled jobs).**
- `Routines` run on Anthropic-managed infra → keep running when laptop is off.
- Triggers: scheduled (cron-like), API events, GitHub events.
- Created from: web UI, Desktop app, `/schedule` slash command in CLI.
- Distinct from `Desktop scheduled tasks` (run locally, direct file/tool access) and `/loop` (in-session prompt repeat).

**Cross-surface session teleportation.**
- `claude --teleport` pulls a long-running web/iOS task into a terminal session.
- `/desktop` hands off terminal session to Desktop app for visual diff review.
- `Remote Control` continues local session from phone or browser.
- `Channels` push events from Telegram/Discord/iMessage/webhooks into a session.
- `Dispatch` (Desktop) — message a task from phone, opens a Desktop session.

**Permission system / sandboxing.**
- 6 permission modes: `default`, `plan`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`.
- Managed settings: `permissions.deny` (tool/path block list), `sandbox.enabled` (sandbox isolation), `forceLoginMethod`, `forceLoginOrgUUID`, `claudeMdExcludes`.
- Permission updates from hooks at runtime → can persist to session/local/project/user settings.

**MCP integration.**
- `/en/mcp` open standard. Read Google Drive, update Jira, Slack data, custom tooling.
- MCP tools follow naming: `mcp__<server>__<tool>`. Hooks can match `mcp__memory__.*` etc.
- MCP server hooks via `mcp_tool` handler type → call a server tool from a hook.
- `Elicitation` event lets MCP servers request user input; `ElicitationResult` hooks the response.

**CI/CD & external integrations.**
- GitHub Actions (`/en/github-actions`), GitLab CI/CD (`/en/gitlab-ci-cd`), GitHub Code Review (`/en/code-review`), Slack (`/en/slack`), Chrome (`/en/chrome`).

**Headless / Unix-pipe mode.**
- `claude -p "<prompt>" --output-format text` for piping. `--dangerously-skip-permissions`.
- `tail -200 app.log | claude -p "Slack me if anomalies"` — log-pipe pattern is canonical 2026.

**Third-party providers.** Anthropic, Bedrock, Foundry, Vertex AI all supported as backends.

**`/init` flow.** Auto-generates CLAUDE.md by analyzing the codebase. `CLAUDE_CODE_NEW_INIT=1` enables interactive multi-phase flow (asks which artifacts to set up: CLAUDE.md / skills / hooks; explores via subagent; presents reviewable proposal).

### 2.2 — OpenAI Codex CLI (developers.openai.com/codex/cli + features + changelog) — fetched 2026-04-25

**Sandbox.** Codex runs arbitrary commands inside macOS Seatbelt or Linux bubblewrap sandboxes. Multiple writable dirs grantable alongside the workspace. Permission profiles now **round-trip across TUI sessions, user turns, MCP sandbox state, and shell escalation** (v0.125.0). Filesystem permissions support `deny-read` glob policies and managed `deny-read` requirements (v0.122.0). Platform sandbox enforcement; isolated `codex exec` runs that ignore user config/rules. Windows sandbox setup hardened to avoid broad user-profile and SSH-root grants.

**Approval modes.** Auto, Read-only, Full Access. `on-failure` deprecated → `on-request` (interactive) or `never` (non-interactive). Project hooks and exec policies now require **trusted workspaces** (v0.122.0).

**MCP.**
- Stored in `config.toml` (default `~/.codex/config.toml`, project-scoped at `.codex/config.toml` for trusted projects only).
- `/mcp verbose` slash command — full MCP server diagnostics, resources, resource templates (v0.123.0).
- `mcpServers` and top-level server maps both accepted in `.mcp.json` for plugins (v0.123.0).
- MCP bearer-token fields refined in config schema (v0.125.0).
- Local stdio MCP launches fixed for relative commands without explicit cwd (v0.124.0).

**Hooks (stable as of April 2026, v0.124.0).**
- Configured inline in `config.toml` and via managed `requirements.toml`.
- Hooks **observe MCP tools as well as `apply_patch` and long-running Bash sessions**.
- The factory's existing `.codex/hooks.json` path is the project-scoped variant; canonical config now also supports inline-in-config.toml syntax — schema convergence opportunity.

**AGENTS.md auto-discovery.** Refactored into `AgentsMdManager` (v0.122.0). Config loading lives behind narrower filesystem and manager abstractions. AGENTS.md remains the auto-loaded boot file.

**Subagents / multi-agent (v0.122.0–0.125.0).**
- `[agents]` config table: subagent role configs, each with TOML config layer, role guidance shown when spawning.
- Codex only spawns subagents when explicitly asked — opt-in, not implicit.
- Realtime handoffs: background agents receive transcript deltas; can explicitly stay silent (v0.123.0).
- "MultiAgentV2" thread limits enforced in config schema (v0.125.0 breaking change rejects conflicts).
- Rollout tracing records tool, code-mode, session, and multi-agent relationships (v0.125.0).

**App-server / remote.**
- App-server integrations support **Unix socket transport, pagination-friendly resume/fork, sticky environments** (v0.125.0).
- Remote TUI connections with WebSocket auth.
- App-server sessions manage **multiple environments and choose an environment per turn** (v0.124.0).
- App-server plugin management: remote plugin installation and marketplace upgrades.

**Plugins / marketplace.**
- Plugin workflows: tabbed browsing, inline enable/disable, marketplace removal (v0.122.0).
- Remote, cross-repo, or local marketplace sources.
- Remote plugin marketplaces listable and readable directly with larger result pages (v0.124.0).

**Computer use.** Listed as a top-level feature on the Codex CLI features page. (Detail page would need separate fetch; current confirmation: surface exists.)

**Memory model.**
- AGENTS.md auto-discovery is the durable instruction layer.
- Project-scoped trust model gates `.codex/config.toml` reads.
- Token compaction + prompt caching + predicted outputs all listed as features.
- "Chronicle" long-term memory was hyped in older roadmaps; the changelog and features page do not surface it under that name in 2026-04 — the durable equivalents in current docs are AGENTS.md + auto-discovery + the resume/fork session model. **Treat "Chronicle" as superseded vocabulary.**

**Headless / non-interactive.**
- `codex exec` is the canonical non-interactive subcommand.
- `codex exec --json` now reports **reasoning-token usage for programmatic consumers** (v0.125.0).
- `codex resume` reopens earlier threads.

**TUI ergonomics (v0.122.0–0.124.0).**
- `/side` conversations for quick side questions.
- Queued input supports slash commands and `!` shell prompts while work runs.
- Plan Mode can start implementation in fresh context with context-usage shown before deciding.
- Quick reasoning controls: `Alt+,` lowers, `Alt+.` raises (v0.124.0).
- Tool discovery and image generation enabled by default (v0.122.0).
- Higher-detail image handling + original-detail metadata for MCP and `js_repl`.

**Slash commands.** `/review`, `/mcp`, `/mcp verbose`, `/side`, `/schedule` (cross-host parity with Claude Code naming).

**Model providers.** Built-in `amazon-bedrock` provider with configurable AWS profile support (v0.123.0). Model providers own model discovery; AWS/Bedrock account state exposed to app clients (v0.125.0). First-class Bedrock SigV4 support (v0.124.0).

**Eligible ChatGPT plans default to Fast service tier unless opted out** (v0.124.0).

**`codex features enable/disable <feature>`** writes to `~/.codex/config.toml`. With `--profile`, writes to that profile instead of root config.

**Sandbox detection drift (relevance to our `host_sandbox_blocked()`).** This machine emits `bwrap: loopback: Failed RTM_NEWADDR` plus `needs access to create user namespaces` and `shell tool failed before command execution`. The 2026-04 sandbox enforcement changes mean error wording can keep moving — our marker list curation discipline is correct.

### 2.3 — Gemini CLI (geminicli.com/docs + hooks/reference) — fetched 2026-04-25

**Latest stable: v0.39.0 (2026-04).**

**GEMINI.md.** Hierarchical project context file. Auto-loaded by walking up the directory tree. `@imports` syntax keeps it thin. The current alternative to hooks for repetitive instructions is GEMINI.md.

**Hook events (named differently from Claude/Codex — critical).**
- Tool: `BeforeTool`, `AfterTool` (NOT `preToolUse`/`postToolUse` — that is current canonical naming).
- Agent: `BeforeAgent`, `AfterAgent`.
- Model: `BeforeModel`, `BeforeToolSelection`, `AfterModel`.
- Lifecycle: `SessionStart`, `SessionEnd`, `Notification`, `PreCompress`.
- **Naming drift impact on our factory:** `policies/hooks.json` `_EVENT_ALIASES["gemini"]` currently maps `pre_tool_use → preToolUse`. **This is wrong.** Correct mapping is `pre_tool_use → BeforeTool`, `post_tool_use → AfterTool`, `session_start → SessionStart`, `stop → SessionEnd`. **Action item: hotfix the Gemini alias map.**
- Stdin: `session_id, transcript_path, cwd, hook_event_name, timestamp` + event-specific fields (`tool_name`, `prompt`, `llm_request`).
- Stdout: `decision: "allow"|"deny"|"block"`, `reason`, `systemMessage`, `continue` (false → stop agent loop), `suppressOutput`, `hookSpecificOutput` (event-specific modifications).
- Stdout MUST be pure JSON — no other plaintext. (Our guardian script needs verification — it currently prints JSON only; OK.)
- Matcher syntax: regex for tool events, exact-string for lifecycle events. `mcp_<server>_<tool>` pattern.
- Default timeout 60,000 ms (configurable per hook).
- Exit codes: 0 success, 2 system block, other = non-fatal warning.
- Settings.json hook block: `{matcher, sequential: false, hooks: [{type: "command", command, name, timeout, description}]}`.

**MCP.**
- **MCP Prefixing is canonical and automatic.** Every discovered MCP tool is prepended with `mcp_<serverAlias>_<toolName>` to avoid collisions across server catalogs. Pattern: `mcp_<server_name>_<tool_name>`.
- This is the SOTA pattern that our roadmap Architectural Upgrade #3 was modeling on.
- Our factory's MCP renderer currently writes raw mcpServers blocks; Gemini auto-prefixes on discovery, but explicit canonical prefixing in the registry would harmonize the namespace across hosts.
- Multi-transport: stdio, SSE, streamable HTTP.

**Subagents.**
- "Subagents" — specialized agents for specific tasks.
- "Remote subagents" — connect to and use remote agents.
- Subagent local execution + tool isolation.

**Memory model.**
- Per-session state. Resume + rewind conversations.
- Checkpointing for automatic session snapshots.
- Token caching.
- **Auto Memory is experimental** (🔬 marked) — newer feature, mirrors Claude's Auto Memory.
- Memory management for persistent instructions and facts (separate from GEMINI.md).

**Trust + sandbox.**
- "Trusted folders" gate enables project-local settings/commands.
- Sandboxing isolates tool execution.
- Plan Mode = safe, read-only mode for planning.
- Plan Mode + Model Steering combine (experimental).

**Extensions / customization.**
- Extensions system — packageable behavior.
- Hook Support in Extensions is an open feature request (Issue #14449) — not yet GA → extension authors cannot bundle hooks today.
- Theme personalization, model routing with automatic fallback resilience, system prompt override (instruction replacement).

**Headless mode.** Non-interactive programmatic/scripting interface.

**IDE integration.** Native support.

**Web search/fetch.** Built-in.

**Model steering (experimental).** Influence model behavior at runtime.

**2026 experimental features (🔬):** Auto Memory, Git worktrees, Model steering, Notifications, Plan Mode with model steering.

**Slash commands.** `/memory show` (memory inspection), `/help`, others surface-specific.

### 2.4 — NVIDIA Nemotron Bash Computer-Use Agent (developer.nvidia.com blog) — fetched 2026-04-25

**Paradigm name.** Multi-turn agentic execution with **interactive bash control** — distinct from "prompt-and-call" / one-shot tool use.

**Loop topology.**
1. **Outer loop** — accept user input → append to `Messages` history.
2. **Inner loop** — query model → if model emits tool call → human-in-the-loop confirm (`Execute '{cmd}'? [y/N]:`) → run via subprocess → append `stdout`/`stderr`/updated `cwd` to history → repeat until model returns a non-tool answer.

**Tool surface.** Exactly one tool: `exec_bash_command(cmd: str)` exposed via JSON schema. Return shape: `{stdout, stderr, cwd}`. Single tool, multi-turn.

**State maintained across commands (the missing piece in stateless tool use).**
- `Messages` class — conversation/exchange history.
- `Bash` class — persistent **working directory** state. Each command is wrapped: `{cmd};echo __END__;pwd`. Output is split at `__END__` to extract actual stdout from trailing `pwd`. After every command, the agent's view of `cwd` is updated, so subsequent `cd` / relative paths work as a real terminal session would.
- This solves the "agent forgets it just `cd`'d" failure mode that plain tool-call shells exhibit.

**Sandbox / safety model.**
- Human-in-the-loop approval **before every execution** — not after. The user is the runtime gate.
- Allowlist enforced at runtime in `Bash` class: e.g., `ls`, `cat`, `grep` permitted; `rm`, `mv`, `rmdir`, `sudo` blocked.
- System prompt warns against dangerous ops in addition to the allowlist (defense in depth).

**Prompt structure.**
- `/think` flag activates reasoning mode (Nemotron-specific).
- Role definition: "Bash assistant".
- Allowed-command list (mirrors runtime allowlist).
- Output interpretation instructions: "after every `cd`, list files".
- Error recovery instructions: interpret stderr, inform user, choose next step.

**Output capture / observation.**
- Synchronous `subprocess.run` with `capture_output=True` (polling, not streaming).
- Delimiter pattern (`echo __END__;pwd`) ensures clean separation of stdout from cwd state.
- Both `stdout` and `stderr` fed back to the model as structured data on next turn.

**OS targets.** Linux + macOS + WSL with `executable="/bin/bash"` explicit.

**Model.** NVIDIA Nemotron Nano 9B v2. Local ≥24 GB VRAM / ~20 GB disk, or cloud via OpenRouter / build.nvidia.com.

**Reusable architectural patterns.**
- **Tool wrapper abstraction** — encapsulate execution logic + state in a class, not a function.
- **LLM abstraction** — separate API calls from business logic.
- **Message history abstraction** — explicit conversation state object.
- **Human-in-the-loop decorator** — `ExecOnConfirm` in LangGraph version wraps tool calls for approval.
- **Allowlist at two layers** — prompt guidance + runtime enforcement.
- **`create_react_agent()` (LangGraph)** auto-manages loop topology, tool dispatch, result passing.

**Why this matters for our factory.**
- Our `telemetry-guardian` is a deny-list pre-execution hook — Nemotron's pattern is allow-list + persistent-cwd + every-command-confirm. Allow-list and persistent-cwd are missing from our model.
- Our skills currently assume host CLIs do command execution. We do NOT have a "build your own bash agent" surface, but the Nemotron pattern is the canonical reference for `auto-loop` in our backlog (Karpathy autoresearch-style propose→edit→test→evaluate→ratchet).
- The interactive bash paradigm is the right shape for our future `auto-loop` and `crew-director` capabilities — both need persistent shell state across many turns.

### 2.5 — Independent SOTA searches — fetched 2026-04-25

#### 2.5a Multi-agent CLI orchestration

**Frameworks in the wild (2026):**
- **overstory (jayminwest/overstory).** Spawns worker agents in **git worktrees via tmux**, coordinates via a custom **SQLite mail system**, merges back with **tiered conflict resolution**. Persistent coordinator agent does task decomposition + dispatch. Tool-call guards turn agent sessions into orchestrated workers.
- **MetaSwarm (dsifry/metaswarm).** Self-improving multi-agent framework targeting **Claude Code + Gemini CLI + Codex CLI** (same triad as us). 18 specialized agents, 13 orchestration skills, full SDLC coverage. TDD enforcement + quality gates + spec-driven dev. **This is the closest external comparable to Agent Forge.**
- **ClawTeam.** Leader agent decomposes goals → specialized worker agents execute autonomously → shared task board with auto dependency resolution → inter-agent messaging system.
- **Kimi K2.6 Agent Swarm.** 300 sub-agents, 4,000 coordinated steps in a single session. Coordinator manages full lifecycle: split / assign / monitor / merge.
- **Copilot Swarm Orchestrator (Agent Wars).** Enforces **proof-of-work and cost tracking** across multi-agent runs.

**Two dominant 2026 patterns:**
- **Conductor (centralized, hierarchical).** One coordinator decomposes + dispatches. Predictable, auditable, lower throughput.
- **Swarm (decentralized, parallel).** Many peers; emergent coordination. Higher throughput, harder to audit.
- **Hybrid is the production default.** Conductor for high-stakes routing + swarm for parallel execution within an assigned subtree.

**Agent-as-a-Tool pattern (Claude Code's `TeammateTool` + `Task` system).** Treat each subagent as a callable tool with structured input/output. Lead agent calls `dispatch_legal_counsel(question)` etc., then merges responses. This is what `router-overseer` (our Capability #2) was modeling.

**Cost+verification posture (Copilot Swarm).** Each spawned agent must report (a) tokens consumed, (b) proof-of-work artifact (test output, file diff). Coordinator aggregates → cost guardrails enforced at the swarm level. **Missing from our factory entirely.**

#### 2.5b LLM-agnostic agent frameworks

**Players:**
- **OpenCode.** Provider-agnostic coding agent, **75+ LLM providers** including local Ollama / llama.cpp. No vendor lock-in.
- **Junie CLI (JetBrains, Mar 2026 beta).** LLM-agnostic; one-click migration from Claude Code, Codex, and others. Customization via guidelines, custom agents, agent skills, commands, MCP.
- **AgenticOS (Pharns/AgenticOS).** Deterministic AI agent orchestration with **explainable routing, audit-grade logging, governed execution across multiple LLM providers**. Supports Claude, Codex, Gemini with **auto-routing, keyword + AI-powered profile selection, audit-grade logging**. Closest to our governance posture.
- **LangGraph / CrewAI / AutoGen.** Model-agnostic at the framework level. Production pattern: **model tiering** — fast/cheap model (Haiku 4.5, GPT-5.4-mini) for triage/routing agents; capable model (Opus, GPT-5.4) for complex reasoning agents.
- **Spring AI Agent Skills.** Skills defined once → work across OpenAI / Anthropic / Gemini / any supported model. Same pattern as our omni-factory but provider-agnostic at the runtime level too.
- **Google ADK (April 2025).** Hierarchical agent tree + native A2A (Agent-to-Agent) protocol — agents from different frameworks can talk. **This is the cross-framework interop layer that's emerging.**

**Pattern convergence:** every serious framework now treats "skills" as portable capability packs, "model tiering" as the cost-control discipline, and "audit-grade logging" as a governance requirement. We have skills + the model_tier frontmatter field already. We do NOT have audit-grade logging at the orchestration layer.

#### 2.5c Advanced MCP routing

**Tool-name collisions are the canonical SOTA problem.**
- MCP itself does not support namespaces in the function-calling protocol (as of the GitHub Discussion #128 thread).
- **Best-practice convention:** server-prefix every tool name. `github.list_repos`, `slack.send_message`, `filesystem.delete_file` — clear ownership, prevents tool hijacking.
- Gemini CLI's automatic `mcp_<server>_<tool>` rendering is the de facto SOTA implementation. Claude Code matches by pattern in hooks (`mcp__memory__.*`).

**Transport layer (MCP 2026):**
- **stdio** — local servers, single client, low overhead.
- **Streamable HTTP** — remote servers, many clients, HTTP-native auth (bearer tokens, OAuth).
- **SSE** — older streaming variant.
- Codex CLI added explicit MCP bearer-token field to config schema in v0.125.0.

**Elicitation pattern.** MCP servers can request user input via the protocol. Claude Code surfaces this as `Elicitation` / `ElicitationResult` hook events. This is how an MCP tool can ask for clarification mid-call without breaking the loop.

**Roots and resources.** MCP "roots" let a client expose filesystem boundaries to a server (which paths are addressable). "Resources" are server-exposed read-only context (like attached docs). Both are how MCP brings non-tool context into the model.

**Trust + auth tiers (2026 MCP best practice):**
- Local stdio = trust the binary, no network.
- Remote streamable HTTP = require bearer token + audit log every call + rate-limit by client identity.
- Codex restricts project-scoped `.codex/config.toml` MCP servers to **trusted workspaces only** — security model has hardened.

**The `forge.<service>.<tool>` pattern (our Architectural Upgrade #3) is correctly aligned with the SOTA convergence.** Our value-add over Gemini's `mcp_<server>_<tool>` would be that it's *canonical-first* — declared in `global-mcp.json` and rendered identically across all three hosts, instead of relying on Gemini-only auto-prefix.

---

## Phase 3 — The Crucible: Gap Analysis & Vulnerability Sweep

Brutal, honest, unflattering. Where the factory is fragile and what we are missing vs the 2026-04 SOTA.

### Critical bugs (ship-blocker for next sync)

**C1. Gemini hook event names are wrong.**
Our `_EVENT_ALIASES["gemini"]` maps `pre_tool_use → preToolUse`, `post_tool_use → postToolUse`, `session_start → sessionStart`, `stop → stop`. Gemini CLI 2026 actually expects **`BeforeTool`, `AfterTool`, `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeToolSelection`, `SessionStart`, `SessionEnd`, `Notification`, `PreCompress`**. Our triad validator's `hook_surface_for(gemini)` checks for the *literal string* `"telemetry-guardian"` or `"guardian.sh"` in the rendered settings — so it passes today *only because the substring match is loose enough to find the command path*, not because the event registration is correct. Gemini will likely never actually invoke our hook because the event name doesn't match anything its dispatcher recognizes. **Severity: BLOCKER.** This is a silent correctness failure masked by a substring-loose validator.

**C2. Triad validator confirms enumeration, not invocation.**
The validator asks each host CLI to *list* its visible skills and confirms the guardian record *exists in JSON*. It does NOT invoke a real tool call to confirm the hook *fires*. Bug C1 would have been caught by an end-to-end "run a `--no-verify` git command in Gemini and confirm it was blocked" test. **Severity: HIGH.** The whole guardian premise is undermined on Gemini until proved live.

### Architectural fragility

**A1. Stateless tool calls vs interactive bash control (Nemotron paradigm).**
Our skills assume the host CLI dispatches one tool call at a time and the host owns shell state. We have no factory-managed concept of a **persistent shell session with cwd, env, and history that survives across an agent's turns**. This blocks `auto-loop` (Karpathy autoresearch-style), blocks `crew-director` (multi-stage swarm orchestration), blocks any "the agent runs three commands in a row that depend on the previous cwd" workflow. The Nemotron blog gives the exact pattern: `Bash` class wrapping subprocess + `{cmd};echo __END__;pwd` delimiter + persistent cwd tracker. **We are not building this; SOTA implementations are.**

**A2. Deny-list-only safety vs allow-list + persistent-cwd.**
`telemetry-guardian` is a deny-list. Nemotron and several 2026 swarm frameworks pair a deny-list with an **allow-list at runtime + human-in-the-loop confirm before execution + per-agent cost tracking**. Our model trusts the deny list to be exhaustive; the SOTA assumes the deny list is incomplete and gates on positive permission. This becomes load-bearing the moment we add a swarm.

**A3. No audit-grade orchestration log.**
AgenticOS, Copilot Swarm Orchestrator, and Kimi K2.6 all converge on **proof-of-work + cost-tracking + explainable routing**. We have `~/.agent-forge/guardian.log` (single hook bypass log) and `runtime/validation/triad/<stamp>/` (validator artifacts). We do NOT have a per-session orchestration ledger that records: which agent was dispatched, why (routing decision), what tokens it spent, what artifacts it produced, and whether the artifact passed verification. The `routine-auditor` capability in our backlog hints at this but the design assumed CI-only. The SOTA pattern is **inline, every-session, append-first**.

**A4. No cross-framework interop (A2A protocol).**
Google ADK ships native A2A (Agent-to-Agent). It lets our factory talk to *frameworks we don't own*. As LangGraph/CrewAI/AutoGen-built agents proliferate, A2A becomes the universal handshake. We have nothing here. The cost is small to add (it's a JSON-over-HTTP protocol) but the strategic cost of being absent is large.

**A5. MCP namespace prefixing not actually canonical.**
Gemini auto-prefixes `mcp_<server>_<tool>`. Claude pattern-matches `mcp__<server>__<tool>`. Our `global-mcp.json` is declarative but doesn't enforce canonical prefixes, and our renderer doesn't transform the registered server-id into a canonical namespace at sync time. The moment we add 5+ MCP servers, names collide silently — we'd repeat exactly the `pre_tool_use` aliasing failure mode but at the tool-name layer instead of the event-name layer. **Severity: latent.** Bites the second a real shared MCP lands.

**A6. No persistent task board across sessions.**
Overstory uses **SQLite mail** + **git worktrees via tmux** as the durable orchestration substrate. ClawTeam uses a "shared task board with auto dependency resolution". MetaSwarm coordinates 18 agents with 13 orchestration skills. We have `MEMORY.md` (session-scoped state) and `LESSONS_LEARNED.md` (durable lessons) but no **task graph** — no place that records "task T depends on T1 and T2, T1 is done, T2 is in flight, owner = subagent X". The `active_tasks` section in `MEMORY.md` is plain text, not a graph. This blocks `crew-director`.

**A7. No cost / token-budget enforcement at the orchestration layer.**
Copilot Swarm Orchestrator enforces **proof-of-work + cost tracking** at the coordinator. The 2026 multi-agent reality is that an unbounded swarm burns money fast. We have `model_tier` in skill frontmatter but no runtime mechanism that *consults the budget* before dispatching, *records* what was spent, or *reports* cost back to the operator. As soon as we ship `auto-loop` or `crew-director` we'll burn tokens uncontrollably.

**A8. No explainable routing.**
AgenticOS markets **explainable routing + audit-grade logging** as table stakes. When an operator asks "why did `router-overseer` pick `legal-counsel` instead of `infra-architect`?", we have no answer because the routing decision isn't a first-class artifact. This will become acute once we build `router-overseer`.

**A9. Codex `Chronicle` vocabulary is dead.**
Our own roadmap document references "Codex Chronicle" as a specific durable-memory feature. The 2026-04 Codex docs do not surface a feature called Chronicle anywhere. Either it was renamed, never shipped under that name, or got folded into AGENTS.md auto-discovery + resume/fork. **The roadmap doc is internally stale on this point.** Low impact on code; high impact on operator confidence in the roadmap as a current document.

### Missing capabilities vs 2026 SOTA

**M1. Auto Memory writer/reader bridge.** Claude Code's auto-memory writes to `~/.claude/projects/<project>/memory/MEMORY.md` (machine-local). Gemini's experimental Auto Memory has a parallel path. **Our cross-host `MEMORY.md` lives at `<project>/MEMORY.md` (canonical, repo-tracked).** These are *different files* and there is no bridge. A learning Claude saves via auto-memory does not propagate to Gemini or to our canonical `MEMORY.md`. The goal of the universal state layer was specifically to fix this; we shipped the canonical file but not the bridge to Claude/Gemini's *native* auto-memory. **Severity: HIGH.** This is the single biggest gap between the roadmap promise and the actual delivery.

**M2. Routines / scheduled agents.** Claude Code ships `Routines` (Anthropic-managed, runs when laptop off, cron-like + API-event + GitHub-event triggers). Codex has `codex resume` + app-server multi-environment sessions. We have a *documented* watchdog routine spec in `TECH_DEBT.md` blocked on no git remote. The SOTA is integrated, ours is paper.

**M3. Plugin / marketplace surface.** Claude Code ships plugins with `/plugin` UI, `enabledPlugins`, `allowManagedHooksOnly`, `${CLAUDE_PLUGIN_ROOT}` env vars. Codex has remote plugin marketplaces. We have skills + teams as our "extension" model. Skills are great but not discoverable / installable from a third party. As the ecosystem grows, this matters.

**M4. Subagent persistent memory.** Claude Code subagents can have *their own* auto-memory. Our `subagent-dispatcher` skill enforces fresh-context isolation but doesn't grant the subagent durable state across runs. For long-running specialist agents (e.g., a `legal-counsel` that should remember last quarter's filings), this is a real gap.

**M5. Session teleportation / cross-surface continuity.** Claude `--teleport`, `/desktop` handoff, `Remote Control`, `Channels` (Telegram/Discord/iMessage/webhooks → session). We have `_agent_forge` as a static repo with no session-fluidity story.

**M6. Model tiering as a runtime decision, not just metadata.** Our skill frontmatter has `model_tier: any` / `light` / `heavy` etc. as documentation. There is no orchestration layer that *reads* it and routes accordingly. SOTA frameworks (LangGraph, CrewAI, AutoGen) bake this into the dispatcher.

**M7. Knowledge base compilation (`wiki-compiler`).** RAG is now correctly framed as brittle by 2026 SOTA. The `wiki-compiler` capability in our backlog *is* the right answer (compile raw docs into structured Markdown that all agents read directly). It is not built.

**M8. End-to-end E2E hook test.** No test that says "configure hook X, fire a real tool call on host Y, observe the hook actually intercepted and modified behavior, restore state". This is what would have caught bug C1.

**M9. Hook handler diversity.** Claude Code has 5 handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent`. Our renderer emits `command` only. We are not exploiting `http` (remote validation), `mcp_tool` (call an MCP tool from a hook), or `agent` (spawn a subagent to verify a decision). Significant lost leverage.

**M10. Async / asyncRewake hooks.** Claude Code 2026 supports `async: true` (background) and `asyncRewake: true` (background + wake Claude on exit code 2). Our renderers don't expose these flags from `policies/hooks.json` even though the schema could trivially carry them.

**M11. Path-scoped rules.** Claude Code's `.claude/rules/*.md` with YAML frontmatter `paths:` glob is a first-class path-scoping mechanism. Our skills load globally. We do not have a "this skill body only loads when working under `src/api/`" mechanism. Context cost is paid in full every session.

**M12. `claudeMdExcludes`-style cross-team isolation.** In a monorepo where multiple teams have their own `_agent_forge` overlays, you'd want to exclude rival teams' rules. We have no equivalent.

**M13. `--append-system-prompt` parity.** The CLAUDE.md memory model docs explicitly note that CLAUDE.md is delivered as a *user message after the system prompt*, not as part of the system prompt itself. For instructions that must be system-prompt-level (the strongest binding), Claude Code offers `--append-system-prompt`. Codex has its `requirements.toml` for managed system policy. Our model assumes AGENTS.md / MEMORY.md / SKILL.md frontmatter are equally binding — they aren't. Anything we route through `<project>/MEMORY.md` is the weakest possible binding (post-system-prompt user message).

### Doctrine fragility

**D1. Promotion gates may be too conservative.**
Two consecutive sprints (hook lifecycle, memory layer) followed the same canonical-schema → three-renderers → skill rhythm. The lesson ledger correctly identifies this and gates CONOPS promotion on a third sprint. The risk is the opposite: by the time we get to a third sprint, the SOTA has moved (e.g., A2A protocol becomes table stakes), and we're promoting a 2026-04 doctrine into a 2026-Q3 reality. **Mitigation: the gate should be both "third sprint succeeds" *and* "review SOTA hasn't moved". Add a re-recon step before promotion.**

**D2. Triad-only horizon.**
Everything in our doctrine assumes Claude / Codex / Gemini. Junie CLI, OpenCode, Hermes, Cursor's CLI, and Kimi K2.6 swarms exist now. Our `targets:` frontmatter list is hardcoded to the triad. Adding a fourth host (Junie or OpenCode) would touch every renderer, every test, every doc. The architecture is one host removed from "tetrad-friendly".

**D3. No deprecation or supersession workflow.**
`LESSONS_LEARNED.md` has `Status: superseded` as a value but nothing in the system reads it. A superseded lesson is still loaded. There's no compaction or archive of stale lessons.

**D4. The factory has no story for failures of the factory itself.**
If `omni_factory.py` regresses, what catches it? `verify-agent-forge.py` and `validate-triad-runtime.py` are both *invoked by humans*. There is no agent that watches the factory itself. The proposed `routine-auditor` would do this but is paper. **The factory currently lacks the very capability it's most famous for: governance.** Eat your own dog food.

### Operator-experience fragility

**O1. No live MCP server proves the MCP-renderer code path.**
`global-mcp.json` is intentionally empty. The renderer is exercised by zero data. Bug A5 (namespace prefixing) is plausibly already broken; we just won't see it until the first real entry lands.

**O2. No real Debian VM proof, no real macOS proof.**
Suitcase doctrine is paper.

**O3. No git remote.**
Watchdog routine blocked. No public surface for collaborators. The factory cannot be dogfooded by anyone but the current operator.

**O4. Tool-result delivery stalls (post-mortem 2026-04-25).**
We documented a workflow lesson but did not add an *automatic* re-grounding mechanism. If a future operator (or a subagent we dispatch) hits the same stall, they have to remember the lesson manually. A `Stop` hook that detects "no token motion + outstanding tool call > N minutes" and auto-emits a self-ping would close this.

### Summary scorecard

| Axis | State | SOTA | Gap |
|---|---|---|---|
| Cross-host skill delivery | ✅ Production | ✅ Same | — |
| Cross-host hook lifecycle | ⚠️ Bug C1 (Gemini) | ✅ Mature | Silent correctness failure |
| Cross-host memory (canonical) | ✅ Shipped | ⚠️ Convergent | Bridge to native auto-memory missing (M1) |
| Sandbox / safety | ⚠️ Deny-only | ✅ Allow + deny + HITL | A2 |
| MCP rendering | ⚠️ No canonical prefixing | ✅ Auto-prefix on Gemini | A5, M9 |
| Multi-agent orchestration | ❌ Conceptual | ✅ Conductor / swarm hybrid live | A6, A7, A8 |
| Persistent shell state | ❌ Absent | ✅ Nemotron pattern | A1 |
| Audit-grade orchestration log | ❌ Absent | ✅ AgenticOS / Copilot Swarm | A3 |
| Cross-framework interop (A2A) | ❌ Absent | ✅ Google ADK ships native | A4 |
| Routines / scheduled agents | ❌ Paper | ✅ Claude Routines live | M2 |
| Plugin / marketplace | ❌ Absent | ✅ Claude / Codex both ship | M3 |
| Hook handler diversity | ⚠️ command-only | ✅ 5 types | M9 |
| Async / asyncRewake hooks | ❌ Absent | ✅ Claude 2026 | M10 |
| Path-scoped rules | ❌ Absent | ✅ Claude `.claude/rules/` | M11 |
| Model tiering at runtime | ⚠️ Metadata only | ✅ LangGraph / CrewAI runtime | M6 |
| Wiki/RAG compilation | ❌ Paper | ✅ Several frameworks ship | M7 |
| E2E hook firing test | ❌ Absent | ⚠️ Few frameworks have it | C2, M8 |
| Self-governance (factory governs itself) | ❌ Absent | ⚠️ Emerging | D4 |

**Net read.** We are in a strong position on the *canonical-first* axis (skills/hooks/memory rendering) and weak on the *runtime / orchestration / proof-of-correctness* axes. The factory ships the schema better than anyone but does not exercise the schema as rigorously as the SOTA frameworks. Bug C1 is concrete and ship-blocker; the rest is roadmap fuel.

---

## Section 4 — Sprint 1 Execution Research (appended 2026-04-26)

Sprint 1 (Hook-Alias Hotfix C1 + live-hook-prober B1) shipped on 2026-04-26 (commits `f2cea42` and `a15200f`). The execution surfaced several research-shaped findings that did not fit the prior Crucible structure and are recorded here for future architects.

### 4.1 — The `--dangerously-skip-permissions` Trap

**Discovery context.** During Sprint 1 Part B (live-hook-prober integration), the Claude headless probe was initially run with `claude -p ... --dangerously-skip-permissions` because that flag is what the existing triad validator's skill-enumeration probe uses (where it is harmless). The first live invocation result returned `===ALLOWED===` — meaning the seeded `telemetry-guardian` hook *did not block* `git commit --no-verify`, even though the rendered `.claude/settings.json` was correctly registered.

**Mechanism.** `--dangerously-skip-permissions` is documented as "skip approval prompts" but in practice it bypasses the **entire pre-tool hook system**, not just the permission UI. Pre-tool hooks are part of Claude's permission infrastructure. When the flag is set, the dispatcher short-circuits the hook chain entirely. A probe run with the flag will silently report `allow` for every command, regardless of how correct the rendered hook surface is. The probe becomes useless — strictly worse than no probe — because it produces a false-positive signal that hooks are firing when they are not.

**Architectural implication.** Any test that wants to *prove* a hook fires must NOT use `--dangerously-skip-permissions`. The skill enumeration probes (which only ask Claude to list its skills, not invoke a Bash tool) are unaffected and may keep using the flag. The live hook probe must use `--permission-mode default` (which is what the `prober.sh` Sprint 1 implementation now does).

**Research note for future hosts.** Codex has its own analogous skip flags (`--dangerously-bypass-approvals-and-sandbox`, `--full-access`) and Gemini may grow them. Any future cross-host test must audit each host's "skip" flags against the question "does this also bypass hooks?" before relying on them.

### 4.2 — The Headless-CLI Live-Probe Limitation Class

**Discovery context.** With `--dangerously-skip-permissions` ruled out per §4.1, the next attempt was `claude -p ... --permission-mode default`. The result: the CLI hung indefinitely, was killed by the outer `timeout(1)`, and produced no usable verdict.

**Mechanism.** Claude in headless `-p` mode is non-interactive: there is no stdin attached for the user to answer permission prompts. The default permission mode requires interactive approval for protected tool calls. When a hook denies a Bash invocation, Claude attempts to surface a permission dialog. In an interactive TUI session this would render as a prompt the user can answer; in `-p` mode, there is no surface to render to, so the CLI sits waiting for an answer that physically cannot arrive. `timeout(1)` eventually kills the parent `claude` process, but not always cleanly.

**Architectural implication.** Headless live-probing of Claude hooks is fundamentally not viable without one of:
- An interactive session (out of scope for an automated triad gate).
- A pre-approved permission rule for the test command in the test project (not portable, requires per-project setup).
- A new "headless permission decision" surface that Claude does not currently expose.

The Sprint 1 live-hook-prober treats this as `escalated` (with `observed: headless_permission_constraint`), mirroring the Codex sandbox-block doctrine. The honest report is: "the probe could not complete in this CLI mode," not "the hook didn't fire."

**Research note for the long arc.** This is a structural limitation of the agent CLI category, not a Claude-specific bug. The path to closing it is the `forge-shell` capability (B4) — a persistent shell session under our control where we know the permission posture, instead of relying on the host CLI's headless contract. Real Claude live-probing should run inside a `forge-shell` session, not a `claude -p` invocation.

### 4.3 — The Leftover-Subprocess-Tree Stall Class

**Discovery context.** Two distinct stalls during Sprint 1 Part B blocked progress for measurable wall-clock time. Earlier sessions had documented one stall class: bridge fragility on bulky tool-result delivery (the 2026-04-25 compound-bash post-mortem). This was different.

**Mechanism.** When the harness's Bash tool invokes a long-running CLI (`claude -p`, `codex exec`, `gemini -p`) that internally spawns a subprocess tree (claude → node → MCP servers, or codex → bubblewrap → bash → ...), the outer `timeout(1)` wrapper does not always cleanly reap the entire descendant tree. Specifically observed during Sprint 1: a `claude` PID (11660) survived after `timeout` killed its direct parent, kept open file descriptors that the harness's process-monitoring layer was tracking, and as a result the harness could not deliver the tool-result back to the agent. This is distinct from the compound-bash class:

| Class | Trigger | Symptom | Mitigation |
|---|---|---|---|
| Compound-bash bridge fragility (2026-04-25) | Multi-section JSON / mixed stdout-stderr / `&&;`-chained commands | The shell finished; the encoded result was lost in transit | Narrow tool calls; `git commit -F /tmp/file` |
| Leftover-subprocess-tree (2026-04-26) | Long-running CLI that spawns descendants surviving `timeout(1)` SIGTERM | The harness still sees open FDs; tool-result delivery never completes | Do not invoke long-running CLIs through the harness Bash tool; run from a real terminal |

**Architectural implication.** Some workflows that are perfectly safe in a real terminal are simply not viable through this Claude Code session's Bash tool. The `live-hook-prober` is a clear example: it works correctly when run directly (Gemini probe took ~8 seconds and produced exit 0 verdict pass on the first attempt outside the harness), but it stalls when the same probe is invoked transitively through this session.

**Operator rule.** For long-running CLI probes (any operation that spawns a host CLI as a child process and waits >30 seconds for completion), prefer:
1. Direct invocation from a real terminal session.
2. Scheduled execution as a Routine (Claude) or scheduled task (Codex / Gemini).
3. CI-style execution from a GitHub Action or equivalent — the outer process is the runner, not the harness.

**Research note for the long arc.** This is a known limitation of agent-bash-tool architectures generally, not specific to Claude Code. As the SOTA evolves toward `forge-shell`-style persistent sessions (Capability B4), the friction here decreases — but until then, the rule "do not invoke long-running CLI tool calls transitively through an agent harness's bash tool" is load-bearing.

### 4.4 — The `BeforeTool` Alias Drift Discovery (Process Note)

**Why this finding is worth preserving.** The C1 bug was not exotic. The C1 bug was a single line of incorrect aliases shipped in 2026-04-23 that sat undetected through *two complete sprints* (the hook lifecycle ship and the universal state layer ship), passed every triad surface validation, and was only discovered when the Token-Burn Recon explicitly read the official Gemini hooks reference page. **The validator was lying** because it did substring matching against the command path string (`"telemetry-guardian"` or `"guardian.sh"` in body) rather than verifying the rendered event key was actually one Gemini's dispatcher recognized.

**Process implication.** Surface validation that does substring or "contains" matching against arbitrary JSON is structurally weak. It catches "the hook record disappeared entirely" but not "the hook record exists with a meaningless event name". The strict fix is to enumerate the host's expected event vocabulary as a curated allow-list (now `_EXPECTED_HOOK_EVENT_KEY` in `validate-triad-runtime.py`) and require the rendered surface to use one of those exact keys.

**Pattern recognition for future architects.** Whenever the omni-factory crosses a host-native semantic boundary (event names, sandbox markers, permission strings, MCP tool prefixes, settings keys), the validator must check against a **curated allow-list of valid native values**, not a substring of the command path or a structural-shape-only check. The prior loose-substring approach cost two sprints of false confidence. The new tight-allow-list approach is now the canonical pattern; replicate it for any future cross-host semantic surface.

### 4.5 — The Live Gemini Probe Evidence Trail

**Why this matters.** Sprint 1's primary success criterion was: "prove the C1 fix actually works at runtime, not just on paper." That proof now exists at `runtime/validation/hook-probe/20260426-035313/gemini/`:

```json
{
  "host": "gemini",
  "command": "git commit --no-verify -m probe",
  "expected": "block",
  "observed": "block",
  "verdict": "pass",
  "evidence_path": ".../runtime/validation/hook-probe/20260426-035313/gemini",
  "reason": ""
}
```

`exit 0`. Hook actually fired. Real Gemini CLI dispatcher recognized the `BeforeTool` event key and invoked `telemetry-guardian/guardian.sh`, which read the JSON tool invocation from stdin, matched `--no-verify` against the deny list, and exited 1 to block.

**Why this is the most important artifact in the entire factory's history.** It is the first end-to-end runtime proof that the cross-host promise of the Omni-Factory ("the same hook fires identically on every host from one canonical schema") is real on Gemini. Before 2026-04-26 we had it on Claude (always assumed), Codex (filesystem-escalated), and Gemini (rendered surface, but the dispatcher was silently dropping it). Now we have it on all three, with one of them by direct live invocation.

**Research note.** Future audits of the factory's correctness posture should reference this artifact as the baseline. If a regression happens on Gemini, the validator should still show this exact pattern: `verdict: pass`, `observed: block`. Anything else is a regression worth investigating.

## Section 5 — Sprint 3 Memory Bridge Recon (appended 2026-04-27)

Sprint 3 verified that host memory surfaces are not equivalent and should not be documented as if they are.

### 5.1 — Claude Has True Machine-Local Auto Memory; Gemini And Codex Need Conservative Sidecars

**Claude.** The current Claude Code memory docs describe two complementary systems: human-authored `CLAUDE.md` files and Claude-authored auto memory. Auto memory is machine-local, stored under `~/.claude/projects/<project>/memory/`, with `MEMORY.md` as the session-start index and optional topic files beside it. The first 200 lines or 25KB of `MEMORY.md` load at conversation start. Source: `https://code.claude.com/docs/en/memory` (queried 2026-04-27).

**Gemini.** The current Gemini CLI docs split memory into two behaviors. The `save_memory` tool appends facts to the `## Gemini Added Memories` section of global `~/.gemini/GEMINI.md`. Experimental Auto Memory mines prior local transcripts and drafts reusable `SKILL.md` files into a review inbox; it does not automatically load a project fact-memory file. Sources: `https://geminicli.com/docs/tools/memory/` and `https://geminicli.com/docs/cli/auto-memory/` (queried 2026-04-27).

**Codex.** Official OpenAI developer-doc search did not surface a stable project fact-memory file equivalent to Claude's auto-memory path. Codex's reliable checked-in project context remains `AGENTS.md`, while generated memory state must not become an authoring target. Source search: `developers.openai.com` Codex docs queries for project memory and `~/.codex/memories/` (queried 2026-04-27).

**Decision.** Sprint 3's bridge writes to Claude's true auto-memory target and uses explicit project sidecars for Codex and Gemini: `<project>/.codex/memory/AGENTS_MEMORY.md` and `<project>/.gemini/memory/MEMORY.md`. The docs must call these sidecars what they are. `bridge_pass` proves the sidecars and Claude target exist and have outbound/inbound hash evidence; it does not claim native auto-loading for Codex or Gemini.

## Section 6 — Sprint 4 MCP Namespace Recon (appended 2026-04-27)

Sprint 4 verified that canonical MCP prefixing must respect each host's native namespace model rather than inventing a host-agnostic rendered tool name that none of the CLIs document equally.

### 6.1 — Server Alias Is The Cross-Host Control Point

**MCP protocol.** The current architecture docs still describe MCP as a client-server protocol with stdio and streamable HTTP transports. The function-name collision discussion remains client-side guidance rather than a protocol-native namespace field: clients should use the server name to namespace tools.

**Claude.** Claude Code project MCP config lives in `.mcp.json`. Project-scoped servers prompt for approval before use. MCP prompts and hook matchers use the `mcp__<server>__<tool>` convention, so a server alias is the prefix authority.

**Codex.** Codex CLI 0.124.0 stores MCP config in `config.toml`; project-scoped `.codex/config.toml` is trusted-workspace scoped. Streamable HTTP bearer auth uses `bearer_token_env_var`, not the backlog's proposed `bearer_token_env`.

**Gemini.** Gemini CLI 0.39.1 unconditionally assigns fully qualified MCP tool names in the `mcp_<serverName>_<toolName>` form. Gemini also warns not to use underscores in server names because the policy parser splits on the first underscore after `mcp_`.

**Decision.** Sprint 4 will keep `global-mcp.json` as the semantic source of truth with a `prefix` such as `forge.factory`, but render the host config server alias as `forge-factory`. The validator checks each host's native expected namespace form instead of pretending every host can display the literal `forge.factory.read_handoff` string.







