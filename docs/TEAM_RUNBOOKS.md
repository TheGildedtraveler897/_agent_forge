# Team Runbooks

This file explains how to use the starter teams in practice without needing a heavy orchestration engine.

## Governance Team

Use this team when:
- a repo may have governance drift
- a new project was just bootstrapped
- a repo was moved, copied, or restructured
- you want an audit-first pass before deeper implementation work

### Claude pattern

Use:
- `/multi-agent-governor` as the main entry
- `/portability-audit` for suitcase-doctrine and agent-agnostic path review
- `/doctrine-review` for hidden-risk and over-engineering checks
- `docs/TRIAD_RUNTIME_VALIDATION.md` when the goal is a full workspace validation or remediation run

Recommended flow:
1. Run `/multi-agent-governor` for a top-level audit.
2. If findings are broad or mixed, run `/portability-audit` and `/doctrine-review` in parallel to split the work.
3. Consolidate into one remediation checklist.

### Codex pattern

Use:
- `multi-agent-governor` skill as the main audit skill
- `portability-auditor` skill for portability-specific depth
- delegated runtime agents only if separate contexts are materially useful

Recommended flow:
1. Run a governance audit.
2. If needed, split portability review into a separate delegated pass.
3. Produce one remediation checklist and stop.

### Stop condition

Stop when:
- blockers and warnings are categorized
- exact remediation actions are listed
- no further mutation is required without explicit approval

## Bootstrap Team

Use this team when:
- creating a governed project
- standardizing an older repo

Primary entry:
- `project-bootstrap`

## Delivery Team

Use this team for actual repo work when planning, building, and review should stay separate.

Primary pattern:
- planner
- builder
- reviewer

## Research Team

Use this team when:
- the task needs web or source research before implementation
- the material is broad, conflicting, or expensive to keep in raw form
- a downstream planner needs a compact evidence artifact

Collapse to single worker when: the question has 1-2 known sources with no conflicts.

### Claude pattern

Use:
- `/evidence-packager` as the main entry for compact output
- `/context-engineer` to compress findings into a brief if the evidence pack is still too large
- Explore Agents for parallel source gathering when sources span different domains

Recommended flow:
1. Define the research question explicitly.
2. Gather sources (web search, repo exploration, doc reads).
3. Triage into confirmed/conflicting/uncertain.
4. Package into an evidence pack using the template from OPERATOR_TEMPLATES.md.

### Codex pattern

Use:
- `evidence-packager` skill for output format
- `context-engineer` skill for compaction
- delegated runtime agents when source volume is high and parallel gathering helps

### Stop condition

Stop when:
- an evidence pack artifact exists
- a planner can work from it without re-reading the sources
- unresolved questions are explicitly listed

## Planning Team

Use this team when:
- the task is still underspecified after research
- implementation needs a decision-complete brief
- you want a cheaper model to execute later from a stronger plan

Collapse to single worker when: requirements are already clear and scope is small.

### Claude pattern

Use:
- `/context-engineer` to produce the brief
- `/quality-gate` to verify the brief is decision-complete before handing off
- Plan mode for structured plan development

Recommended flow:
1. Read the evidence pack (if research team ran first) and repo truth docs.
2. Clarify goal, constraints, and acceptance criteria.
3. Write an implementation brief using the template from OPERATOR_TEMPLATES.md.
4. Run quality-gate on the brief — fix any blockers before handoff.

### Codex pattern

Use:
- `context-engineer` and `quality-gate` skills
- delegated agents when plan needs architectural input from different domain experts

### Stop condition

Stop when:
- an implementation brief exists with no blocker-level quality-gate findings
- a builder can execute without making major architectural decisions
- acceptance criteria are testable

## Assessment Team

Use this team when:
- work is complete but quality is uncertain
- you need explicit findings and regression checks
- a release, merge, or handoff needs objective evidence

Collapse to single worker when: the change is small with binary acceptance criteria.

### Claude pattern

Use:
- `/quality-gate` as the primary scoring tool
- `/doctrine-review` for doctrine alignment checks
- Agents when the review surface should stay separate from the build context

Recommended flow:
1. Compare outcome against stated goal and acceptance criteria.
2. Check for regressions, doctrine violations, and verification gaps.
3. Produce a scorecard with severity-tagged findings (blocker/warning/note).
4. State explicit recommendation: keep, revise, or reject.

### Codex pattern

Use:
- `quality-gate` and `code-review-doctrine` skills
- delegated reviewers when the build and review contexts should not overlap

### Stop condition

Stop when:
- a scorecard exists
- the next action (keep/revise/reject) is unambiguous
- no major finding is left uncategorized

## Improvement Team

Use this team when:
- findings exist and need prioritization
- a process, skill, or team should be tightened after a run
- docs, doctrine, or prompts need to evolve from real evidence

Collapse to single worker when: findings are few and the fix is obvious.

### Claude pattern

Use:
- `/quality-gate` to score current state
- `/context-engineer` to compact improvement plan into a handoff
- `/sprint-harvester` to capture durable lessons before they are promoted into doctrine
- Edit tools directly for doc/skill/manifest updates

Recommended flow:
1. Rank findings by leverage and repeatability.
2. Design the smallest remediation set that addresses the highest-leverage gaps.
3. Apply improvements to skills, teams, or docs.
4. Harvest durable lessons into `docs/LESSONS_LEARNED.md`.
5. Re-run quality-gate to verify improvements didn't introduce new issues.
6. Update HANDOFF.md.

### Codex pattern

Use:
- `quality-gate` and `context-engineer` skills
- delegated agents when improvement surfaces are disjoint (e.g., docs vs scripts)

### Stop condition

Stop when:
- improvements are applied and verified
- doctrine/doc update checklist is complete
- the next run will benefit from the changes without re-deriving them
