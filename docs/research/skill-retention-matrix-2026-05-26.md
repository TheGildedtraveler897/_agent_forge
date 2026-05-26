# Skill Retention / Consolidation Matrix

Date: 2026-05-26 (enterprise-readiness audit)
Scope: 30 global skills under `skills/global/`. Project-local skills: none.

## Verdict summary

**Zero deletions, zero merges this pass.** The apparent "overlap" flagged by a
naive read was entirely **README drift**, not duplicated skills: the README
listed four skills that do not exist on disk (`code-review-doctrine`,
`quality-gate`, `quick-task-runner`, `workstream-manager`) and omitted two that
do (`e2e-qa-tester`, `paranoid-reviewer`). `paranoid-reviewer` already
consolidated the legacy `code-review`/`quality-gate` flows (per `AGENTS.md`);
the legacy folders were already gone. The README is now synced to disk.

All 30 skills satisfy the agentskills.io spec: `name` matches the parent
directory, `description` present, `SKILL.md` under the 500-line / 5000-token
recommendation (largest: `onboarding-guide` at 360 lines).

## Matrix

| Skill | Class | Lines | Scripts | Delivery | Purpose (one line) | Overlap / verdict |
|---|---|---|---|---|---|---|
| spec-architect | workflow | 92 | — | all | Adversarial one-question spec discovery + section approval | Chain step 1. Keep. |
| execution-planner | workflow | 213 | — | all | Decompose approved spec into micro-tasks w/ RED tests | Chain step 2. Keep. |
| tdd-engineer | workflow | 86 | — | all | RED/GREEN/REFACTOR w/ three-fix architecture stop | Chain step 3. Keep. |
| subagent-dispatcher | workflow | 42 | — | all | Parallel/sequential delegation w/ fresh-context isolation | Chain step 4. Keep. |
| verification-gate | workflow | 85 | — | all | Fresh-evidence completion gate | Chain step 5. Keep. |
| branch-finisher | workflow | 104 | — | all | Tests-pass merge gate + plan archival | Chain step 6. Keep. |
| root-cause-analyst | workflow | 71 | — | all | Diagnose before patching (three-fix escape hatch) | Escape hatch. Keep. |
| paranoid-reviewer | expert | 32 | — | `*` | Deep static analysis + doctrine review | Supersedes legacy code-review/quality-gate. Keep (canonical reviewer). |
| context-engineer | workflow | 68 | — | all | Compact broad tasks into minimal truth-preserving artifacts | Distinct from evidence-packager (compaction vs sourcing). Keep. |
| evidence-packager | workflow | 59 | — | all | Convert research into a sourced evidence pack | Distinct from context-engineer. Keep. |
| multi-agent-governor | workflow | 60 | — | `*` | Audit repo for SOTA multi-agent governance readiness | Keep. |
| portability-auditor | workflow | 46 | — | `*` | Suitcase-doctrine portability audit (cmd alias `portability-audit`) | Keep. Name==folder; alias is renderer metadata. |
| skill-author | workflow | 92 | — | all | Author/revise a skill w/ canonical frontmatter | Meta-skill. Keep. |
| onboarding-guide | workflow | 360 | onboard.py, EXPLAINERS.md | all | Inline 8-beat first-operator tour | Demo entry point. Keep. |
| project-bootstrap | workflow | 38 | — | `*` | Bootstrap a governed project | Keep. |
| company-onboarder | workflow | 57 | scripts/ | all | Company onboarding (cmd `init-company`) | Keep. |
| memory-archivist | workflow | 83 | archivist.py | all | Append-only MEMORY.md edits | Keep. State layer. |
| memory-bridge | workflow | 48 | bridge.py | all | Sync MEMORY.md to host-local sidecars | Keep. State layer. |
| lesson-distiller | workflow | 103 | distiller.py | all | Archive promoted lessons (bounded decay) | Keep. Paired w/ sprint-harvester. |
| sprint-harvester | workflow | 56 | — | all | Append normalized end-of-sprint lessons | Keep. |
| handoff-archiver | workflow | 71 | archiver.py | all | Compact old HANDOFF sprints to archive | Keep. |
| telemetry-guardian | expert | 64 | guardian.py, guardian.sh | all | Universal pre-tool destructive-command veto (Python-first) | Keep. Hook target. |
| prompt-auto-activator | workflow | 46 | auto-activator.py/.sh | claude, codex | Route opt-in phrases to skills via prompt hook | Keep. |
| live-hook-prober | workflow | 102 | prober.py, prober.sh | all | Probe live hook wiring | Keep. |
| token-optimizer | workflow | 56 | — | all | Caveman/terse token-frugal output discipline | Keep. |
| brand-guardian | expert | 23 | — | all | Enforce DESIGN.md visual identity | Keep (domain expert). |
| corporate-controller | expert | 23 | — | all | Accounting/tax/bookkeeping guidance | Keep (domain expert). |
| legal-counsel | expert | 26 | — | all | Draft instruments / review contracts (IRAC) | Keep (domain expert). |
| infra-architect | expert | 22 | — | all | Infra/Docker/hardware TCO audit | Keep (domain expert). |
| e2e-qa-tester | expert | 19 | — | `*` | End-to-end QA testing | Keep. Was missing from README (now added). |

## Notes

- **Domain-expert skills** (brand-guardian, corporate-controller, legal-counsel,
  infra-architect) are intentionally small and single-purpose; they are not
  workflow-chain members and have no overlap with each other.
- **No `metadata.agent_forge.*` migration this pass** — local-extension
  frontmatter stays top-level; tracked in `docs/TECH_DEBT.md`.
- The naming-vs-doctrine references resolved: `portability-audit` (command alias)
  vs `portability-auditor` (folder/name) is intentional renderer metadata, not a
  violation; `paranoid-reviewer` is the single canonical reviewer.
