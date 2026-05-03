# Evidence Pack: GSD Native Assimilation

- **Question:** How should Agent Forge incorporate useful methodology from `gsd-build/get-shit-done` without losing cross-host governance, token discipline, or canonical-source control?
- **Date:** 2026-04-30
- **Conclusion:** Extract GSD patterns natively. Do not vendor the package, command tree, or agent tree wholesale.

## Source Table

| Source | Type | Relevant claims |
|---|---|---|
| [GSD README](https://github.com/gsd-build/get-shit-done) | Upstream public docs | GSD is a context-engineering and spec-driven development system for many coding runtimes; core lifecycle is new-project, discuss, plan, execute, verify, ship; README also warns that the full surface has material eager-token overhead and documents a minimal mode. |
| [GSD Architecture](https://github.com/gsd-build/get-shit-done/blob/main/docs/ARCHITECTURE.md) | Upstream architecture | GSD uses command, workflow, agent, CLI-tool, hook, and file-state layers. It emphasizes fresh context per agent, thin orchestrators, `.planning/` state, defense in depth, wave execution, context budgets, hooks, runtime adaptation, and drift gates. |
| [GSD Inventory](https://github.com/gsd-build/get-shit-done/blob/main/docs/INVENTORY.md) | Upstream inventory | The documented surface includes 33 agents, 65 shipped commands, 85 workflows, 51 references, 33 CLI modules, and 11 hooks. The inventory explicitly says counts can drift and should be checked against the tree. |
| [GSD User Guide](https://github.com/gsd-build/get-shit-done/blob/main/docs/USER-GUIDE.md) | Upstream user workflow | User-facing workflow includes discuss -> plan -> execute -> verify -> ship, plus Nyquist validation, assumptions mode, decision coverage gates, UI design contracts, spikes, sketches, backlog, seeds, threads, workstreams, UAT, code review, quick scan, and recovery flows. |
| [gsd-plan-checker](https://github.com/gsd-build/get-shit-done/blob/main/agents/gsd-plan-checker.md) | Upstream agent | Strongest plan-quality material: goal-backward verification before execution, requirement coverage, task completeness, dependency correctness, key links, scope sanity, must-haves, context compliance, scope-reduction detection, and architecture-tier compliance. |
| [gsd-verifier](https://github.com/gsd-build/get-shit-done/blob/main/agents/gsd-verifier.md) | Upstream agent | Strongest post-execution verification material: do not trust summaries; verify truths, artifacts, wiring, data flow, stubs, missing files, orphaned artifacts, and hollow/static data. |
| [gsd-executor](https://github.com/gsd-build/get-shit-done/blob/main/agents/gsd-executor.md) | Upstream agent | Execution discipline: atomic task commits, deviation rules, checkpoints, auth gates, continuation protocol, TDD handling, and analysis-paralysis guard. |
| `AGENTS.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, `docs/LESSONS_LEARNED.md` | Agent Forge local doctrine | Agent Forge already mandates canonical skills, host rendering, triad validation, memory bridge, checkpoint discipline, branch discipline, and native extraction of third-party methodologies. |

## Confirmed Findings

### 1. GSD's value is mostly methodology, not runtime code

GSD's architecture is a host-adapter framework around markdown commands, workflows, agents, references, CLI tools, hooks, and `.planning/` state. Agent Forge already has the more general canonical-renderer architecture for Claude, Codex, and Gemini. Importing GSD as a dependency would duplicate Agent Forge's host delivery layer instead of improving it.

Practical implication: assimilate concepts into `skills/global/`, `teams/`, `policies/`, and docs; do not add `get-shit-done` as a package dependency or copy its entire command/agent tree.

### 2. GSD's full surface would be too heavy for Agent Forge's default load path

GSD's README documents a full surface with dozens of skills/commands and agents and a minimal mode to reduce eager token overhead. Agent Forge has already built `token-optimizer`, `context-engineer`, and canonical skill delivery. The correct assimilation pattern is selective, not exhaustive.

Practical implication: add a small number of high-leverage skills and upgrade existing skills. Avoid 60+ new commands that all hosts enumerate.

### 3. GSD's strongest planning improvement is goal-backward preflight

The `gsd-plan-checker` approach is materially stronger than Agent Forge's current `quality-gate` for implementation plans. It verifies whether plans will achieve the goal, not whether they merely look complete. Its most valuable checks are:

- requirement coverage
- task completeness
- dependency graph correctness
- key artifact links
- context budget sanity
- `must_haves` derivation
- locked decision coverage
- scope-reduction detection
- architectural-tier fit

Practical implication: add a dedicated `plan-quality-auditor` or upgrade `quality-gate` and `execution-planner` with these dimensions.

### 4. GSD's strongest completion improvement is post-execution goal verification

The `gsd-verifier` workflow is more adversarial than Agent Forge's current completion pattern. It treats summaries as claims, not evidence, and verifies truths, artifacts, wiring, and data flow. Agent Forge's `verification-gate` already requires fresh commands, but it does not yet provide a reusable goal-backward verification skill for feature completeness.

Practical implication: create `goal-verifier` or extend `verification-gate` with a mode for goal-level artifact/wiring/data-flow verification.

### 5. GSD's wave execution maps cleanly to Agent Forge subagent discipline

GSD groups plans into dependency waves, executes independent plans in parallel, and uses fresh contexts per executor. Agent Forge's `subagent-dispatcher` already enforces independence checks and fresh context, but lacks explicit wave metadata, file-ownership manifests, and wave-level integration rules.

Practical implication: extend `execution-planner` and `subagent-dispatcher` with `wave`, `depends_on`, `file_ownership`, and wave-level verification rules.

### 6. GSD's state model overlaps with Agent Forge but adds useful operators

GSD stores state in `.planning/` and includes pause/resume, progress, stats, threads, seeds, backlog, quick tasks, workstreams, and workspace state. Agent Forge already has `MEMORY.md`, `.forge_state/`, `dev/active/<slug>/cursor.json`, branch discipline, and handoff rules. GSD adds better user-facing operators around those primitives.

Practical implication: do not create a competing `.planning/` root. Implement GSD state ideas against Agent Forge primitives:

- `.planning/STATE.md` -> `MEMORY.md active_tasks` plus `dev/active/<slug>/cursor.json`
- `.planning/HANDOFF.json` -> `dev/active/<slug>/handoff.md`
- `.planning/quick/` -> `dev/active/quick-<slug>/`
- `.planning/threads/` -> either `MEMORY.md recent_decisions` or a future governed `docs/threads/` design
- `.planning/seeds/` -> roadmap/ledger follow-ups, not hidden backlog
- `.planning/workstreams/` -> branch plus worktree plus isolated cursor state

### 7. GSD security material should strengthen hooks and artifact intake

GSD includes prompt-injection scanning, path traversal prevention, safe JSON/shell handling, read-before-edit guards, workflow guards, and commit validation. Agent Forge already has `telemetry-guardian`, hook governance, and no-bypass rules. The missing pieces are prompt-injection scanning for generated planning artifacts and read-before-edit/workflow-context advisories.

Practical implication: add prompt-artifact hygiene to future `plan-quality-auditor` / `goal-verifier`, and defer hook-level prompt guards until the non-command hook sentinel debt is resolved.

### 8. GSD's quick/fast split is worth copying with stronger guardrails

GSD has fast inline tasks and quick tracked tasks. Agent Forge currently has a heavy workflow chain that can be overkill for small work. However, fast paths must not bypass branch discipline, fresh verification, or final commit hygiene.

Practical implication: add `quick-task-runner` with tiers:

- `fast`: trivial docs or one-line config; still requires feature branch or explicit primary-branch integration exception
- `quick`: one contained task with plan summary, proof command, and atomic commit
- `quick --validate`: adds plan-quality and goal-verifier checks

### 9. GSD's brownfield codebase intelligence is a good next layer

GSD's `map-codebase`, `graphify`, `scan`, `intel`, drift detection, docs ingest, and docs update workflows are directly useful for Agent Forge. Agent Forge has `evidence-packager`, `portability-auditor`, and project-specific skills, but lacks a reusable codebase cartography skill.

Practical implication: add `codebase-cartographer` as a global skill for stack, architecture, conventions, risks, test surfaces, integration surfaces, and freshness/drift checks.

### 10. GSD's spikes and sketches should become optional exploration skills

GSD's spike/sketch workflows turn uncertainty into evidence before planning. Agent Forge already has `spec-architect`, but not a dedicated experimental lab skill.

Practical implication: add `spike-sketch-lab` after core planning/verification improvements. It should write throwaway experiments under `dev/active/<slug>/experiments/` and promote durable lessons only through `sprint-harvester` or `skill-author`.

## Local Comparison Matrix

| GSD pattern | Agent Forge current surface | Gap | Assimilation decision |
|---|---|---|---|
| New project questions/research/requirements/roadmap | `spec-architect`, `project-bootstrap`, `onboarding-guide` | Agent Forge has better governance but less product-roadmap scaffolding | Already covered for factory work; selectively add product-intake prompts later. |
| Discuss phase | `spec-architect` | Agent Forge asks one-question-at-a-time; GSD adds assumptions mode and decision IDs | Enhance `spec-architect` with optional assumption-first mode and decision IDs. |
| Plan phase | `execution-planner` | Missing GSD `must_haves`, wave metadata, source coverage, context budget | Upgrade `execution-planner`. |
| Plan checker | `quality-gate` | Current gate is generic; GSD plan checker is stronger and adversarial | Add `plan-quality-auditor` or major `quality-gate` mode. |
| Execute phase | `tdd-engineer`, `subagent-dispatcher` | Missing wave metadata, atomic-per-task history rule, checkpoint table | Upgrade existing skills; do not create another executor. |
| Goal verifier | `verification-gate` | Fresh evidence exists, but goal-backward artifact/wiring/data-flow checks are missing | Add `goal-verifier`. |
| Verify work/UAT | `verification-gate`, user-driven checks | No structured UAT artifact | Add UAT section to `goal-verifier`; optional `operator-uat` later. |
| Quick/fast | none dedicated | Current workflow may be too heavy for small safe tasks | Add `quick-task-runner`. |
| Workstreams/workspaces | branch discipline, `dev/active`, worktrees manually | No operator skill for multi-agent branch/worktree lanes | Add `workstream-manager`. |
| Pause/resume/progress | `context-engineer`, `memory-archivist`, `continuity_cursor.py` | Primitives exist; operator affordances are thin | Upgrade `context-engineer`; possibly add `progress-reporter`. |
| Codebase mapping/intel | `evidence-packager`, project skills | No canonical map/scan skill | Add `codebase-cartographer`. |
| Drift gate | `multi-agent-governor`, tech debt note | No post-execute map freshness gate | Defer to `codebase-cartographer` v2. |
| Security prompt guard | `telemetry-guardian`, hook policy | No prompt-injection scan for planning artifacts | Add to `plan-quality-auditor`; hook sentinel later. |
| Read-before-edit guard | AGENTS/editing rules | Rules exist but no hook/skill check | Defer to hook hardening. |
| Statusline/context monitor | `token-optimizer`, `context-engineer` | No live context threshold hook | Defer to A4/B3/B5 or prompt-auto-activator extension. |
| Model profiles | skill `model_tier` frontmatter | No runtime budget decisioning | Defer to cost-warden/router-overseer. |
| UI design contract/review | `brand-guardian` | GSD has workflow-specific UI-SPEC and review | Enhance `brand-guardian` later; not Sprint 1. |
| Spike/sketch | none dedicated | Useful for reducing uncertainty before planning | Add `spike-sketch-lab` after core. |
| Backlog/seeds/threads | `LESSONS_LEARNED`, roadmap, `MEMORY.md` | No structured lightweight idea capture | Defer until after core state operators. |
| Docs ingest/update | no dedicated global doc updater | Useful but less urgent | Defer to `codebase-cartographer` v2 or `wiki-compiler`. |
| Cross-AI review | `subagent-dispatcher`, future router | Needs orchestration/cost logs | Defer to A4/B6/B9. |
| Autonomous all-phase execution | future `auto-loop`, `crew-director` | Not safe before orchestration log/cost-warden | Defer explicitly. |

## Extraction Priority

### Sprint 1: Evidence and contracts

- This evidence pack.
- Spec for GSD native assimilation.
- Execution plan for core assimilation bundle.

### Sprint 2: Core planning and verification

- `plan-quality-auditor`.
- `goal-verifier`.
- `execution-planner` upgrades.
- `verification-gate` handoff integration.

### Sprint 3: Execution ergonomics

- `quick-task-runner`.
- `workstream-manager`.
- `subagent-dispatcher` wave metadata upgrades.
- `branch-finisher` atomic-history refinements.

### Sprint 4: Codebase intelligence

- `codebase-cartographer`.
- drift/freshness warnings.
- docs ingest/update hooks into `wiki-compiler` roadmap.

### Sprint 5: Exploration and UX

- `spike-sketch-lab`.
- `brand-guardian` UI design contract and review mode.
- backlog/seeds/thread capture model if still needed.

### Later: Orchestration and automation

- cross-AI plan review
- statusline/context monitor
- autonomous mode
- model profiles/cost profiles
- crew-director execution

These depend on Agent Forge A4/B3/B6/B9 roadmap items so routing, cost, and audit logs exist before autonomy expands.

## Conflicts And Uncertainty

- GSD README and inventory use different surface terms/counts across release-era docs. The implementation pass should use upstream `docs/INVENTORY.md` plus a live tree listing as the source of truth.
- GSD recommends permission-skip style automation in some paths. Agent Forge must not import that pattern because `branch-finisher` and `telemetry-guardian` explicitly refuse hook/signature bypasses.
- GSD is optimized around Claude-style command/workflow files and then adapts outward. Agent Forge's canonical model is host-agnostic first. Any copied GSD text must be rewritten into agent-agnostic skill language before landing.
- GSD's `.planning/` state is intentionally git-visible. Agent Forge's active state is split between durable `docs/plans`, rewriteable `MEMORY.md`, local `dev/active`, and `.forge_state`. The extraction must map ideas onto that model rather than introduce a second state root.

## Recommended Next Step

Proceed with the approved spec and execution plan in `docs/specs/2026-04-30-gsd-native-assimilation.md` and `docs/plans/2026-04-30-gsd-native-assimilation.md`.
