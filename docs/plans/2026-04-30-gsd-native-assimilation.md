# Plan: GSD Native Assimilation

- **Spec:** `docs/specs/2026-04-30-gsd-native-assimilation.md`
- **Evidence pack:** `docs/research/2026-04-30-gsd-evidence-pack.md`
- **Execution mode:** staged sequential implementation; subagent dispatch only after file ownership is explicit
- **Branch:** `feat/gsd-extraction-foundation`
- **Branch preflight:** `scripts/enforce-branch-discipline.sh --branch feat/gsd-extraction-foundation --require-upstream`
- **Total tasks:** 15
- **Estimated effort:** 2-4 focused sessions

## Scope

This plan implements GSD methodology inside Agent Forge's canonical model. It does not vendor upstream files. It creates five core skills, upgrades seven existing skills/team manifests, and records the extraction lesson.

## Phase 0 - Documentation Slice Already Covered By This Commit

### T-00 - Land evidence pack, spec, and execution plan

Files:

- `docs/research/2026-04-30-gsd-evidence-pack.md`
- `docs/specs/2026-04-30-gsd-native-assimilation.md`
- `docs/plans/2026-04-30-gsd-native-assimilation.md`

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

## Phase 1 - Core Plan Quality

### T-01 - Create `plan-quality-auditor`

Files:

- `skills/global/plan-quality-auditor/SKILL.md`

Dependencies: T-00

RED check:

```bash
test -f skills/global/plan-quality-auditor/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Canonical frontmatter with `targets: ["claude", "codex", "gemini"]`.
- Use-when description: use before implementation when a plan must be checked for goal delivery.
- Checks: requirement coverage, task completeness, dependency correctness, key links, context budget, `must_haves`, decision coverage, scope-reduction detection, architectural-tier placement, and no placeholder/skip language.
- Output format: blockers, warnings, pass/fail, and revision instructions.
- Must reject plan approval when scope-reduction language hides omitted user decisions.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0 and skill counted in registry after render.

### T-02 - Upgrade `execution-planner` with GSD-derived metadata

Files:

- `skills/global/execution-planner/SKILL.md`

Dependencies: T-01

RED check:

```bash
grep -q "must_haves" skills/global/execution-planner/SKILL.md
```

Expected before task: non-zero unless already added.

GREEN requirements:

- Add plan metadata contract for `must_haves`, `wave`, `depends_on`, `file_ownership`, `source_coverage`, and `context_budget`.
- Add explicit source-coverage audit mapping spec acceptance criteria and locked decisions to task IDs.
- Add plan-quality-auditor as the next gate before implementation begins.
- Preserve existing micro-task, RED test, branch discipline, and checkpoint discipline rules.

Verification:

```bash
grep -q "must_haves" skills/global/execution-planner/SKILL.md
grep -q "plan-quality-auditor" skills/global/execution-planner/SKILL.md
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

### T-03 - Add decision IDs and assumptions mode to `spec-architect`

Files:

- `skills/global/spec-architect/SKILL.md`

Dependencies: T-01

RED check:

```bash
grep -q "Decision IDs" skills/global/spec-architect/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Add optional assumption-first mode when the repo has enough code/context to infer defaults.
- Every locked decision that must survive planning gets a stable `D-NN` identifier.
- Deferred, informational, and discretion decisions are explicitly taggable.
- Preserve one-question-at-a-time as default when assumptions are unsafe.

Verification:

```bash
grep -q "D-01" skills/global/spec-architect/SKILL.md
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

## Phase 2 - Goal-Backward Completion

### T-04 - Create `goal-verifier`

Files:

- `skills/global/goal-verifier/SKILL.md`

Dependencies: T-02

RED check:

```bash
test -f skills/global/goal-verifier/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Canonical frontmatter with all three targets.
- Use when a feature, sprint, or phase completion claim must be verified against user-visible goal truth.
- Must not trust summaries, commit messages, or agent reports as evidence.
- Verification levels: truths, artifacts, substance, wiring, data flow, disabled/skipped tests, circular tests, assertion strength, manual/UAT uncertainty.
- Output: verified, failed blocker, uncertain warning, proof command, evidence path, and fix-plan handoff.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0 and new skill parsed.

### T-05 - Wire `verification-gate` to `goal-verifier`

Files:

- `skills/global/verification-gate/SKILL.md`

Dependencies: T-04

RED check:

```bash
grep -q "goal-verifier" skills/global/verification-gate/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- For task-local claims, keep current five-step assertion protocol.
- For feature/phase/sprint claims, require `goal-verifier` before completion is asserted.
- Clarify that passing tests prove only the tested claim, not overall goal achievement.

Verification:

```bash
grep -q "goal-verifier" skills/global/verification-gate/SKILL.md
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

### T-06 - Add UAT routing to `goal-verifier`

Files:

- `skills/global/goal-verifier/SKILL.md`

Dependencies: T-04

RED check:

```bash
grep -q "UAT" skills/global/goal-verifier/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- If a truth cannot be programmatically verified, produce operator-facing UAT steps.
- UAT steps must be concrete, one deliverable at a time, with expected result and failure triage.
- Failed UAT routes to `root-cause-analyst` or `execution-planner` depending on whether root cause is known.

Verification:

```bash
grep -q "operator-facing UAT" skills/global/goal-verifier/SKILL.md
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

## Phase 3 - Execution Ergonomics

### T-07 - Create `quick-task-runner`

Files:

- `skills/global/quick-task-runner/SKILL.md`

Dependencies: T-05

RED check:

```bash
test -f skills/global/quick-task-runner/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Define `fast`, `quick`, and `quick --validate` tiers.
- All tiers require branch discipline unless the user explicitly asks for integration/release work on the base branch.
- `fast`: trivial one-file/no-code or tiny docs/config edits only; still run relevant verification.
- `quick`: one contained task, small plan summary, proof command, atomic commit.
- `quick --validate`: adds `plan-quality-auditor` before and `goal-verifier` after.
- State captured in `dev/active/quick-<slug>/cursor.json` when more than one step is involved.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

### T-08 - Create `workstream-manager`

Files:

- `skills/global/workstream-manager/SKILL.md`

Dependencies: T-02

RED check:

```bash
test -f skills/global/workstream-manager/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Manage concurrent work as branches/worktrees plus independent `dev/active/<slug>/cursor.json`.
- Commands described as skill workflow actions, not host-specific slash commands.
- Actions: create, list, switch, status, complete, resume.
- Must refuse two agents writing same branch unless deliberately pairing.
- Must record branch, upstream, latest commit, dirty state, next task, and owner.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

### T-09 - Upgrade `subagent-dispatcher` for waves

Files:

- `skills/global/subagent-dispatcher/SKILL.md`

Dependencies: T-02, T-08

RED check:

```bash
grep -q "wave" skills/global/subagent-dispatcher/SKILL.md
```

Expected before task: non-zero or insufficient.

GREEN requirements:

- Read `wave`, `depends_on`, and `file_ownership` metadata from execution plans.
- Parallelize only within same wave and only when file ownership is disjoint.
- Run wave-level integration checks before the next wave starts.
- Record which wave/task each agent owns.
- Do not adopt GSD's hook-bypass commit behavior.

Verification:

```bash
grep -q "file_ownership" skills/global/subagent-dispatcher/SKILL.md
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

### T-10 - Refine branch finishing for atomic task history

Files:

- `skills/global/branch-finisher/SKILL.md`

Dependencies: T-07, T-08

RED check:

```bash
grep -q "atomic task" skills/global/branch-finisher/SKILL.md
```

Expected before task: non-zero unless equivalent already exists.

GREEN requirements:

- Encourage one meaningful commit per completed micro-task or quick task.
- Preserve no hook bypass, no signature bypass, no force to primary branch.
- When keeping a branch, include latest task commit and upstream.
- When merging, run post-merge verification as already required.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

## Phase 4 - Codebase Intelligence

### T-11 - Create `codebase-cartographer`

Files:

- `skills/global/codebase-cartographer/SKILL.md`

Dependencies: T-01

RED check:

```bash
test -f skills/global/codebase-cartographer/SKILL.md
```

Expected before task: non-zero.

GREEN requirements:

- Use when a repo must be mapped before planning or when structural drift is suspected.
- Outputs: stack, architecture, conventions, risks, tests, integrations, entrypoints, generated surfaces, and freshness timestamp.
- Supports `full`, `fast`, `focus quality`, `focus concerns`, and `diff since <ref>` modes.
- Output location defaults to an evidence pack or project-local codebase map; no new `.planning/` root.
- Must separate confirmed facts from inferred patterns.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

### T-12 - Wire team manifests

Files:

- `teams/planning-team.json`
- `teams/delivery-team.json`
- `teams/research-team.json`
- `teams/assessment-team.json`

Dependencies: T-01, T-04, T-07, T-08, T-11

RED check:

```bash
grep -q "plan-quality-auditor" teams/planning-team.json
```

Expected before task: non-zero.

GREEN requirements:

- Planning team preferred entries include `codebase-cartographer` and `plan-quality-auditor`.
- Delivery team preferred entries include `quick-task-runner`, `workstream-manager`, and `goal-verifier`.
- Research team preferred entries include `codebase-cartographer`.
- Assessment team preferred entries include `plan-quality-auditor` and `goal-verifier`.
- Keep JSON valid.

Verification:

```bash
python3 -m json.tool teams/planning-team.json >/tmp/planning-team.json
python3 -m json.tool teams/delivery-team.json >/tmp/delivery-team.json
python3 -m json.tool teams/research-team.json >/tmp/research-team.json
python3 -m json.tool teams/assessment-team.json >/tmp/assessment-team.json
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0.

## Phase 5 - Docs, Registry, Sync, Runtime Gate

### T-13 - Record GSD extraction lesson

Files:

- `docs/LESSONS_LEARNED.md`

Dependencies: T-12

RED check:

```bash
grep -q "GSD Native Assimilation" docs/LESSONS_LEARNED.md
```

Expected before task: non-zero.

GREEN requirements:

- Append a new lesson entry.
- Record that native extraction is the rule, not vendoring.
- Record rejected patterns: permission skip, command bloat, duplicate `.planning/` canonical state.
- Record evidence paths and triad artifact path after validation.

Verification:

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0.

### T-14 - Refresh registry and sync governed projects

Files:

- `registry.json`
- generated host/project surfaces as produced by sync commands

Dependencies: T-13

GREEN requirements:

- Render registry.
- Sync Claude, Codex, and Gemini surfaces for every governed project.
- Run syncs sequentially until `runtime/managed-state.json` gets atomic locking.

Verification:

```bash
python3 scripts/omni_factory.py render-registry > registry.json
python3 scripts/omni_factory.py sync-claude --project jarvis
python3 scripts/omni_factory.py sync-codex --project jarvis
python3 scripts/omni_factory.py sync-gemini --project jarvis
python3 scripts/verify-agent-forge.py
```

Expected: all exit 0. Repeat syncs for all governed projects before final runtime gate.

### T-15 - Run final runtime gate and finish branch

Files:

- `runtime/validation/triad/<stamp>/summary.json` generated by validator
- `docs/HANDOFF.md` only if this sprint is complete and triad-green

Dependencies: T-14

Verification:

```bash
python3 scripts/validate-triad-runtime.py --project jarvis
python3 -m unittest tests.test_hooks_v3 tests.test_memory_bridge tests.test_mcp_namespace tests.test_branch_discipline -v
python3 scripts/verify-agent-forge.py
```

Expected:

- triad `overall_pass: true`
- unit tests pass
- verifier exits 0

Branch finish:

```bash
git status --short
git add <changed files>
git commit -m "Assimilate GSD workflow discipline natively"
git push
```

Then run `branch-finisher` to choose PR/merge/keep.

## Acceptance Mapping

| Spec acceptance criterion | Covered by |
|---|---|
| Evidence pack exists and maps GSD surfaces | T-00 |
| Spec states native extraction | T-00 |
| Plan exists with exact paths and commands | T-00 |
| No behavior changes in docs slice | T-00 verifier and diff review |
| Verifier exits 0 after docs | T-00 |
| Branch is `feat/gsd-extraction-foundation` | T-00 preflight |
| Plan names next skills | T-01 through T-15 |

## Next Skill Handoff

Use `execution-planner` to split Phase 1 into a micro-task plan, then execute through `tdd-engineer` for any tests/scripts and normal skill-authoring discipline for SKILL.md changes. Use `plan-quality-auditor` only after T-01 exists; until then, use `quality-gate` as the weaker temporary review.
