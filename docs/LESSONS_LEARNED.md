# Lessons Learned
Last updated: 2026-04-25 (universal state layer + memory-archivist)

This file is the append-first knowledge anchor for Agent Forge.

## Rules

- Add normalized entries here before changing durable doctrine.
- Do not overwrite `AGENTS.md` or `docs/CONOPS.md` as part of harvesting.
- Promote a lesson into doctrine only when it is durable, broad, and worth loading by default.
- Keep secrets, local-only residue, and one-off operator trivia out of this ledger.

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

### 2026-04-23 - Keep Native Boot Files Native

- `Date:` 2026-04-23
- `Context:` Omni-Factory Phase 3 required reconciling stale Claude-branded docs without breaking host-native boot behavior.
- `Lesson:` Native boot filenames still matter. `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` should keep their host-specific names, while secondary integration runbooks can be renamed safely.
- `Architectural Decision:` Keep host boot files native and rename only secondary docs to host-agnostic names such as `HOST_INTEGRATIONS.md` and `TRIAD_RUNTIME_VALIDATION.md`.
- `Evidence:` 2026 official docs for Claude Code memory, Codex `AGENTS.md`, and Gemini `GEMINI.md`; Phase 3 wargame and repo reconciliation pass.
- `Promotion Target:` `docs/HOST_INTEGRATIONS.md`
- `Status:` active

### 2026-04-23 - Codex Needs AGENTS-Led Access To The Lesson Ledger

- `Date:` 2026-04-23
- `Context:` Claude and Gemini can import `docs/LESSONS_LEARNED.md` directly, but Codex does not auto-load arbitrary docs paths the same way.
- `Lesson:` A separate lesson ledger works best when Claude and Gemini import it directly and Codex is explicitly pointed to it through `AGENTS.md`, generated agent instructions, and validation prompts.
- `Architectural Decision:` Keep the canonical knowledge anchor at `docs/LESSONS_LEARNED.md`. Load it natively through `CLAUDE.md` and `GEMINI.md`, and require Codex-facing docs and runtime probes to consult it deliberately.
- `Evidence:` Codex `AGENTS.md` discovery rules, Gemini `@` imports, Claude `@` imports, and Phase 3 runtime-validation design.
- `Promotion Target:` `docs/TRIAD_RUNTIME_VALIDATION.md`
- `Status:` active

### 2026-04-23 - Delete Legacy Host-Specific Source Trees Once The Generator Owns Delivery

- `Date:` 2026-04-23
- `Context:` `_agent_forge/claude/` survived after the omni-factory migration even though the generator no longer read it.
- `Lesson:` Leaving an unused legacy adapter tree behind creates false source-of-truth signals and stale documentation drift.
- `Architectural Decision:` Generated Claude, Codex, and Gemini surfaces must come only from canonical capability metadata plus the shared omni-factory engine. Remove dead source trees once the replacement path is verified.
- `Evidence:` `scripts/omni_factory.py` capability discovery, stale-doc audit, and the Phase 3 purge plan.
- `Promotion Target:` `docs/PORTABILITY.md`
- `Status:` active

### 2026-04-23 - Distinguish Codex Sandbox Failure From Missing Generated Surfaces

- `Date:` 2026-04-23
- `Context:` The live Codex runtime probe against `jarvis` returned a structured failure even though `.agents/skills`, `.codex/agents`, `.codex/config.toml`, and `~/.agents/skills/sprint-harvester` were present on disk.
- `Lesson:` On this machine, Codex's internal sandbox can fail local shell/file inspection with `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. A failed runtime proof does not automatically mean the omni-factory failed to generate surfaces.
- `Architectural Decision:` Keep the live probe strict and report `pass: false` when Codex cannot confirm visibility, but pair that result with direct filesystem evidence before deciding the generator is broken.
- `Evidence:` `runtime/validation/codex/20260423-194504/`, generated Jarvis `.agents/` and `.codex/` surfaces, and `~/.agents/skills/sprint-harvester`
- `Promotion Target:` `docs/TRIAD_RUNTIME_VALIDATION.md`
- `Status:` active

### 2026-04-23 - Implement Multi-Fault Validation Escalation For Sandboxed Probes

- `Date:` 2026-04-23
- `Context:` A strict sandbox failure hides whether the factory actually generated the correct files.
- `Lesson:` When a host-native probe fails due to environmental sandbox constraints (like `bwrap` network issues), the validator should automatically escalate to a non-sandboxed probe to verify the underlying structural integrity.
- `Architectural Decision:` Use a two-phase "strict then escalated" probe model. Report strict `pass: false` if it fails sandboxed, but run an escalated probe (`--dangerously-bypass-approvals-and-sandbox`) to prove file visibility.
- `Evidence:` Updated `scripts/omni_factory.py` with `host_sandbox_blocked` logic and `escalated_pass` metrics.
- `Promotion Target:` `docs/TRIAD_RUNTIME_VALIDATION.md`
- `Status:` active

### 2026-04-23 - Assimilate Workflow Discipline Natively Instead Of Importing Third-Party Plugins

- `Date:` 2026-04-23
- `Context:` The factory's governance skills were strong but its *workflow-discipline* surface was weak — no canonical skill enforced brainstorming gates, micro-task planning, RED/GREEN/REFACTOR, root-cause-before-fix, or fresh-evidence completion. An overeager LLM could still skip straight from "got it" to committed code. The `obra/superpowers` project has these disciplines but is host-specific and third-party.
- `Lesson:` Extract external workflow philosophies as agent-agnostic native skills rather than taking a dependency. The methodology is the asset; the plugin is not. Role-based naming and Omni-Factory frontmatter make the reforge pass the verifier on the first run, and every host (Claude, Codex, Gemini) receives identical discipline.
- `Architectural Decision:` Added seven new global workflow skills (`spec-architect`, `execution-planner`, `tdd-engineer`, `root-cause-analyst`, `verification-gate`, `subagent-dispatcher`, `branch-finisher`) plus `skill-author` as the meta-skill for future skill authoring. Extended `code-review-doctrine` with a receiving-feedback discipline section. Added a "Workflow Discipline Chain" block to `AGENTS.md` listing the default sequence. Four team manifests (`planning-team`, `delivery-team`, `assessment-team`, `improvement-team`) now reference the new skills in their `preferred_entries` and tightened their `stop_condition` and `handoff_artifacts` to match.
- `Evidence:` New SKILL.md files under `skills/global/`, updated team manifests under `teams/`, updated `AGENTS.md` Workflow Discipline Chain section, regenerated `registry.json`, passing `scripts/verify-agent-forge.py`.
- `Promotion Target:` `docs/CONOPS.md` §Capability Model — once the new skills are proven across two or three governed projects, elevate the chain from AGENTS.md into a first-class CONOPS section.
- `Status:` active

### 2026-04-24 - Triad Runtime Validator Promoted To Permanent Gate; Global Skills Propagate To All Governed Projects By Default

- `Date:` 2026-04-24
- `Context:` The superpowers assimilation passed the structural verifier, but a manual runtime check revealed two real gaps. (1) `scripts/verify-agent-forge.py` only proves files exist on disk; it never asks the Claude, Codex, or Gemini CLIs to enumerate what they can actually see. (2) `omni_factory.py` treated an absent `delivery_projects` key as "global-only" rather than "deliver everywhere", so the 8 new workflow skills landed at `~/.agents/skills/`, `~/.claude/commands/`, and `~/.gemini/commands/` but did **not** mirror into any governed project's local surface. The jarvis project-local surfaces were missing the entire workflow-discipline chain.
- `Lesson:` Structural-smoke tests are necessary but insufficient. "Generated on disk" is not the same as "reachable at runtime". An opt-in delivery default silently under-delivers; the right default for a portable, suitcase-export-style factory is "propagate everywhere governed, opt out explicitly when narrowing is intentional".
- `Architectural Decision:` Three changes. (a) In `scripts/omni_factory.py`, when a global skill omits `delivery_projects`, default to every governed project listed in `projects.json`. Support `["*"]` as an explicit wildcard equivalent, and keep `[]` as the explicit opt-out for user-home-only skills. (b) Added `_resolve_project_root` so `--project <name>` translates through `projects.json` rather than assuming `projects_root/name` — this was a latent bug that only surfaced when we synced the `factory` project (root `ZorroForge/factory`). (c) New `scripts/validate-triad-runtime.py` is now the mandatory final gate after any canonical skill/team/MCP/hook change. It probes each host's live CLI and records expected-vs-observed skill counts, falling back to filesystem evidence for sandbox-blocked hosts per the 2026-04-23 escalation doctrine. `AGENTS.md` Rules now names the triad validator as the final gate; `docs/TRIAD_RUNTIME_VALIDATION.md` replaces the old manual-prompt runbook with the scripted path and keeps the prompts as a documented fallback.
- `Evidence:` `scripts/omni_factory.py` (lines around 251 and 256 for default propagation, wildcard, and `_resolve_project_root`); `scripts/validate-triad-runtime.py`; first live run artifact `runtime/validation/triad/20260424-050553/summary.json` (overall `pass: true`; Gemini `cli` 27/26 observed; Claude `cli` 39/26 observed; Codex `filesystem-escalated` 26/26 with `sandbox_blocked: true`); `runtime/validation-matrix.json` triad_runtime.jarvis entry. Post-fix sync confirms all 8 new skills land in all 6 governed projects × 3 hosts (144/144 surfaces present).
- `Promotion Target:` `docs/CONOPS.md` §Capability Model for the propagation default; `docs/CONOPS.md` §Runtime Validation for the new triad-gate requirement. Promote after the gate has caught at least one real regression in production use.
- `Status:` active

### 2026-04-24 - Unified Hook Lifecycle Across Claude Codex Gemini; Telemetry Guardian As Universal Pre-Tool Veto

- `Date:` 2026-04-24
- `Context:` `policies/hooks.json` existed as a canonical input but was only wired to Codex. Claude and Gemini had no hook renderer at all — their `settings.json` surfaces didn't even have a `hooks` key. This meant hostile or careless tool invocations (`git commit --no-verify`, `git push --force origin main`, `rm -rf $HOME`, `terraform destroy` without `-target`, recursive 777 on home) had no universal guardrail. PATHFINDER architectural upgrade #2 called for a unified hook lifecycle and a `telemetry-guardian` capability (#3 in the backlog) as the universal pre-tool veto.
- `Lesson:` Host-partitioned canonical sources silently rot when only one host has a renderer. The fix is to (a) hold the hook schema as shared records with a `targets` array that the renderers each translate into their host's native event names, (b) enforce via the verifier that every referenced command script actually exists, and (c) extend the triad runtime validator to prove the hook reached each host's rendered surface — not just that the canonical JSON carries it.
- `Architectural Decision:` (a) Bumped `policies/hooks.json` to schema version 2 with a top-level `shared` array plus host-specific arrays. Each record carries `id`, `event`, `matcher`, `command`, `targets`, optional `timeout_ms`, `status_message`, `description`. (b) Added `claude_hook_payload()` and `gemini_hook_payload()` renderers in `omni_factory.py` next to the existing Codex renderer; all three pull from `_hooks_for_host(host)` which merges shared + own. Claude writes `.claude/settings.json`, Gemini merges hooks into `.gemini/settings.json`, Codex continues to emit `.codex/hooks.json`. (c) Event names translate via `_EVENT_ALIASES`. (d) New skill `skills/global/telemetry-guardian/` with POSIX `guardian.sh` deny list (`--no-verify`, force-push-to-protected, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777 on home, `--no-gpg-sign`, explicit `git reset --hard <ref>`). Opt out with `AGENT_FORGE_GUARDIAN=off`, logged to `~/.agent-forge/guardian.log`. (e) `verify()` now parses `hooks.json`, checks every record has `id`/`event`/`command`, and verifies referenced `bash <script>` paths exist. (f) `validate-triad-runtime.py` now runs a `hook_surface_for(host, project_root)` check after skill enumeration and attaches `hook_surface` to each host result; overall pass requires both skill enumeration AND hook-surface presence.
- `Evidence:` `policies/hooks.json` (version 2 schema with `shared[0]` = `pre-tool-execution-guardian`); `scripts/omni_factory.py` (`_hooks_for_host`, `codex_hook_payload`, `claude_hook_payload`, `gemini_hook_payload`, `_EVENT_ALIASES`, `sync_claude` writing `.claude/settings.json`, `render_gemini_settings` injecting `hooks` block, extended `verify()` checks); `skills/global/telemetry-guardian/SKILL.md` and `guardian.sh` (tested with 7 invocations: 3 allowed, 4 blocked, 1 bypassed correctly); `scripts/validate-triad-runtime.py` `hook_surface_for` check added.
- `Promotion Target:` `docs/CONOPS.md` §Hook Governance — promote once at least one additional cross-host hook has been added and survived a full sync cycle across all 6 governed projects.
- `Status:` active

### 2026-04-25 - Universal State Layer + Memory Archivist; Triad Validator Gains memory_surface_for + Refined Sandbox Detection

- `Date:` 2026-04-25
- `Context:` Pathfinder Roadmap Architectural Upgrade #1 called for a cross-host shared brain — Claude Auto-Memory, Codex Chronicle, and Gemini Memory v2 each siloed knowledge in host-native shapes. Without a canonical layer, an overnight insight in one host vanished from the others. Capability #1 (`memory-archivist`) was the partner skill that exercises the protocol; without a writer, the layer is dead weight.
- `Lesson:` The pattern that worked for the hook lifecycle (canonical schema + three host renderers + verifier coverage + validator gate + skill that exercises the layer) generalizes. Reusing it cut decision overhead — copy `policies/hooks.json` shape into `policies/memory.json`, copy `hook_surface_for` into `memory_surface_for`, copy `telemetry-guardian` skill scaffolding into `memory-archivist`. The second time we ran this rhythm, it took roughly half the time of the first. Also: Codex's sandbox-block error string can change between releases. The triad validator's `host_sandbox_blocked()` matched only `bwrap: loopback: Failed RTM_NEWADDR`, but on the 2026-04-25 run Codex emitted `shell tool failed before command execution` / `needs access to create user namespaces` / `shell tool is blocked by the sandbox`. Without an updated marker list, the validator stayed in `cli` method, reported `missing=28/28`, and FAILed even though all surfaces were on disk. The fix is to keep the marker list as a curated allow-list of known sandbox-block phrases and update it whenever Codex changes its error output.
- `Architectural Decision:` (a) Canonical schema at `policies/memory.json` v1 with five sections (build_commands, project_quirks, active_tasks, recent_decisions, known_failures), retention 50/warn-at-40, secrets_policy=deny. `active_tasks` is the only rewriteable section. (b) `scripts/omni_factory.py` gains `_memory_sections()`, `render_memory_md()`, `render_forge_state_readme()`, `render_forge_state_manifest()`, and `sync_memory()`; the latter is called from `sync_claude` / `sync_codex` / `sync_gemini` so memory writes propagate to every governed project. (c) `render_project_gemini_md` adds `@MEMORY.md` import. (d) `AGENTS.md` Read Order gains a fifth entry pointing every host at `<project>/MEMORY.md` — single edit covers Claude / Codex / Gemini reachability. (e) `verify()` parses `policies/memory.json` and checks every governed project has `MEMORY.md` with all section anchors and a well-formed `.forge_state/manifest.json`. (f) `skills/global/memory-archivist/` ships with `SKILL.md` (workflow class, all-host targets) and `archivist.py` providing `append`, `validate`, `summary` subcommands; secrets-deny patterns reject API keys, private keys, and credential-shaped strings; audit log at `<project>/.forge_state/archivist.log`. (g) `scripts/validate-triad-runtime.py` gains `memory_surface_for(host, project_root)` parallel to `hook_surface_for`. Overall pass now requires skill + hook + memory surfaces. Per-host matrix entry adds `memory_pass`. (h) `host_sandbox_blocked()` marker list extended with the new Codex error strings.
- `Evidence:` `policies/memory.json`; `scripts/omni_factory.py` (memory renderers, `MEMORY_POLICY_PATH`, extended `verify()`); `AGENTS.md` Read Order entry 5; `skills/global/memory-archivist/SKILL.md` and `archivist.py` (live unit-tested: append OK, validate OK, secrets-deny rejected `API_KEY=...` with exit 2); `scripts/validate-triad-runtime.py` (`memory_surface_for`, expanded sandbox-marker list); `runtime/validation/triad/20260425-174222/summary.json` (overall pass=true, all three hosts hook_pass=true memory_pass=true, 28/28 skills, Codex `filesystem-escalated` after sandbox detection upgrade); `teams/improvement-team.json` (memory-archivist wired alongside sprint-harvester); `runtime/validation-matrix.json` (per-host memory_pass field).
- `Promotion Target:` `docs/CONOPS.md` §Capability Model — promote the "policy schema + three renderers + skill that exercises it" rhythm into first-class CONOPS doctrine once a third paired sprint succeeds. The two data points so far (hook lifecycle 2026-04-24, memory layer 2026-04-25) are convergent but a third confirms the pattern is robust.
- `Status:` active
