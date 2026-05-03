# Agent Forge Handoff

Last updated: 2026-05-03 (GSD Native Assimilation — Codex T-01..T-13, Claude T-14..T-15 pickup)

## What Changed

### Sprint: GSD Native Assimilation (2026-05-03, Codex T-01..T-13 + Claude Opus 4.7 T-14..T-15)

Cross-agent sprint. Codex executed Phases 1–4 of the GSD assimilation plan (`docs/plans/2026-04-30-gsd-native-assimilation.md`); Claude picked up Phase 5 (T-14 sync + T-15 runtime gate) after Codex hit a token budget at T-13.

#### Codex contribution (T-00..T-13, commits `861ad11`..`daf51e7`)

1. **Five new global skills shipped:**
   - `plan-quality-auditor` (T-01): pre-flight quality scoring for implementation/sprint/dispatch plans before execution.
   - `goal-verifier` (T-04): verifies feature/sprint/release completion against original user-visible goal, not summaries or test reports.
   - `quick-task-runner` (T-07): bounded-task lane that moves faster than full spec→plan workflow without bypassing branch discipline or verification.
   - `workstream-manager` (T-08): splits concurrent agent/human work into safe branches, worktrees, owners, file-ownership lanes, and resumable continuity cursors.
   - `codebase-cartographer` (T-11): structural mapping of repos before planning; brownfield codebase intelligence.
2. **Seven existing skills modified:**
   - `execution-planner` (T-02): GSD plan metadata fields added.
   - `spec-architect` (T-03): decision IDs for traceability.
   - `verification-gate` (T-05): wired to delegate to `goal-verifier` for goal-completion claims.
   - `goal-verifier` (T-06): UAT routing.
   - `subagent-dispatcher` (T-09): wave discipline with `depends_on` and `file_ownership` metadata.
   - `branch-finisher` (T-10): atomic task history preserved across branch close.
   - team manifests (T-12): `assessment-team`, `delivery-team`, `planning-team`, `research-team` all rewired to reference the new GSD skills.
3. **Lesson recorded** (T-13, commit `daf51e7`): GSD native assimilation lesson appended to `docs/LESSONS_LEARNED.md`.

#### Claude pickup (T-14..T-15, this commit)

1. **T-14 — Refresh registry + sync 6 governed projects.**
   - `python3 scripts/omni_factory.py render-registry > registry.json` (38,457 bytes).
   - 18 sync commands sequential across `jarvis`, `RoboNaaz`, `ZorroClaw`, `homelab`, `factory`, `playlist-archive` × Claude/Codex/Gemini.
   - All Claude + Codex syncs succeeded (12/12 rc=0). All Gemini per-project syncs returned rc=1 with the documented protective behavior `Refusing to overwrite unmanaged file: <project>/GEMINI.md` — the root `GEMINI.md` files are operator-curated. The `.gemini/skills/` content synced cleanly before the protective abort, so all 5 new GSD skills landed across all three host surfaces in all 6 projects.
   - `python3 scripts/verify-agent-forge.py` exit 0 post-sync.
2. **T-15 — Runtime gate + branch finish.**
   - `python3 scripts/validate-triad-runtime.py --project jarvis`: `overall_pass: true`. Per-host: Claude `cli` 38/38, Codex `filesystem-escalated` 38/38 (`sandbox_blocked: true`, per documented escalation doctrine), Gemini `filesystem` 37/37 (one fewer because `prompt-auto-activator` excludes Gemini). All hosts `hook+ mem+ bridge+ mcp+`. Artifact: `runtime/validation/triad/20260503-095907/`.
   - `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge tests.test_mcp_namespace tests.test_branch_discipline -v`: 20 OK.
   - `python3 scripts/verify-agent-forge.py` exit 0.
3. **Bugfix discovered during T-15:** `scripts/validate-triad-runtime.py` `run_cmd()` raised `TypeError: can't concat str to bytes` when the gemini probe hit `subprocess.TimeoutExpired` — `exc.stderr` was bytes, the timeout-suffix was str. Fixed by coercing both `exc.stdout` and `exc.stderr` to str via UTF-8 decode before concatenation. This is a pre-existing bug, not a GSD regression; it surfaced because the gemini probe legitimately timed out on this run.

#### Cross-agent handoff observations

The pickup tested whether Agent Forge's handoff infrastructure supports seamless cross-agent continuity. **What worked:** the durable plan file at `docs/plans/2026-04-30-gsd-native-assimilation.md` named exact T-14/T-15 commands; git log + commit messages mapped 1:1 to plan tasks; the recorded T-13 lesson served as a "Codex's contribution recorded" marker. **What was missing:** Codex did not write a "paused at T-13; T-14 next" cursor into `<project>/MEMORY.md active_tasks` — the canonical rewriteable cross-host pointer designed for exactly this purpose was unused. A fresh agent on a new session would have to derive the pickup point from git log + plan file rather than a single-line cursor. New active lesson recorded in `docs/LESSONS_LEARNED.md` documenting the gap and recommending a doctrine update.

Evidence:
- Codex commits: `861ad11`..`daf51e7` (13 commits, all on origin pre-pickup).
- Claude pickup commit: this one.
- Triad runtime artifact: `runtime/validation/triad/20260503-095907/summary.json`.
- Verifier exit 0; tests 20 OK.

### Sprint: RC Polish + Audit-Reconciliation (2026-04-29, Claude Opus 4.7)

A polish-and-audit sprint following the RC milestone. Closed three doc-drift items, recorded two new lessons, and exercised the bootstrap-project.sh `--existing` path that had been pending operator validation.

#### Changes Made

1. **Doc reconciliation (Track C, commit `9604e74`).** `docs/PATHFINDER_ROADMAP.md` Sprint 5 row updated from "A4 + B3 Orchestration Log + Cost Warden" to "SOTA-2026 Overhaul" (the actual shipped Sprint 5); cascading renumbering for Sprints 6–11+. `docs/SPRINT_BACKLOG.md` status table updated: Sprints 3, 4, 5 marked shipped. `docs/TECH_DEBT.md` adds Sprint 5 + lessons-ledger triage to "Recently Resolved" and removes the now-completed ledger-triage item from "Follow-On Work"; header refreshed to RC milestone.
2. **`feat/onboarding-guide` branch deleted.** Was 0 commits ahead, 2 behind master. Work fully integrated via commit `2a573a6` ("feat: onboarding-guide build-out"). Used `git branch -d` (safe variant) which confirmed integration before deleting.
3. **Track B3: `dev/active/` cleanup reference added to `branch-finisher`.** Step 5 — Cleanup now explicitly names `dev/active/<slug>/` deletion at task close, closing the lifecycle loop documented in `execution-planner` § Checkpoint Discipline.
4. **Track B1: defensive Codex sandbox marker added.** `host_sandbox_blocked()` in `validate-triad-runtime.py` gains `"Codex's Linux sandbox uses bubblewrap"` as a stable warning-header detector. The current marker list correctly caught Codex v0.125.0's bwrap blocker on the 2026-04-28 run; the new marker is preventive maintenance against future wording drift in the rest of the sentence.
5. **Track B2: bootstrap-project.sh `--existing` exercised against a fake project.** Test artifact `~/Projects/bootstrap-test-existing/` (cleaned up after) confirmed the script's `--existing` mode unconditionally overwrites `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`. Custom files (e.g. `src/main.py`) preserved correctly. This is a real footgun for any operator running `--existing` against a curated tree; recorded as 2026-04-29 lesson "bootstrap-project.sh --existing Unconditionally Overwrites Governance Docs".
6. **Two new lessons recorded.** 2026-04-29 entries added to `docs/LESSONS_LEARNED.md`: (a) the bootstrap finding above, with promotion targets in the script and the operator runbook; (b) the audit-reconciliation pattern that caught real sprint-numbering drift one day after the RC milestone. Header counts now 15 promoted, 3 active, 0 superseded.
7. **Track A (watchdog activation) deferred.** Operator-gated on GitHub repo creation. The watchdog routine spec at `docs/TECH_DEBT.md:44-126` is ready to schedule once the operator pushes `_agent_forge` to a GitHub remote.

Evidence:
- Commit `9604e74` "Reconcile sprint docs with shipped RC state" (Track C).
- Verifier: `python3 scripts/verify-agent-forge.py` exit 0.
- Tests: `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge tests.test_mcp_namespace -v` 17 OK.
- Triad runtime artifact: `runtime/validation/triad/20260429-223331/summary.json` (`overall pass=true`, Claude `cli` 33/33, Codex `filesystem-escalated` 33/33 with `sandbox_blocked: true`, Gemini `filesystem` 32/32).
- Bootstrap test artifact captured md5 deltas before cleanup.

### Sprint 5 / RC Milestone: SOTA-2026 Overhaul + Lessons-Ledger Triage (2026-04-28, Claude)

Sprint 5 ships the SOTA-2026 overhaul (checkpoint discipline, terse-mode capability, prompt-auto-activator hook), syncs all six governed projects, runs the full triad validator green, and triages the lessons ledger to clear the second-backlog problem before the next-evolution work.

This is the **Release Candidate** milestone: every shippable backlog item is done; only platform-blocked items remain (and they will not block forever via reachable engineering — they need real machines, kernel-level changes, or upstream CLI behavior changes). The factory is ready for the next-evolution sprint (extracting `obra/superpowers`, `gsd-build/get-shit-done`, and the Reddit GSD framework as native skills under canonical Omni-Factory governance — a separate clean pass).

#### Changes Made

1. **Two new global skills shipped.** `token-optimizer` (workflow, all three hosts) defines the terse-mode contract; `prompt-auto-activator` (workflow, Claude+Codex only) owns the user-prompt-submit advisory hook.
2. **Canonical event `user_prompt_submit` is now exercised by a real record.** `policies/hooks.json` `shared` array gained `prompt-auto-activator` with `command` handler at `skills/global/prompt-auto-activator/auto-activator.sh`. Gemini is excluded (alias `None`); the constraint is recorded in the lesson ledger so the next operator re-verifies against current Gemini CLI release notes before extending targets.
3. **Checkpoint discipline added to `context-engineer` and `execution-planner`.** Additive `## Checkpoint Discipline` sections; the durable plan stays at `docs/plans/<slug>.md`, the cross-host pointer remains `MEMORY.md active_tasks`, and a transient `dev/active/<slug>/` working tree (`.gitignore`d) holds the rolling cursor. Cadence binds to verification-gate passes, not a fixed task count.
4. **`tests/test_hooks_v3.py` covers the new render contract.** Two new methods: `test_user_prompt_submit_renders_for_claude_and_codex` and `test_user_prompt_submit_filtered_from_gemini`. Five tests OK.
5. **Sync to all six governed projects done.** Claude, Codex, and Gemini surfaces refreshed for `jarvis`, `RoboNaaz`, `ZorroClaw`, `homelab`, `factory`, `playlist-archive`. Spot-check on `jarvis` confirms Claude+Codex carry the new `UserPromptSubmit` key and `prompt-auto-activator` command path; Gemini correctly omits both.
6. **Triad runtime validator green.** `validate-triad-runtime.py --project jarvis` reports `overall=PASS` with Claude `cli` 33/33, Codex `filesystem-escalated` 33/33 (`sandbox_blocked: true` per the documented host blocker), Gemini `filesystem` 32/32 (one fewer because `prompt-auto-activator` excludes Gemini). All hosts `hook+ mem+ bridge+ mcp+`. Artifact: `runtime/validation/triad/20260428-190104/`.
7. **Lessons-ledger triage complete.** 16 entries reviewed; 9 promoted (lesson is now enforced in code or in `AGENTS.md`/`CONOPS.md` as a Rule), 7 remain active (operational context that still shapes future decisions, or doctrine-promotion still pending). The ledger is no longer drifting into a second backlog.
8. **Content-freshness audit clean.** All four expert skills (`infra-architect`, `corporate-controller`, `legal-counsel`, `brand-guardian`) already delegate to runtime web search; no embedded date-stamped facts. The single hit (`evidence-packager` example rows dated 2025) is illustrative template content, not load-bearing.
9. **`docs/specs/2026-04-27-sota-2026-overhaul.md` archives the relayed brief verbatim**, plus the four operator-confirmed architectural deviations from the literal request.
10. **`docs/plans/2026-04-27-sota-2026-overhaul.md` records the 11-task micro-plan** with verification commands.

Evidence:
- Verifier: `python3 scripts/verify-agent-forge.py` exit 0 (post registry refresh).
- Tests: `python3 -m unittest tests.test_hooks_v3 -v` 5 OK.
- Triad runtime artifact: `runtime/validation/triad/20260428-190104/summary.json` (`overall pass=true`, all hosts `hook+ mem+ bridge+ mcp+`; Codex remains `filesystem-escalated` with `sandbox_blocked: true`).
- Hook surface spot check on `jarvis`: Claude `prompt-auto-activator=True UserPromptSubmit_key=True`, Codex same, Gemini both `False`.
- Auto-activator smoke test: `printf '/caveman' | bash auto-activator.sh` returns one JSON advisory line, exit 0.

Operational note: `prompt-auto-activator` is the first cross-host record bound to canonical event `user_prompt_submit`. Live invocation through Claude headless remains constrained per the 2026-04-26 doctrine; live-probe verification is operator-driven from a real terminal, not from this Bash tool.

### Sprint 4: MCP Namespace Prefixing & Routing (2026-04-27, Codex)

Shipped A3: the omni-factory now has its first real shared MCP server, host-safe namespace rendering, trust-gated project routing, and a triad `mcp_pass` gate.

#### Changes Made

1. **`global-mcp.json` upgraded to v2** — seeded `forge-factory` as a local stdio shared server with semantic prefix `forge.factory`, host-safe alias `forge-factory`, and one filtered tool: `read_handoff`.
2. **`projects.json` gained `trusted_workspace`** — `jarvis` is the Sprint 4 proof target; remote or project-scoped MCP servers are now blocked from untrusted governed projects.
3. **Local proof server shipped** — `scripts/mcp/forge_factory_server.py` implements a minimal MCP stdio server with real content-length framing, `initialize`, `ping`, `tools/list`, and `tools/call`.
4. **MCP renderers hardened** — `scripts/omni_factory.py` now normalizes MCP v2 records, derives host-safe `server_alias`, filters by host targets, emits Codex `bearer_token_env_var` / `enabled_tools`, and writes Claude `.mcp.json`, Codex `.codex/config.toml`, and Gemini `.gemini/settings.json` consistently.
5. **Verifier extended** — `validate_mcp_inventory()` now rejects duplicate prefixes, invalid targets/scope/auth/trust/transport values, Gemini-unsafe underscores in server aliases, and trust-gate violations for project-scoped or remote servers.
6. **Triad validator extended** — `validate-triad-runtime.py` now runs `mcp_surface_for()` per host and records `mcp_pass`. Pass means the host-native config surface contains the expected alias and the seeded stdio server answers a direct MCP `tools/list` smoke request with `read_handoff`.
7. **Focused tests added** — `tests/test_mcp_namespace.py` covers v2 normalization, alias derivation, trust gating, duplicate-prefix rejection, the proof server handshake, and validator MCP surface proof.

Evidence:
- Tests: `python3 -m py_compile scripts/omni_factory.py scripts/validate-triad-runtime.py scripts/mcp/forge_factory_server.py` exit 0.
- Tests: `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge tests.test_mcp_namespace` exit 0.
- Structural verifier: `python3 scripts/verify-agent-forge.py` exit 0.
- Triad runtime artifact: `runtime/validation/triad/20260427-234006/summary.json` (`overall pass=true`, all hosts `hook+ mem+ bridge+ mcp+`; Codex remains `filesystem-escalated` with `sandbox_blocked:true`).

Operational note: host MCP management subcommands are not yet a clean cross-host proof surface for project-local servers. `claude mcp get forge-factory` sees the project config but still reports `Failed to connect`; `mcp_pass` therefore uses rendered-surface validation plus a direct stdio `tools/list` smoke instead of `mcp get/list` parity.

### Sprint 3: Cross-Host Auto-Memory Bridge (2026-04-27, Codex)

Shipped A2 + B2: canonical `MEMORY.md` now syncs to host-local memory surfaces through async session lifecycle hooks, with bridge state and triad runtime proof.

#### Changes Made

1. **`policies/memory.json` upgraded to v2** — additive `bridge` block enables Claude/Codex/Gemini, outbound `session_start`, inbound `stop`, `append-first` conflicts, and `deny` secrets inheritance.
2. **`memory-bridge` capability shipped** — `skills/global/memory-bridge/` includes `SKILL.md` plus `bridge.py outbound|inbound|status`. Outbound writes a managed block into the host target; inbound removes the managed block, imports new notes once, rejects credential-shaped content, and appends through `memory-archivist`.
3. **Host-specific hook records added** — `memory-bridge-outbound-claude|codex|gemini` and `memory-bridge-inbound-claude|codex|gemini`, using explicit `--host` arguments instead of relying on an undocumented `$HOST_TAG`.
4. **Bridge targets are explicit** — Claude writes true machine-local auto memory at `~/.claude/projects/<encoded-project-path>/memory/MEMORY.md`; Codex writes `<project>/.codex/memory/AGENTS_MEMORY.md`; Gemini writes `<project>/.gemini/memory/MEMORY.md`. Codex and Gemini are sidecars, not claims of native auto-memory loading.
5. **Bridge state created for every governed project** — `<project>/.forge_state/bridge.json` and `bridge.log` now exist alongside memory manifest state.
6. **Verifier and triad validator extended** — `verify-agent-forge.py` validates memory policy v2, Python hook command paths, bridge fields, and bridge state/log sidecars. `validate-triad-runtime.py` adds `memory_bridge_for()` and records `bridge_pass` per host.
7. **Archivist hardened** — `memory-archivist` now uses file locking and atomic writes so bridge inbound imports cannot corrupt canonical `MEMORY.md`.
8. **Focused tests added** — `tests/test_memory_bridge.py` covers outbound idempotence, inbound de-duplication, secrets rejection, archivist source tagging, and bridge state initialization.

Evidence:
- Tests: `python3 -m py_compile scripts/omni_factory.py scripts/validate-triad-runtime.py skills/global/memory-bridge/bridge.py skills/global/memory-archivist/archivist.py` exit 0.
- Tests: `python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge` exit 0.
- Structural verifier: `python3 scripts/verify-agent-forge.py` exit 0.
- Bridge outbound proof: Claude, Codex, and Gemini all wrote Jarvis native targets with hash `5413aa8cb72de0e691f4b7c77b8926879f589b2fa86e133c5af00e4232861eef`.
- Triad runtime artifact: `runtime/validation/triad/20260427-203021/summary.json` (`overall pass=true`, expected 31 skills, all hosts `hook+ mem+ bridge+`; Codex remains `filesystem-escalated` with `sandbox_blocked:true`).

Operational note: Gemini global context sync still refuses to overwrite unmanaged `~/.gemini/GEMINI.md`; project-local Gemini surfaces sync correctly. This is deliberate managed-file protection, not a Sprint 3 failure.

### Sprint 2: Hook Lifecycle V2 + Codex Event-Key Drift Fix (2026-04-27, Codex)

Shipped the v3 hook policy foundation and closed a second event-key drift class before it reached a live failure.

#### Changes Made

1. **Preflight checkpoint preserved** — existing untracked `onboarding-guide` + Codex cost tally helper work was committed separately as `e5a370c` before Sprint 2 edits. Preflight verifier green and triad baseline green at `runtime/validation/triad/20260427-045321/`.
2. **`policies/hooks.json` upgraded to schema v3** — active records now use explicit `handler` objects. The seeded `pre-tool-execution-guardian` remains the active cross-host command hook. Dormant Claude examples cover `http`, `mcp_tool`, `prompt`, and `agent` handler shapes without rendering unsafe inactive hooks.
3. **Codex hook aliases corrected** — `_EVENT_ALIASES["codex"]` now maps canonical `pre_tool_use` to native `PreToolUse` and related supported Codex events to PascalCase. Official Codex docs show PascalCase hook keys; prior snake_case output was a silent-correctness risk.
4. **Hook renderer normalized v2/v3 records** — `scripts/omni_factory.py` now normalizes legacy top-level `command` records into v3 command handlers, exposes `native_hook_event()`, converts `timeout_ms` to seconds for Claude/Codex and milliseconds for Gemini, and renders Gemini hooks in the current nested `hooks` array shape.
5. **Verifier tightened** — `verify()` checks hook version, known canonical event ids, target host names, handler types, required handler fields, command script paths, and async rules. Unsupported active event/handler/host pairs produce warnings instead of invalid rendered config.
6. **Triad validator tightened again** — `hook_surface_for()` now computes `expected_hook_records` from every active policy record and checks every expected native event key, not just one guardian event. Fresh artifact `runtime/validation/triad/20260427-085402/summary.json` shows all hosts `hook+ mem+`, with Codex expecting and observing `PreToolUse`.
7. **`live-hook-prober` updated** — accepts `--handler-type <command|http|mcp_tool|prompt|agent>` and records handler type in JSON evidence. Command mode remains the only cross-host live-dispatch proof; non-command modes are sentinel/escalated until safe local sentinels exist.
8. **Docs and lessons updated** — `docs/SPRINT2_DESIGN.md`, `docs/HOST_INTEGRATIONS.md`, `docs/TRIAD_RUNTIME_VALIDATION.md`, and `docs/LESSONS_LEARNED.md` now record v3 schema and the Codex event-key drift lesson.

Evidence:
- Preflight commit: `e5a370c` (`Add onboarding guide and Codex cost tally helpers`).
- Tests: `python3 -m unittest tests.test_hooks_v3` exit 0.
- Structural verifier: `python3 scripts/verify-agent-forge.py` exit 0.
- Triad runtime artifact: `runtime/validation/triad/20260427-085402/summary.json` (`overall pass=true`, expected 30 skills).

Stabilization note: Sprint 2 proves command hook reachability and every active rendered native event key. Non-command hook handler shapes are schema-validated and dormant by design; they are not live-dispatch proven until a host-safe sentinel exists. Generated delivery-target repos may show surface dirt after sync and should be treated as outputs of `_agent_forge`, not hand-edit sources.

### Sprint 1: Gemini Hook-Alias Hotfix + live-hook-prober (2026-04-25/26, Claude)

First sprint of the new Apex Roadmap. Closed the BLOCKER C1 bug + shipped the deeper validation gate that catches its entire class.

#### Changes Made

1. **C1 hotfix — Gemini event aliases corrected** in `scripts/omni_factory.py` `_EVENT_ALIASES["gemini"]`. Renamed `preToolUse → BeforeTool`, `postToolUse → AfterTool`, `sessionStart → SessionStart`, `stop → SessionEnd`. Gemini CLI v0.39 expects PascalCase event names; our prior camelCase aliases were never recognized by the dispatcher, so the seeded `telemetry-guardian` hook silently never fired on Gemini.
2. **`hook_surface_for()` tightened** in `scripts/validate-triad-runtime.py`. Now also checks that the per-host expected event key is present as a top-level key in the rendered hooks payload (`PreToolUse` / `pre_tool_use` / `BeforeTool`). Without this, any future event-name drift would slip through surface validation the same way C1 did. The check exposes `expected_event_key`, `observed_event_keys`, `event_key_present` alongside `guardian_present`.
3. **`live-hook-prober` skill shipped** at `skills/global/live-hook-prober/`. Fires a real `git commit --no-verify -m probe` on each host CLI and observes whether the seeded guardian hook actually intercepts it. Three escalation modes: `sandbox_blocked` (Codex bwrap), `trust_blocked` (Gemini workspace trust), `headless_permission_constraint` (Claude `-p` mode — see Limitations in the SKILL.md). Returns single-line JSON; non-zero exit on real fail.
4. **`--probe-invocations` flag added** to `validate-triad-runtime.py`. Default OFF (each probe is a real CLI call). When ON, runs `live_hook_invocation_for(host, project_root)` after surface checks pass; matrix entries gain `live_hook_pass` + `live_hook_verdict`.
5. **Live verification — Gemini live+ proves the C1 fix end-to-end.** `bash skills/global/live-hook-prober/prober.sh --host gemini --project ~/Projects/jarvis --command "git commit --no-verify -m probe" --expect block` returned `verdict: pass`, `observed: block`, exit 0. Hook actually fired. Codex live~ (sandbox-blocked, escalated per doctrine). Claude live~ (headless-permission-constraint, escalated and documented as inherent CLI limitation; real Claude live-probing requires `forge-shell` from B4 roadmap).
6. **Skill count rose 28 → 29.** Triad surface validator green: `runtime/validation/triad/20260426-035206/` shows all three hosts `hook+ mem+`.

Evidence:
- C7 commit `f2cea42`: `fix: Gemini hook event aliases (C1) + tightened hook_surface check`.
- Live Gemini probe artifact: `runtime/validation/hook-probe/20260426-035313/gemini/` (verdict=pass, exit=0).
- Triad surface artifact: `runtime/validation/triad/20260426-035206/summary.json`.

### Workflow Discipline Post-Mortem: Stalled Tool-Result Delivery (2026-04-25, Claude)

## What Changed

### Workflow Discipline Post-Mortem: Stalled Tool-Result Delivery (2026-04-25, Claude)

Two silent stalls during the universal state layer sprint were traced to harness-level tool-result delivery failures on compound bash commands, not actual hangs. Captured as `2026-04-25 - Compound Bash Calls Cause Silent Tool-Result Delivery Stalls` in `docs/LESSONS_LEARNED.md`. Two short rules added to `AGENTS.md`: prefer narrow tool calls, and treat `[Tool result missing due to internal error]` as a re-grounding signal rather than a retry signal. New `Operator Tips` section in `AGENTS.md` names the >5-minute silent-stall heuristic so operators know how to unblock cheaply.

**Follow-up finding (Sprint 1, 2026-04-25/26):** A second stall class was identified — long-running CLI tool calls (e.g., `claude -p` headless probes) hang on permission approval that has no interactive stdin to deliver. `timeout(1)` does not always reap the full subprocess tree (claude → node → MCP servers). The leftover child keeps file descriptors open and the bash-result delivery to the agent drops. Mitigation: do **not** invoke `live-hook-prober` transitively through a Claude Code session's Bash tool. Run it directly from a real terminal or as a scheduled Routine. Documented in `skills/global/live-hook-prober/SKILL.md` § Known limitations.

### Universal State Layer + Memory Archivist (2026-04-25, Claude)

Pathfinder Roadmap Architectural Upgrade #1 paired with Capability Backlog #1, shipped together and validated end-to-end through the triad runtime gate.

#### Changes Made

1. **`policies/memory.json` v1 authored** — five sections (`build_commands`, `project_quirks`, `active_tasks` [rewriteable], `recent_decisions`, `known_failures`), retention 50/warn-at-40, `secrets_policy: deny`.
2. **Three omni-factory renderers shipped** in `scripts/omni_factory.py`: `render_memory_md()`, `render_forge_state_readme()`, `render_forge_state_manifest()`, plus `sync_memory()` invoked from `sync_claude` / `sync_codex` / `sync_gemini`. `render_project_gemini_md` extended to `@import MEMORY.md`.
3. **18 host-native surfaces written** — six governed projects each gain `<project>/MEMORY.md` + `<project>/.forge_state/{README.md,manifest.json}`.
4. **`AGENTS.md` Read Order extended** with a fifth entry naming `<project>/MEMORY.md` as the universal cross-host session-state file. Single edit covers all three hosts via the AGENTS chain.
5. **`memory-archivist` capability shipped** at `skills/global/memory-archivist/` with `SKILL.md` (workflow class, all-host targets) and `archivist.py` providing `append`, `validate`, `summary` subcommands. Secrets-deny patterns reject API keys / private keys / credential-shaped strings. Audit log at `<project>/.forge_state/archivist.log`. Live unit-tested: append OK (exit 0), validate OK (exit 0), secrets-deny rejected `API_KEY=...` with exit 2.
6. **Verifier extended** — `verify()` parses `policies/memory.json`, confirms every governed project has `MEMORY.md` with all section anchors and a well-formed `.forge_state/manifest.json`.
7. **Triad validator extended** — `memory_surface_for(host, project_root)` parallels `hook_surface_for`. Overall pass now requires skill + hook + memory. `host_sandbox_blocked()` marker list expanded with Codex's newer error strings (`needs access to create user namespaces`, `shell tool is blocked by the sandbox`, etc.) so sandbox-blocked Codex still escalates to `filesystem-escalated` evidence.
8. **`teams/improvement-team.json` updated** — `memory-archivist` wired alongside `sprint-harvester` in all three host mappings; harvester captures durable doctrine candidates, archivist captures session-scoped state.
9. **Final E2E green** — `verify-agent-forge.py` EXIT=0 with new memory checks reporting OK; `validate-triad-runtime.py --project jarvis` EXIT=0 with `overall_pass: true`, all three hosts `pass: true` `hook_pass: true` `memory_pass: true`, expected count **28** (was 27). Codex auto-escalated to `filesystem-escalated` after sandbox-marker list was updated.

Evidence artifact: `runtime/validation/triad/20260425-174222/summary.json`.

### Unified Hook Lifecycle + Telemetry Guardian (2026-04-24, Claude)

Shipped Pathfinder Roadmap **Architectural Upgrade #2** and **Capability Backlog #3** as one paired sprint, wired through the triad runtime gate.

#### Changes Made

1. **`policies/hooks.json` upgraded to schema v2** — top-level `shared` array plus per-host arrays. Each record carries `id`, `event`, `matcher`, `command`, `targets`, `timeout_ms`, `status_message`, `description`. Seeded with the `pre-tool-execution-guardian` record targeting all three hosts.
2. **Three host renderers added** — `scripts/omni_factory.py` now carries `_hooks_for_host()`, `_EVENT_ALIASES`, plus `claude_hook_payload()` / `codex_hook_payload()` (updated) / `gemini_hook_payload()`. Event names translate via `_EVENT_ALIASES` (snake_case → Claude PascalCase / Codex snake_case / Gemini camelCase).
3. **Three host-native surfaces written per project** — `<project>/.claude/settings.json` (top-level `hooks` block), `<project>/.codex/hooks.json` (existing path), `<project>/.gemini/settings.json` (`hooks` block merged alongside `context` and `mcpServers`).
4. **`telemetry-guardian` capability shipped** — `skills/global/telemetry-guardian/SKILL.md` (expert class, all-host targets) plus POSIX `guardian.sh`. Deny list: `--no-verify`, `--no-gpg-sign`, force-push to protected branches, explicit `git reset --hard <ref>`, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777. Bypass via `AGENT_FORGE_GUARDIAN=off`, logged to `~/.agent-forge/guardian.log`. Unit-tested 7 invocations: 3 allows, 4 blocks, 1 bypass — all correct verdicts.
5. **Verifier extended** — `verify()` parses `hooks.json`, requires `id`/`event`/`command` per record, and confirms every referenced bash script path exists on disk.
6. **Triad validator extended** — `hook_surface_for(host, project_root)` runs after skill enumeration, attaches `hook_surface` to each per-host result, and gates overall pass on guardian presence in each rendered settings file. Matrix now includes `hook_pass` per host.
7. **Docs landed** — new "Unified Hook Lifecycle" section in `docs/HOST_INTEGRATIONS.md` with schema, event-translation table, rendered-surface paths, and the add-a-hook workflow. New entry in `docs/LESSONS_LEARNED.md`.
8. **Final E2E green** — render-registry → sync all 6 governed projects × 3 hosts → `verify-agent-forge.py` EXIT=0 → `validate-triad-runtime.py --project jarvis` EXIT=0 with `overall_pass: true` and `hook_pass: true` on all three hosts (Gemini CLI 27 expected, Claude CLI 27 expected, Codex filesystem-escalated 27/27 with `sandbox_blocked: true`). Live guardian unit re-test blocked `--no-verify` with exit 1 and correct matched-pattern JSON.

Evidence artifact: `runtime/validation/triad/20260424-205818/summary.json`.

### Triad Runtime Validator + Global Skill Propagation Default (2026-04-24, Claude)

Made the runtime gate scripted and fixed a silent under-delivery bug in the omni-factory's propagation logic.

#### Changes Made

1. **`scripts/validate-triad-runtime.py` shipped as the mandatory final gate** — probes Claude / Codex / Gemini live CLIs in sequence, parses each one's enumerated skill list, and compares to canonical `registry.json`. Falls back to filesystem evidence on Codex sandbox blocks (`bwrap: loopback: Failed RTM_NEWADDR`), recording method as `filesystem-escalated` per the 2026-04-23 escalation lesson.
2. **`scripts/validate-codex-runtime.py` retained as the strict Codex-only probe** for cases where the operator wants a single-host check.
3. **`scripts/omni_factory.py` propagation default fixed** — when a global skill omits `delivery_projects`, it now mirrors to every governed project in `projects.json` (was previously treated as "global-only" and silently under-delivered to project-local surfaces). `["*"]` is the explicit wildcard equivalent; `[]` is the explicit opt-out.
4. **`_resolve_project_root` added** — `--project <name>` now translates through `projects.json` rather than assuming `projects_root/name`. Latent bug surfaced when syncing `factory` (root `ZorroForge/factory`).
5. **Workflow Discipline assimilation** — eight new global skills (`spec-architect`, `execution-planner`, `tdd-engineer`, `root-cause-analyst`, `verification-gate`, `subagent-dispatcher`, `branch-finisher`, plus `skill-author` as the meta-skill). `code-review-doctrine` extended with a receiving-feedback discipline section. `AGENTS.md` gained a "Workflow Discipline Chain" block listing the default sequence. Four team manifests (`planning-team`, `delivery-team`, `assessment-team`, `improvement-team`) updated to reference the new skills. Methodology was extracted natively from `obra/superpowers` rather than taken as a third-party plugin.
6. **`AGENTS.md` Rules** — added the rule that `validate-triad-runtime.py` is the mandatory final gate after any canonical skill / team / MCP / hook change.
7. **Final E2E green** — first triad run artifact `runtime/validation/triad/20260424-050553/`. Post-fix sync confirmed all 8 new skills landed in all 6 governed projects × 3 hosts (144/144 surfaces present).

Lesson ledger: 2026-04-23 entry "Assimilate Workflow Discipline Natively" + 2026-04-24 entry "Triad Runtime Validator Promoted To Permanent Gate".

### Omni-Factory Phase 3: Wargame, Purge, And Knowledge Anchor (2026-04-23, Codex)

Finished the final standardization pass needed to make the omni-factory model internally coherent and anti-fragile.

#### Changes Made

1. **Host-ingestion wargame completed** — verified that `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` remain the native boot filenames, so only secondary docs were renamed.
3. **Knowledge anchor added** — `docs/LESSONS_LEARNED.md` is now the canonical append-first ledger for durable lessons and workaround history.
4. **Host boot files added for the factory repo** — `_agent_forge/CLAUDE.md` and `_agent_forge/GEMINI.md` now load the lesson ledger directly.
5. **Capability contract hardened** — `scripts/omni_factory.py` now accepts `targets` as the canonical host key while keeping `hosts` as a compatibility alias.
6. **Gemini context generation widened** — generated project `GEMINI.md` files now import the factory lesson ledger in addition to the shared factory contract.
7. **Codex runtime proof improved** — the validator now implements multi-fault escalation; it strictly probes for sandbox compliance, but if the host blocks sandboxed network namespaces (e.g. `bwrap` issues), it automatically escalates to a non-sandboxed probe to verify that the generated surfaces actually exist.
8. **Legacy Claude source tree purged** — `_agent_forge/claude/` is no longer part of the architecture and has been deleted from the repo.
9. **Knowledge-harvesting capability added** — `skills/global/sprint-harvester/` now exists and is wired into the improvement team manifest.
10. **Stale docs reconciled** — the old Claude-first runbooks and portability docs have been updated for the omni-factory engine, and a final stale-reference sweep has been completed.

10. **Continuation prompt packaged** — `docs/NEXT_AGENT_PROMPT.md` now provides a clean pickup prompt for Claude or Gemini with the current state, constraints, and exact next tasks.

## Current State

- **Milestone:** Release Candidate (2026-04-28). All shippable backlog cleared; only platform-blocked items remain (see below).
- **Registry:** generated compatibility artifact derived from canonical sources; refreshed 2026-04-28.
- **Capabilities:** 30 canonical global skills with host-agnostic metadata. Sprint 5 added `token-optimizer` and `prompt-auto-activator`.
- **Teams:** canonical team manifests, with improvement-team now including lesson harvesting and memory-archivist.
- **Hosts:** Claude, Codex, and Gemini delivery all wired through one sync engine.
- **Knowledge anchor:** `docs/LESSONS_LEARNED.md` holds durable lessons; 9 of 16 entries promoted, 7 remain active.
- **Hooks:** four active cross-host records (`pre-tool-execution-guardian`, six `memory-bridge` per-host records, and `prompt-auto-activator`). Two canonical events exercised: `pre_tool_use` (all hosts), `user_prompt_submit` (Claude+Codex only). `session_start` and `stop` carry the memory-bridge records.
- **MCP:** canonical governance layer is live with one seeded shared stdio server (`forge-factory`) and host-safe alias rendering.
- **Validation:** structural verifier green; triad validation records `hook_pass`, `memory_pass`, `bridge_pass`, and `mcp_pass` per host. Latest jarvis run 33/33 Claude+Codex, 32/32 Gemini (correct — `prompt-auto-activator` excludes Gemini).
- **Suitcase status:** export/deploy path present and host-agnostic; not yet exercised on a real fresh Debian VM or macOS host.
- **Pickup path:** `docs/NEXT_AGENT_PROMPT.md` is the intended operator handoff artifact for Claude or Gemini.

## Remaining Weaknesses (Platform-Blocked)

These items are not in-engineering reach within this generation. They need real machines, kernel-level changes, upstream CLI behavior changes, or operator-driven proof runs. They are documented here so the next-evolution sprint does not block on them.

1. **Host-native MCP management UIs are not equivalent proof surfaces** — project-local `mcp get/list` behavior still differs across Claude, Codex, and Gemini even when the rendered surfaces and direct stdio smoke are correct. The triad validator's `mcp_pass` is the canonical gate; host UIs are spot-check only.
2. **No real Debian VM proof** — export/deploy/bootstrap flows still need a full fresh-machine operator run on a real VM.
3. **No real macOS proof** — MacPorts bootstrap path remains untested.
4. **Claude live hook probing is constrained by headless CLI behavior** — per the 2026-04-26 doctrine, headless `claude -p` cannot prove hooks without bypassing them or stalling on interactive permission. Real Claude live-probe needs an interactive session or the `forge-shell` capability (post-RC roadmap).
5. **Gemini live hook probing is opt-in** — `--probe-invocations` fires actual CLI tool calls and is operator-driven, not a default-on triad gate.
6. **This machine has a Codex sandbox blocker** — `bwrap: loopback: Failed RTM_NEWADDR` prevents Codex from inspecting local shell/file surfaces. The triad validator escalates to filesystem evidence per the 2026-04-23 doctrine.
7. **Team manifests are still conceptual** — orchestration remains manual/operator-driven. Real team-as-runtime is a next-generation capability, not RC polish.

## Resolved Backlog Items

- ~~Content freshness~~ — audited 2026-04-28; expert skills correctly delegate to runtime web search, no embedded stale facts.
- ~~Periodic ledger triage~~ — done 2026-04-28; 9 entries promoted, 7 active, 0 superseded.

## Manual Follow-Up Items (Operator-Driven)

1. Exercise `bootstrap-project.sh --existing` against a real existing repo.
2. Run a real Debian VM proof and a real macOS proof.
3. Broaden MCP proof depth from direct stdio smoke to true host-native tool invocation parity where the CLIs expose a stable project-local MCP inspection path.
4. Resolve the Codex `bwrap` sandbox issue on this machine and rerun the strict `jarvis` probe.
5. Improve Claude and Gemini live-invocation proof depth without relying on headless CLI behavior that bypasses or stalls hooks.

## Next Evolution (Post-RC Sprint)

Extract `obra/superpowers`, `gsd-build/get-shit-done`, and the Reddit "Get Shit Done" framework as native skills under canonical Omni-Factory governance. Per the 2026-04-23 promoted lesson, methodology is the asset; do not take plugin dependencies. Native extraction preserves cross-host portability across Claude, Codex, and Gemini, which is the explicit design goal.

Scope sketch (separate clean pass, not in this RC):

1. Inventory the three sources for unique methodology that is not already in the existing 8-skill workflow chain.
2. Author each new methodology as a discrete `skills/global/<name>/SKILL.md` with canonical frontmatter.
3. Extend the validator and tests for any new canonical patterns introduced.
4. Sync to governed projects, run triad gate, ledger-triage the lessons that came out of the extraction.

## Final Verdict

**Agent Forge has reached its Release Candidate milestone.** The canonical authoring surfaces are stable, the cross-host renderer is hardened, the validation gate is multi-layered, the knowledge anchor is groomed, and the operator handoff is current. The remaining weaknesses are platform-blocked, not in-engineering reach. The factory is ready for the OSS-extraction sprint that the operator's stated end-goal requires.
