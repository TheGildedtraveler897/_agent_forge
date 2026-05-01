# Spec: GSD Native Assimilation

- **Status:** approved (operator requested implementation on 2026-04-30)
- **Evidence pack:** `docs/research/2026-04-30-gsd-evidence-pack.md`
- **Implementation plan:** `docs/plans/2026-04-30-gsd-native-assimilation.md`
- **Branch:** `feat/gsd-extraction-foundation`

## Goal

Assimilate the highest-value productivity patterns from `gsd-build/get-shit-done` into Agent Forge as portable, canonical, triad-validated skills and workflow doctrine.

## Non-Goals

- Do not vendor `get-shit-done` as an npm, git submodule, copied command tree, or copied agent tree.
- Do not add a second canonical state root like `.planning/` to Agent Forge.
- Do not create dozens of eager-loaded commands that increase default token overhead.
- Do not import permission-skip, hook-bypass, or unsafe force automation patterns.
- Do not implement autonomous multi-phase execution until the Agent Forge orchestration log and cost-warden roadmap items exist.
- Do not change generated host delivery surfaces by hand.

## User-Visible Behavior

After the full assimilation completes:

- Operators can run a stricter plan-quality pass before implementation begins.
- Operators can run a goal-backward verifier that checks feature truth, artifacts, wiring, and data flow after execution.
- Small tasks can use a quick/fast path without losing branch discipline, state capture, verification, or commit hygiene.
- Multiple agents can work in parallel through explicit workstreams backed by branches/worktrees and independent continuity cursors.
- Brownfield projects can be mapped into compact codebase intelligence artifacts before planning.
- Future GSD-inspired exploration workflows can run spikes or sketches without polluting durable doctrine until findings are promoted.

## Interfaces

### New Global Skills

All new skills use canonical Omni-Factory frontmatter:

```yaml
---
name: <skill-name>
description: <searchable use-when sentence>
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---
```

Required new skills:

- `skills/global/plan-quality-auditor/SKILL.md`
- `skills/global/goal-verifier/SKILL.md`
- `skills/global/quick-task-runner/SKILL.md`
- `skills/global/workstream-manager/SKILL.md`
- `skills/global/codebase-cartographer/SKILL.md`

Deferred optional skills:

- `skills/global/spike-sketch-lab/SKILL.md`
- `skills/global/progress-reporter/SKILL.md`

### Existing Skill Updates

- `skills/global/spec-architect/SKILL.md`: optional assumption-first mode and stable decision IDs for decisions that must survive planning.
- `skills/global/execution-planner/SKILL.md`: plan metadata for `must_haves`, `wave`, `depends_on`, `file_ownership`, source coverage, and context budget.
- `skills/global/subagent-dispatcher/SKILL.md`: wave execution rules and wave-level integration verification.
- `skills/global/verification-gate/SKILL.md`: handoff path to `goal-verifier` for feature-level completion claims.
- `skills/global/branch-finisher/SKILL.md`: preserve atomic task commit guidance without allowing hook bypasses or force operations.
- `skills/global/context-engineer/SKILL.md`: progress/resume output that names branch, commit, cursor, plan, latest verifier result, and next action.
- `skills/global/quality-gate/SKILL.md`: either defer to `plan-quality-auditor` for plans or absorb only generic scorecard improvements.

### Team Manifest Updates

- `teams/planning-team.json`: add `plan-quality-auditor`, `codebase-cartographer`.
- `teams/delivery-team.json`: add `goal-verifier`, `quick-task-runner`, `workstream-manager`.
- `teams/research-team.json`: add `codebase-cartographer`.
- `teams/assessment-team.json`: add `plan-quality-auditor`, `goal-verifier`.
- `teams/improvement-team.json`: add future `spike-sketch-lab` only after it exists.

### State Mapping

Do not create `.planning/`.

GSD concepts map into Agent Forge state as follows:

- GSD `STATE.md` -> `MEMORY.md active_tasks` plus `dev/active/<slug>/cursor.json`.
- GSD `HANDOFF.json` and `continue-here.md` -> `dev/active/<slug>/handoff.md`.
- GSD `PLAN.md` -> durable `docs/plans/<slug>.md`.
- GSD `SUMMARY.md` -> branch commit messages plus `docs/HANDOFF.md` only at close.
- GSD quick task directory -> `dev/active/quick-<slug>/`.
- GSD workstream -> branch/worktree plus independent cursor.
- GSD codebase mapping -> future project-local `docs/codebase-map/` or `.forge_state/codebase-map/` after a separate schema decision.

## Data Model

Plan metadata added by `execution-planner` should be expressed in plain Markdown with fenced YAML fragments, not a new parser in Sprint 1.

Required metadata fields:

```yaml
must_haves:
  truths:
    - "<observable truth>"
  artifacts:
    - path: "<relative/path>"
      provides: "<why this artifact matters>"
  key_links:
    - from: "<artifact or subsystem>"
      to: "<artifact or subsystem>"
      via: "<connection mechanism>"
wave: 1
depends_on: []
file_ownership:
  - path: "<relative/path>"
    owner_task: "T-01"
source_coverage:
  decisions:
    - "D-01"
context_budget:
  expected_files: 3
  expected_tasks: 2
```

The first implementation should keep validation manual inside skills. Parser/test automation can follow once the text contract is proven.

## Failure Modes

- **Surface bloat:** Too many skills inflate context. Mitigation: five core skills first, optional skills deferred.
- **State split-brain:** `.planning/` competes with `MEMORY.md` and `dev/active`. Mitigation: explicit no-`.planning/` rule.
- **Unsafe automation import:** GSD permission-skip or hook-bypass patterns conflict with Agent Forge doctrine. Mitigation: reject those patterns and cite `branch-finisher`/`telemetry-guardian`.
- **False completion confidence:** Generic tests pass but user-visible goal fails. Mitigation: `goal-verifier`.
- **Planning theater:** Plans look detailed but reduce scope. Mitigation: `plan-quality-auditor` scope-reduction check.
- **Parallel-agent collision:** Agents edit same files or same branch. Mitigation: workstream branch/worktree discipline and `file_ownership`.
- **Claude WIP interference:** Current distillation work is isolated on `feat/distillation-pipeline-wip`. Mitigation: implement GSD work only on `feat/gsd-extraction-foundation`.

## Acceptance Criteria

1. Evidence pack exists at `docs/research/2026-04-30-gsd-evidence-pack.md` and maps every major GSD surface family to assimilate, covered, defer, or reject.
2. This spec exists and states native extraction as the approved architecture.
3. Implementation plan exists at `docs/plans/2026-04-30-gsd-native-assimilation.md` with exact file paths, verification commands, dependencies, and branch preflight.
4. No production skill, policy, team, or renderer behavior changes in this first documentation slice.
5. `python3 scripts/verify-agent-forge.py` exits 0 after the docs are added.
6. The docs commit lands on `feat/gsd-extraction-foundation`, not `master` and not `feat/distillation-pipeline-wip`.
7. The implementation plan names the next skill(s) to use for the actual code/content changes.

## Out-Of-Scope Follow-Ups

- Hook-level prompt-injection guard implementation.
- Runtime model profile resolver.
- Full statusline/context monitor.
- Cross-AI plan review.
- Autonomous milestone execution.
- GSD package installer or npm integration.
- Worktree automation beyond documented branch/workstream discipline.
