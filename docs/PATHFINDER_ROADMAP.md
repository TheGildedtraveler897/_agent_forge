# Omni-Factory Pathfinder Roadmap

**Last regenerated:** 2026-04-25 (Token-Burn Recon sprint).
**Source of truth for this rewrite:** `docs/PATHFINDER_LEDGER.md` — append-only recon ledger; do not delete.

This roadmap supersedes all prior versions. The shipped-status footnotes for the previous Architectural Upgrades #1, #2 and Capability Backlog #1, #3 are preserved at the bottom; everything above is forward-looking.

---

## The 2026 SOTA Horizon — what the industry is doing

Synthesized from official Claude Code 2026-04 docs, Codex CLI changelog v0.122–v0.125, Gemini CLI v0.39, NVIDIA Nemotron's bash-computer-use blog, and a sweep of multi-agent / LLM-agnostic / MCP-routing frameworks (overstory, MetaSwarm, AgenticOS, Junie, OpenCode, Kimi K2.6, ClawTeam, Spring AI, Google ADK).

### The five axes the SOTA has converged on

1. **Hooks are a 26-event lifecycle, not a single pre/post pair.** Claude Code now exposes `SessionStart`/`SessionEnd`/`InstructionsLoaded`/`UserPromptSubmit`/`UserPromptExpansion`/`PreToolUse`/`PermissionRequest`/`PermissionDenied`/`PostToolUse`/`PostToolUseFailure`/`PostToolBatch`/`SubagentStart`/`SubagentStop`/`TaskCreated`/`TaskCompleted`/`TeammateIdle`/`ConfigChange`/`CwdChanged`/`FileChanged`/`PreCompact`/`PostCompact`/`Elicitation`/`ElicitationResult`/`Notification`/`Stop`/`StopFailure`/`WorktreeCreate`/`WorktreeRemove`. Hook handlers are no longer just shell — five types: `command`, `http`, `mcp_tool`, `prompt` (yes/no via Claude), `agent` (spawn subagent to verify). `async: true` and `asyncRewake: true` flags decouple the hook from the agent's main loop. Permission updates can be applied from a hook at runtime and persisted to session/local/project/user settings.

2. **Memory is two layers, native + cross-host.** Claude Code's native auto-memory writes to `~/.claude/projects/<project>/memory/MEMORY.md` (machine-local, derived from git repo root, 200-line / 25KB index + topic files loaded on demand). Gemini ships experimental Auto Memory. Codex offloads to AGENTS.md auto-discovery + `codex resume` + multi-environment app-server sessions. **The cross-host shared brain is built on top of the native layers, not in place of them.** Our `<project>/MEMORY.md` is the cross-host layer; it must bridge to each host's native auto-memory, not replace it.

3. **MCP namespace prefixing is canonical.** Gemini auto-prefixes `mcp_<server>_<tool>`. Claude pattern-matches `mcp__<server>__<tool>`. The MCP spec itself does not enforce namespaces; community best practice is `<service>.<verb>` (e.g., `github.list_repos`, `slack.send_message`). Streamable HTTP transport with bearer-token auth + per-client audit log is now standard. Codex restricts project-scoped MCP servers to **trusted workspaces only**.

4. **Multi-agent orchestration has settled into the Conductor / Swarm hybrid.** A central conductor decomposes + routes; specialized swarm workers execute in parallel; results merge back through a coordinator. **Agent-as-a-Tool** (Claude's `TeammateTool`, Codex's `[agents]` config table) is the canonical primitive. Production-grade frameworks (Copilot Swarm, AgenticOS) enforce **proof-of-work + cost tracking + explainable routing + audit-grade logging** at the orchestrator level. Persistent state (overstory's git-worktree + tmux + SQLite mail) is how serious swarms keep work durable.

5. **Interactive bash control beats one-shot tool use.** NVIDIA Nemotron's pattern (and every non-trivial autonomous-coding agent in 2026) maintains **persistent shell state across turns**: cwd tracking via `{cmd};echo __END__;pwd` delimiter, allowlist runtime validation, human-in-the-loop confirm before each command. This is the substrate for autonomous loops (`auto-loop`), TDD micro-runs, and any "the agent runs three commands that depend on the previous cwd" workflow.

### How we leapfrog

The Triad coding CLIs (Claude/Codex/Gemini) and frameworks (overstory/MetaSwarm/AgenticOS) are each strong on a subset of these axes. **None ships all five.** Our differentiator is, and remains, the **canonical-first omni-factory** model: one schema authored in `_agent_forge`, three host-native renderings, runtime-validated with hook+memory+invocation gates. Where the SOTA today is "Claude does it well, Codex does part of it, Gemini does some of it", we ship "all three identically, audited, and provably reachable from each host's CLI".

The leapfrog opportunities, in priority order:

- **L1.** Render every canonical hook into all 26 native event names per host (we currently render 6). Every host gains the full lifecycle without rewriting hooks.
- **L2.** Bridge our cross-host `<project>/MEMORY.md` to each host's native auto-memory so "Claude saves a build command" / "Gemini auto-memory captures a quirk" both round-trip into the canonical file. **No competing framework does this.**
- **L3.** Render canonical `policies/mcp.json` server records as namespaced tools (`forge.<service>.<tool>`) into all three host configs. We become the **only** factory that ships *deterministic* cross-host MCP namespacing.
- **L4.** Canonical `policies/orchestration.json` schema + `crew-director` skill that emits **audit-grade orchestration logs** (per-agent token spend, proof-of-work, routing rationale) renderable into Claude Routines, Codex realtime handoffs, Gemini subagent dispatch, and arbitrary frameworks via A2A. We ship governance the way no current framework does.
- **L5.** A **`forge-shell`** primitive — Nemotron-style persistent bash session with cwd tracking, allowlist gating, telemetry-guardian as the deny half — exposed via skill so `auto-loop` / `crew-director` / any future autonomy can rely on it instead of host CLI heroics.

---

## Architectural Upgrades — deep technical specs

### A1. Hook Lifecycle V2 — full 26-event coverage with handler diversity

**Why.** `policies/hooks.json` v2 currently maps six canonical events (`pre_tool_use`, `post_tool_use`, `pre_commit`, `post_edit`, `session_start`, `stop`) into Claude/Codex/Gemini. Claude alone exposes 26 events. Codex adds MCP-tool observation + `apply_patch` + long-running Bash hooks (stable v0.124.0). Gemini adds `BeforeAgent`/`AfterAgent`/`BeforeModel`/`AfterModel`/`BeforeToolSelection`/`PreCompress`. We are leaving 80% of the lifecycle on the floor.

**Critical correctness fix (BLOCKER).** Gemini's event names are **not** `preToolUse` / `postToolUse`. They are `BeforeTool` / `AfterTool` / `BeforeAgent` / `AfterAgent` / `BeforeModel` / `AfterModel` / `BeforeToolSelection` / `SessionStart` / `SessionEnd` / `Notification` / `PreCompress`. Our current `_EVENT_ALIASES["gemini"]` map is wrong. The triad validator's `hook_surface_for(gemini)` passes today only because it does a substring match against the command path string, not because the event is actually registered. Hotfix immediately.

**Schema bump.** `policies/hooks.json` → v3.
- Add canonical event ids covering: `pre_tool_use`, `post_tool_use`, `post_tool_use_failure`, `post_tool_batch`, `permission_request`, `permission_denied`, `pre_compact`, `post_compact`, `session_start`, `session_end`, `stop`, `stop_failure`, `instructions_loaded`, `user_prompt_submit`, `user_prompt_expansion`, `subagent_start`, `subagent_stop`, `task_created`, `task_completed`, `teammate_idle`, `config_change`, `cwd_changed`, `file_changed`, `elicitation`, `elicitation_result`, `notification`, `worktree_create`, `worktree_remove`, `before_agent`, `after_agent`, `before_model`, `before_tool_selection`, `after_model`, `pre_compress`.
- Hook record gains `handler.type` ∈ `{command, http, mcp_tool, prompt, agent}` plus type-specific fields (Claude-shaped). Renderers translate to the host's nearest equivalent or skip with a `[WARN]` if no equivalent exists.
- Hook record gains `async: bool` and `async_rewake: bool` flags (Claude-only today; renderers ignore on Codex/Gemini until parity).
- Hook record gains `permission_updates[]` (add/replace/remove rules, set mode, add/remove dirs, destination = session/local/project/user).

**Renderer changes (`scripts/omni_factory.py`).**
- New `_EVENT_ALIASES` table covering all 34 canonical events × 3 hosts. Each cell is the host-native event name OR `null` (skip) OR `"<merge_into>"` (merge into another event the host does support).
- New `_handler_alias()` translating `command|http|mcp_tool|prompt|agent` → host-supported handler. Codex `command` only → render `prompt`/`agent` as `command` calling a wrapper script.
- `verify()` extension: every record's resolved handler exists on disk OR is reachable as a URL.

**Validator changes.** `validate-triad-runtime.py` gains a **live invocation probe** (closes vulnerability C2): write a sentinel hook that increments a counter file, fire a real tool call on each host, confirm the counter advanced. This is the only way to catch the C1-class silent-event-name failure.

**Effort.** ~2 sprints. Day 1: hotfix Gemini aliases, add live-invocation probe. Sprint 1: schema v3 + renderer rewrite. Sprint 2: handler diversity + async + permission_updates.

### A2. Cross-Host Auto-Memory Bridge

**Why.** We shipped the canonical `<project>/MEMORY.md` (Architectural #1, 2026-04-25). What we did **not** ship is a bridge to each host's native auto-memory:
- Claude's `~/.claude/projects/<project>/memory/MEMORY.md` (machine-local, derived from git root).
- Gemini's experimental Auto Memory store.
- Codex's `codex resume` thread state + AGENTS.md auto-discovery.

Today, a fact Claude saves via auto-memory does not reach Gemini, Codex, or our canonical file. This is **the single biggest gap between the roadmap promise and the actual delivery**.

**Architecture.**
- New skill: `memory-bridge` (Capability B2 below). Runs as a `Stop` hook on each host. Reads the host's native auto-memory delta since last bridge run. Normalizes into our canonical sections (`build_commands` / `project_quirks` / `active_tasks` / `recent_decisions` / `known_failures`). Calls `memory-archivist append` to land it in canonical `<project>/MEMORY.md`. Records bridge state in `<project>/.forge_state/bridge.json` (last-run timestamp per host).
- The reverse direction: a `SessionStart` hook on each host reads canonical `<project>/MEMORY.md` and **injects relevant entries into the host's native auto-memory store** (so the host treats them as first-class, not just imports).
- Conflict resolution: append-first; canonical wins on rewriteable sections (`active_tasks`); host-native-only entries are tagged `source:claude-auto` etc. when bridged in.
- Secrets-deny re-applied at the bridge layer (defense in depth on top of `memory-archivist` checks).

**Schema additions.**
- `policies/memory.json` gains `bridge: { enabled: bool, hosts: ["claude","codex","gemini"], cadence: "stop|session-end|manual" }`.
- `<project>/.forge_state/bridge.json` for state.

**Effort.** ~1 sprint, but only after A1 ships (needs `Stop` and `SessionStart` hooks rendered correctly across all three hosts).

### A3. MCP Namespace Prefixing & Routing — canonical-first

**Why.** Gemini auto-prefixes `mcp_<server>_<tool>` on tool discovery. Claude pattern-matches `mcp__<server>__<tool>`. Codex doesn't prefix. Our `global-mcp.json` is empty so the bug is latent. The moment two MCP servers expose `read_file`, names collide silently on Codex.

**Schema bump.** `global-mcp.json` v2.
- Top-level `version: 2`.
- Each server gets `id`, `prefix` (canonical, e.g., `forge.github`), `transport` (`stdio` / `streamable_http` / `sse`), `auth` (`none` / `bearer` / `oauth`), `targets` (host list), `tool_filter` (allow-list of tool names from that server, optional), `trust` (`local` / `remote-trusted` / `remote-sandboxed`).
- Renderer transforms server tool names to `${prefix}.${tool}` form before emitting into host configs.
- Claude `.mcp.json` gets the prefixed names. Codex `config.toml` `[mcp_servers.<id>]` blocks include `prefix`. Gemini `.gemini/settings.json` mcpServers block honors the canonical prefix (overrides Gemini's auto-prefix).

**Trust gating.** Project-scoped `.codex/config.toml` MCP servers only emit when `projects.json` declares the project as a trusted workspace. Otherwise the server lands in user-home only.

**Verifier.** `verify-agent-forge.py` checks every server has a `prefix` and that no two prefixes collide.

**Validator.** `validate-triad-runtime.py` gains an MCP-surface probe: queries each host's CLI to enumerate visible MCP tools, confirms canonical prefix is present.

**Effort.** ~1.5 sprints. Bulk of effort is the verifier + validator extensions; rendering is mechanical.

### A4. Audit-Grade Orchestration Log

**Why.** AgenticOS, Copilot Swarm Orchestrator, and Kimi K2.6 all converge on per-session orchestration logs that record (a) which agent was dispatched, (b) why (routing rationale), (c) tokens spent, (d) artifacts produced, (e) verification result. Without this, swarms burn money uncontrollably and operators can't answer "why did the system pick X". We have nothing here.

**Schema.** New `policies/orchestration.json` v1.
- `log_destination`: `<project>/.forge_state/orchestration.log` (JSONL append-only).
- `log_record_shape`: `{ts, session_id, parent_agent, child_agent, routing_reason, model_tier_requested, model_tier_actual, input_tokens, output_tokens, cost_usd, artifacts: [paths], verification: {status, gate, evidence}}`.
- `cost_budget`: `{per_session_usd, per_subagent_usd, soft_cap_action: "warn|prompt|halt"}`.
- `routing_decisions`: explicit lookup table (e.g., legal questions → `legal-counsel`; infra questions → `infra-architect`).

**Integration points.**
- `subagent-dispatcher` skill: now emits a JSONL record before dispatch and after each subagent finishes.
- `verification-gate`: emits the verification status into the same log.
- `branch-finisher`: records the final commit SHA + cost roll-up.
- New skill: `cost-warden` (Capability B3) reads the log and enforces budgets; halts if a soft cap is hit.

**Renderer.** Hook into `SubagentStart` / `SubagentStop` / `TaskCreated` / `TaskCompleted` lifecycle events from A1 to populate the log automatically.

**Effort.** ~2 sprints. Sprint 1: schema + log writer. Sprint 2: cost-warden + integration with subagent-dispatcher / verification-gate / branch-finisher.

### A5. The `forge-shell` Persistent-Bash Primitive

**Why.** SOTA autonomy frameworks (Nemotron, autoresearch derivatives, ClawTeam) all rely on a persistent bash session with cwd tracking, allowlist runtime validation, and HITL approval. Our skills assume the host CLI does this. They don't — every Bash tool call is independent. This blocks `auto-loop` (Karpathy-style propose→edit→test→evaluate→ratchet) and any multi-step workflow that depends on prior cwd.

**Architecture.**
- Skill: `forge-shell` (Capability B4 below).
- Implements Nemotron pattern in Python: a long-lived subprocess wrapping `/bin/bash` with `executable="/bin/bash"`. Each command wrapped as `{cmd};echo __END__;pwd`. cwd parsed from trailing `pwd`. State persisted in `<project>/.forge_state/shell-<session>.json`.
- Allowlist sourced from `policies/shell.json` (per-skill / per-team configurable).
- HITL approval gated by env var `AGENT_FORGE_SHELL_AUTO=off` (default on; unattended autonomous runs explicitly opt out).
- Telemetry-guardian still runs as the deny half (defense in depth).
- Output capped at 10,000 chars per command (Claude Code parity).

**Surfaces.**
- Subcommands: `forge-shell run --session <id> --cmd "..."` / `forge-shell state --session <id>` / `forge-shell reset --session <id>` / `forge-shell allowlist add|remove`.
- Audit log: `<project>/.forge_state/shell-<session>.log`.

**Why this enables future capabilities.** Once `forge-shell` exists, `auto-loop` is mostly orchestration (propose → call forge-shell → run pytest → evaluate → ratchet). Without `forge-shell`, every loop iteration starts fresh — no cwd, no env vars, no `git status` before commit, no useful TDD cycle.

**Effort.** ~2 sprints. Sprint 1: subprocess wrapper + cwd tracking + allowlist. Sprint 2: HITL flow + audit log + integration with `tdd-engineer` and `auto-loop`.

### A6. Continuous Evolution / Anti-Rot — make the factory govern itself

**Why.** The factory is the most-famous-for-governance repo on disk and yet **no agent watches the factory itself**. `verify-agent-forge.py` and `validate-triad-runtime.py` are human-invoked. SOTA frameworks (AgenticOS routing layer, MetaSwarm self-improving loop) have a self-audit substrate.

**Architecture.**
- Skill: `routine-auditor` (Capability B5 below) — already in backlog, now first-class.
- Three triggers:
  1. **Local schedule.** Cron-like via `/loop` or Routines (Claude). Runs `verify-agent-forge.py` + `validate-triad-runtime.py --project <each>`. If anything regresses, opens a local task in `MEMORY.md` `active_tasks` section (auto-cleanup when fixed).
  2. **Remote watchdog.** The watchdog spec already in `TECH_DEBT.md`. Fires after the repo lands on GitHub. Posts an issue when stale or drift detected.
  3. **Sprint-harvest cycle.** Every successful triad-green sprint, `routine-auditor` reviews the SOTA recon ledger and **flags doctrine that contradicts current SOTA**. Opens a `LESSONS_LEARNED.md` candidate for promotion or supersession.
- Append-only orchestration log (A4) records the auditor's runs.

**Schema.** New `policies/auditor.json` v1.
- Cadence config (cron expression, max gap, manual trigger).
- Re-recon source list (URLs to refetch + stale-after duration).
- Flag thresholds (skill count drift, hook surface drift, MCP server drift, lesson-ledger entry age).

**Integration with promotion gates.** Promotion of a lesson into doctrine (e.g., CONOPS §Hook Governance) **requires** a `routine-auditor` clean run within the prior 24 hours. This closes vulnerability D1 (don't promote stale doctrine).

**Effort.** ~1.5 sprints, but depends on A1 (hooks) + A4 (orchestration log) being solid.

### A7. Cross-Framework Interop — A2A protocol minimal compliance

**Why.** Google ADK ships native A2A (Agent-to-Agent) protocol. LangGraph/CrewAI/AutoGen agents can talk to each other via A2A. As the ecosystem grows, this is the universal handshake. We are absent.

**Architecture.**
- Minimal A2A endpoint exposed by the factory: a tiny HTTP server (`scripts/a2a-server.py` — out of scope for this roadmap doc which forbids code) that speaks the A2A handshake.
- New canonical record type: `policies/a2a.json` — agents we expose (skill names + descriptions in A2A schema), agents we trust to call into us, audit log destination.
- Skills marked `a2a_exposed: true` in frontmatter become callable via the A2A endpoint.
- Calls are logged to the orchestration log (A4) with `parent_agent: external:a2a:<peer>`.

**Effort.** ~1 sprint, deferred until A4 (orchestration log) ships so calls land in the right ledger.

---

## Capability Backlog — prioritized hit list

Numbering uses **B-prefix** to distinguish from previous-roadmap numbering. Each capability cross-references the architectural upgrade it depends on.

### B1. `live-hook-prober` (validation skill)

**Spec.** A skill invoked by `validate-triad-runtime.py` that fires a real, observable side-effect tool call on each host (e.g., a Bash command that writes to a sentinel file) and confirms the relevant hook intercepted/modified/blocked it. Closes critical vulnerability C2. Catches C1-class silent-event-name failures.

**Surface.** `live-hook-prober run --host claude --hook pre_tool_use --expect block` returns pass/fail/evidence-path.

**Depends on:** A1 (hook lifecycle V2). **Effort:** small. **Priority: highest** (immediate ship-blocker fixer).

### B2. `memory-bridge`

**Spec.** Bidirectional bridge between canonical `<project>/MEMORY.md` and each host's native auto-memory. Outbound (canonical → native) injects on `SessionStart`. Inbound (native → canonical) harvests on `Stop` / `SessionEnd`. Round-trips are idempotent and append-first.

**Surface.** Runs as a hook handler, not a slash command. Operator-visible via `<project>/.forge_state/bridge.json` and `bridge.log`.

**Depends on:** A1 (Stop / SessionStart hooks correctly rendered) + A2 (bridge schema). **Effort:** medium. **Priority: high** — closes the biggest delivery gap of the universal state layer.

### B3. `cost-warden`

**Spec.** Reads the orchestration log (A4) and enforces token + cost budgets at session, subagent, and per-skill granularity. Three actions on cap hit: `warn` (log only), `prompt` (HITL approve before continuing), `halt` (refuse to dispatch the next subagent). Reports cost roll-ups in human-readable form at end of session.

**Surface.** Slash command `/cost` (or hostlikely-equivalent) reads the log; runs as a `SubagentStart` hook intercepting dispatch.

**Depends on:** A4 (orchestration log). **Effort:** medium. **Priority: high** — first-line defense before `auto-loop` and `crew-director` ship.

### B4. `forge-shell`

**Spec.** Nemotron-pattern persistent bash primitive. See A5 for full architecture. Used by `auto-loop`, `crew-director`, and any skill that needs multi-turn shell state.

**Surface.** Subcommands `run` / `state` / `reset` / `allowlist`.

**Depends on:** A2 (we want shell sessions tagged in MEMORY.md `active_tasks`) + telemetry-guardian (deny-list defense). **Effort:** large. **Priority: high** — gates Karpathy-style autonomy.

### B5. `routine-auditor`

**Spec.** Already in old backlog. Now elevated to first-class governance capability. See A6. Three triggers (local schedule, remote watchdog, sprint-harvest re-recon). Opens local tasks for regressions, GitHub issues for remote drift, lesson-ledger candidates for SOTA-divergence findings.

**Surface.** Skill invokable manually; also runs as a Routine (Claude) / scheduled task (Codex) / cron (host-agnostic). Closes vulnerability D1 + D4.

**Depends on:** A4 (orchestration log) + A6 (auditor schema). **Effort:** medium. **Priority: high** — the factory must govern itself.

### B6. `router-overseer`

**Spec.** Agent-as-a-Tool dispatcher (already in old backlog). Reads `policies/orchestration.json` `routing_decisions`, picks the right specialist (or set of specialists in parallel), records routing rationale into the orchestration log, merges results, surfaces a single coherent answer.

**Surface.** `/route "<prompt>"` slash command in all three hosts.

**Depends on:** A4 (orchestration log for explainable routing) + B3 (cost-warden as the budget gate). **Effort:** medium. **Priority: high** — this is the operator's "ask the factory anything" entry point.

### B7. `auto-loop`

**Spec.** Karpathy autoresearch-style loop: propose → edit → run test → evaluate → ratchet. Interactive wizard at startup so non-experts can define `program.md` goals + identify failing tests + set hard success metrics before the expensive iteration starts.

**Surface.** `/auto-loop init` (wizard) → `/auto-loop run --max-iterations N --cost-cap $X` (loop).

**Depends on:** A5 (`forge-shell`) + A4 (orchestration log) + B3 (cost-warden). **Effort:** large. **Priority: medium-high** — the factory's "do TDD autonomously" headliner.

### B8. `wiki-compiler`

**Spec.** Compile raw inputs (PDF API specs, large codebase, doc dumps) into structured, densely-hyperlinked Markdown all agents can read directly. End reliance on brittle RAG.

**Surface.** `/wiki-compile --source <path>` produces `<project>/.forge_state/wiki/`. Index file references Markdown topic pages with `@imports`. Re-compilable on source change.

**Depends on:** A5 (`forge-shell` for parsing pipelines) + A2 (memory bridge so wiki entries surface as project quirks). **Effort:** large. **Priority: medium** — gates good performance on large repos.

### B9. `crew-director`

**Spec.** Capstone swarm orchestrator. Conductor pattern + swarm fan-out for declared multi-stage operations ("Release a new software version" → spawns `auto-loop` for tests, `wiki-compiler` for changelog, `brand-guardian` for release graphics, merges results).

**Surface.** Slash command `/crew-direct "<high-level-goal>"`. Operator approves the plan; conductor dispatches; swarm executes; cost-warden enforces; orchestration log records every decision.

**Depends on:** all of A1–A6 + B3 + B5 + B6 + B7. **Effort:** very large. **Priority: medium-low** — endgame; do not start until the dependencies are solid.

### B10. `path-scoped-rules`

**Spec.** Bring Claude Code's `.claude/rules/*.md` with YAML `paths:` glob to all three hosts. Renderer scopes a skill to specific file globs so its body only loads when relevant. Dramatically cuts context cost.

**Surface.** New skill frontmatter field `paths: ["src/api/**/*.ts"]`. Renderer drops the skill from default-load and converts it to a path-scoped rule on Claude / equivalent on Codex AGENTS.md / Gemini context-rule.

**Depends on:** none structural; adds a frontmatter field + renderer logic. **Effort:** small. **Priority: medium** — operator quality-of-life.

### B11. `host-quirk-translator`

**Spec.** A skill that detects host-specific surface mismatches (e.g., Gemini event-name drift, Codex sandbox-marker drift) and proposes a hotfix to `_EVENT_ALIASES` / `host_sandbox_blocked()`. Effectively the meta-skill that catches its own architectural-drift class of bug.

**Surface.** Runs after the `routine-auditor` weekly. Generates a PR-equivalent diff against `scripts/omni_factory.py`.

**Depends on:** A6 (auditor schedule) + A4 (logs to consult). **Effort:** medium. **Priority: medium**.

### B12. `a2a-bridge`

**Spec.** Minimal-compliance A2A protocol exposure (see A7). Lets external frameworks (ADK / LangGraph / CrewAI agents) call our skills. Conversely lets our skills call out to external A2A endpoints (e.g., a domain-specialist agent hosted elsewhere).

**Surface.** Skills with `a2a_exposed: true` are auto-published. `/a2a list` shows active peers; `/a2a call <peer>.<skill>` dispatches.

**Depends on:** A7. **Effort:** medium. **Priority: low** — defensive + future-proofing.

---

## Sprint sequencing recommendation

The technical dependencies push a clean order:

1. **Sprint 1 (immediate).** Hotfix C1 (Gemini aliases) + ship B1 (live-hook-prober). Protects the existing factory from silent correctness regressions.
2. **Sprint 2.** Architectural Upgrade A1 (Hook Lifecycle V2). Opens up the lifecycle for everything downstream.
3. **Sprint 3.** Architectural Upgrade A2 (Memory Bridge) + Capability B2 (`memory-bridge`). Closes the biggest delivery gap of the existing state layer.
4. **Sprint 4.** Architectural Upgrade A3 (MCP Namespace Prefixing) — pre-emptive, before any real shared MCP server lands.
5. **Sprint 5.** Architectural Upgrade A4 (Orchestration Log) + Capability B3 (`cost-warden`). Foundation for safe autonomy.
6. **Sprint 6.** Architectural Upgrade A5 (`forge-shell`) + Capability B4 (it is A5). Unlocks autonomy.
7. **Sprint 7.** Architectural Upgrade A6 (Anti-Rot) + Capability B5 (`routine-auditor`). Self-governance.
8. **Sprint 8.** Capability B6 (`router-overseer`). Operator-visible "ask the factory anything".
9. **Sprint 9.** Capability B10 (`path-scoped-rules`) + B11 (`host-quirk-translator`). Operator-quality-of-life pass.
10. **Sprint 10+.** Capabilities B7 (`auto-loop`), B8 (`wiki-compiler`), B9 (`crew-director`), B12 (`a2a-bridge`). Endgame.

Five paired-sprint cycles to ship the hot path; everything else is pluggable on top. Each sprint follows the established rhythm (canonical schema → three host renderers → skill that exercises it → triad runtime gate → lesson ledger). The pattern that worked twice (hook lifecycle, memory layer) is now load-bearing doctrine.

---

## Previously shipped — preserved status footnotes

**Architectural Upgrade #1 — Cross-Agent Memory Exchange.** ✅ Shipped 2026-04-25. `policies/memory.json` v1; `MEMORY.md` + `.forge_state/` rendered into all six governed projects; Gemini `@MEMORY.md` import; AGENTS.md Read Order entry #5 covers Claude/Codex; `memory_surface_for` triad gate. Evidence: `runtime/validation/triad/20260425-174222/`. **Known incomplete:** native auto-memory bridge (now A2 above).

**Architectural Upgrade #2 — Unified Hook Lifecycle.** ✅ Shipped 2026-04-24 — but **partially correct only**. Claude + Codex render correctly; Gemini event-name aliases are wrong (see C1 / A1). Evidence: `runtime/validation/triad/20260424-205818/`. **Known incomplete:** event-name correctness on Gemini, handler diversity, async, permission_updates.

**Capability #1 — `memory-archivist`.** ✅ Shipped 2026-04-25. `append`/`validate`/`summary` subcommands; secrets-deny patterns; audit log; wired into improvement-team. **Known incomplete:** does not yet bridge to host-native auto-memory (B2).

**Capability #3 — `telemetry-guardian`.** ✅ Shipped 2026-04-24. POSIX `guardian.sh`; deny-list; bypass via `AGENT_FORGE_GUARDIAN=off` logged to `~/.agent-forge/guardian.log`. **Known incomplete:** allow-list pair (Nemotron pattern); persistent-cwd; HITL confirm — these would land with `forge-shell` (B4 / A5).
