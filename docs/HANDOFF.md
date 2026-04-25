# Agent Forge Handoff

Last updated: 2026-04-25

## What Changed

### Workflow Discipline Post-Mortem: Stalled Tool-Result Delivery (2026-04-25, Claude)

Two silent stalls during the universal state layer sprint were traced to harness-level tool-result delivery failures on compound bash commands, not actual hangs. Captured as `2026-04-25 - Compound Bash Calls Cause Silent Tool-Result Delivery Stalls` in `docs/LESSONS_LEARNED.md`. Two short rules added to `AGENTS.md`: prefer narrow tool calls, and treat `[Tool result missing due to internal error]` as a re-grounding signal rather than a retry signal. New `Operator Tips` section in `AGENTS.md` names the >5-minute silent-stall heuristic so operators know how to unblock cheaply.

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
