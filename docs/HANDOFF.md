# Agent Forge Handoff

Last updated: 2026-04-27

## What Changed

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

- **Registry:** generated compatibility artifact derived from canonical sources
- **Capabilities:** canonical `SKILL.md` capabilities with host-agnostic metadata plus `sprint-harvester`
- **Teams:** canonical team manifests, with improvement-team now including lesson harvesting
- **Hosts:** Claude, Codex, and Gemini delivery all wired through one sync engine
- **Knowledge anchor:** `docs/LESSONS_LEARNED.md` holds durable lessons before doctrine promotion
- **MCP:** canonical governance layer exists, but `global-mcp.json` is intentionally empty until real shared servers are added
- **Validation:** structural verifier is green; Codex runtime validation now returns a strict structured result; Claude/Gemini checks remain runbook-driven
- **Suitcase status:** export/deploy path still present and should now describe host-agnostic surfaces instead of the retired Claude-first model
- **Pickup path:** `docs/NEXT_AGENT_PROMPT.md` is the intended operator handoff artifact for Claude or Gemini

## Remaining Weaknesses

1. **No live MCP servers yet** — the governance layer exists but has not been exercised with real shared MCP definitions.
2. **No real Debian VM proof** — export/deploy/bootstrap flows still need a full fresh-machine operator run.
3. **No real macOS proof** — MacPorts bootstrap path remains untested.
4. **No automated Claude runtime validator yet** — Claude still relies on a documented manual runtime pass rather than an in-repo probe script.
5. **No automated Gemini runtime validator yet** — Gemini runtime validation is still runbook-driven.
6. **This machine has a Codex sandbox blocker** — the live `jarvis` probe completed, but Codex could not inspect local shell/file surfaces because its internal sandbox hit `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`.
7. **Team manifests are still conceptual** — orchestration remains manual/operator-driven.
8. **Content freshness** — domain skills still embed date-sensitive knowledge that requires periodic refresh.

## Manual Follow-Up Items

1. Regenerate and commit `registry.json` from `scripts/omni_factory.py render-registry`
2. Run `scripts/verify-agent-forge.py` after the doc and registry updates are committed
3. Exercise `bootstrap-project.sh --existing` against a real existing repo
4. Run a real Debian VM proof and a real macOS proof
5. Add the first real shared MCP server to `global-mcp.json` and test all three host renderers
6. Resolve the Codex `bwrap` sandbox issue on this machine and rerun the strict `jarvis` probe
7. Add automated Claude and Gemini runtime probes so all three hosts have comparable proof depth
8. Periodically promote or supersede entries from `docs/LESSONS_LEARNED.md` instead of letting the ledger become a second backlog

## Final Verdict

**Agent Forge now has the right canonical shape for an omni-factory with an explicit anti-entropy loop.**

It is no longer defensible to describe the repo as "Claude adapters plus some Codex skills." The source of truth now lives in capability metadata, team manifests, project catalog, MCP inventory, hook policy, and a durable lesson ledger, with host-native surfaces generated outward from there.
