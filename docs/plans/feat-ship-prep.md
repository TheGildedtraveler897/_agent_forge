---
plan_id: feat-ship-prep
branch: feat/ship-prep
status: awaiting-approval
created: 2026-05-22T15:30:00Z
last_updated: 2026-05-22T15:30:00Z
spec_ref: null
task_count: 8
execution_mode: sequential
approved_at: null
approved_by: null
ship_target: NRC clean-slate bundle, Monday 2026-05-25
title: Plan Persistence Layer for Agent Forge
---

# Plan: Plan Persistence Layer for Agent Forge

> **Meta-note:** This file IS the first persisted plan. It demonstrates the pattern we're formalizing. If your Claude session glitches before approval, this file survives — any Codex or Gemini agent can read it and pick up where we left off.

## Problem Statement

`execution-planner` currently produces detailed task breakdowns that exist only in the active agent's context window. When the session glitches, hits context overflow, or swaps models, the plan vanishes. Even when working, plans are invisible to peer agents on other hosts (Codex / Gemini). This breaks Agent Forge's core multi-agent continuity promise.

Today's failure: a plan was generated and presented for review. While the operator was reading it, the session glitched. The plan was lost. All upstream iteration context (spec discovery, design tradeoffs, the iteration that produced that final draft) was lost with it.

## Design Principle

Plan persistence is a **project-governance concern**, not a host-rendered primitive. Hosts (Claude, Codex, Gemini) don't have native "plan" formats — only skills (execution-planner, tdd-engineer, branch-finisher) read plan files. So we **skip the omni-factory 5-step pattern** (policy + renderers + verifier + validator + skill). Instead, we treat plans like `LESSONS_LEARNED.md` and `HANDOFF.md`: a project-level Markdown file with frontmatter conventions enforced by the relevant skills and surfaced in AGENTS.md doctrine.

This avoids over-engineering. No new JSON schema. No new renderer. No new validator extension. Just convention + skill integration.

## Three-Tier State Model

### Tier 1 — Active Plan File (`docs/plans/<branch-slug>.md`)
- Full task breakdown with frontmatter
- One file per branch; overwrites on re-plan
- Branch name slugified (`feat/ship-prep` → `feat-ship-prep`)
- Status field tracks workflow position
- Committed with the branch (versioned with the work)

### Tier 2 — MEMORY.md Pointer (lightweight, auto-loaded)
- One-line entry in `active_tasks` section
- Format: `- Plan: docs/plans/<slug>.md — <one-line summary> (status: <status>, tasks: <count>)`
- All three hosts auto-load this on session start (via memory bridge)
- Full plan never auto-loaded — only the pointer

### Tier 3 — Continuity Cursor (existing, hooks in on approval)
- `dev/active/<slug>/cursor.json` + `tasks.md`
- Managed by `scripts/continuity_cursor.py` (already exists)
- Only created when status transitions to `approved`
- Tracks per-task position (which task is in-flight)

## Plan File Format

```markdown
---
plan_id: <branch-slug>
branch: <git branch name>
status: awaiting-approval | approved | in-progress | superseded | completed
created: <ISO timestamp>
last_updated: <ISO timestamp>
spec_ref: docs/specs/YYYY-MM-DD-<slug>.md  # null if no upstream spec
task_count: <int>
execution_mode: sequential | parallel
approved_at: <ISO timestamp or null>
approved_by: <user identifier or null>
title: <one-line plan title>
---

# Plan: <Title>

[Standard execution-planner output: T-01, T-02, ... with files, RED tests, GREEN steps, verification]
```

## Status Lifecycle

```
awaiting-approval  →  approved  →  in-progress  →  completed
                  ↓
              superseded (rejected or re-planned)
```

Transitions:
- **awaiting-approval → approved**: Operator approval (manual or via execution-planner Phase 6c)
- **approved → in-progress**: First task started by tdd-engineer or subagent-dispatcher
- **in-progress → completed**: branch-finisher marks on successful merge
- **any → superseded**: Re-planning the same branch, or explicit rejection

## Token-Awareness Strategy

- Plan files are **NOT** auto-loaded by any host
- Only the MEMORY.md pointer (~100 bytes) loads on session start
- Agents read full plan ON DEMAND when executing or handing off
- This keeps the working context lean while the durable artifact is reachable

## Cleanup Policy (No File Bloat)

- One plan per branch maximum
- Plan overwrites on re-plan (no `.history/` directory)
- On branch merge: plan archived to `docs/archive/PLANS_COMPLETED.md` (with one-line summary), then deleted from `docs/plans/`
- Stale plans (branch deleted but file orphaned) flagged by `verify-agent-forge.py --warn-stale-plans`

## Implementation Tasks

### T-01 — Create `docs/plans/` directory with seed
**Files:** `docs/plans/.gitkeep`

**Goal:** Ensure plan directory exists in fresh installs.

**Steps:**
1. Create directory: `mkdir -p docs/plans`
2. Create `docs/plans/.gitkeep` (empty file)
3. Commit

**Verification:** `test -d docs/plans && test -f docs/plans/.gitkeep`

---

### T-02 — Update `execution-planner` SKILL.md for awaiting-approval persistence
**Files:** `skills/global/execution-planner/SKILL.md`

**Goal:** Phase 5 writes plan to disk BEFORE approval with `status: awaiting-approval`. Phase 6 handles status transitions on approval/rejection.

**Changes:**
1. Insert new Hard Gate after current gate 7 (branch preflight):
   ```
   9. **Persisted plan artifact.** The plan must be written to `docs/plans/<branch-slug>.md` with frontmatter `status: awaiting-approval` BEFORE presenting it for review. This guarantees the plan survives session glitches and is discoverable by peer agents on other hosts.
   ```

2. Replace Phase 5 contents with:
   ```
   ### Phase 5 — Write the plan with awaiting-approval status

   - Slugify the current git branch (`git branch --show-current` → replace `/` with `-`).
   - Write to `docs/plans/<branch-slug>.md` with frontmatter:
     - `plan_id: <branch-slug>`
     - `branch: <full branch name>`
     - `status: awaiting-approval`
     - `created: <ISO 8601 UTC>`
     - `last_updated: <same as created>`
     - `spec_ref: <path to spec, or null>`
     - `task_count: <int>`
     - `execution_mode: sequential | parallel`
     - `approved_at: null`
     - `approved_by: null`
     - `title: <one-line title>`
   - If file already exists for this branch, snapshot the previous file's status. If it was `approved` or `in-progress`, halt and ask the operator before overwriting (existing work may be in-flight).
   - Append a one-line pointer to the project `MEMORY.md` `active_tasks` section via `memory-archivist`:
     ```
     - Plan: docs/plans/<branch-slug>.md — <one-line title> (status: awaiting-approval, tasks: <count>)
     ```
   - Commit the plan file with message: `Plan: <branch-slug> (awaiting approval)`
   ```

3. Replace Phase 6 contents with:
   ```
   ### Phase 6 — Human approval gate

   Present the plan file path (not the full plan body) for review:
     "Plan saved to docs/plans/<branch-slug>.md (status: awaiting-approval). Please review and approve."

   On approval:
   - Update plan frontmatter: `status: approved`, `last_updated: <now>`, `approved_at: <now>`, `approved_by: <operator identifier>`.
   - Update MEMORY.md pointer status field.
   - Initialize continuity cursor: `python3 scripts/continuity_cursor.py start --slug <branch-slug> --plan docs/plans/<branch-slug>.md --task T-01 --next-action "<short next action>"`
   - Commit: `Plan: <branch-slug> (approved)`
   - Name the next skill explicitly (`tdd-engineer` for sequential, `subagent-dispatcher` for parallel).

   On rejection:
   - Update plan frontmatter: `status: superseded`, `last_updated: <now>`.
   - Update MEMORY.md pointer accordingly.
   - Loop back to the failed phase. The superseded file remains on disk as iteration history until the next plan overwrites it.

   On revision request:
   - Treat as "loop back" — Phase 5 will overwrite with a new `awaiting-approval` plan once the revision is ready.
   ```

**Verification:** Read updated SKILL.md and confirm the new phases reference the file path and frontmatter format.

---

### T-03 — Update `branch-finisher` SKILL.md for plan archival on merge
**Files:** `skills/global/branch-finisher/SKILL.md`

**Goal:** When branch merges into master, archive plan file to `docs/archive/PLANS_COMPLETED.md` and delete from `docs/plans/`.

**Changes:**
1. Add to the merge gate:
   ```
   ## Plan Archival (Post-Merge)

   After successful merge into master/main:
   1. Check for `docs/plans/<branch-slug>.md`. If present:
      - Update frontmatter status: `completed`, `last_updated: <now>`.
      - Append a one-line summary to `docs/archive/PLANS_COMPLETED.md`:
        - Format: `- <YYYY-MM-DD> <branch-slug> — <title> (<task_count> tasks)`
        - Create the archive file with a header if it doesn't exist.
      - Delete `docs/plans/<branch-slug>.md`.
      - Remove the MEMORY.md pointer from `active_tasks`.
   2. Commit: `Plan archived: <branch-slug> (completed)`
   ```

**Verification:** Read updated SKILL.md and confirm archival step is present.

---

### T-04 — Update `AGENTS.md` with plan persistence rule
**Files:** `AGENTS.md`

**Goal:** Make plan persistence a top-level rule, update handoff rule to reference plan files.

**Changes:**
1. Add a new bullet under `## Rules`:
   ```
   - Plans authored by `execution-planner` persist to `docs/plans/<branch-slug>.md` with frontmatter status (`awaiting-approval`, `approved`, `in-progress`, `superseded`, `completed`). The plan is committed before the human approval gate so it survives session glitches. Peer agents on other hosts discover it via the MEMORY.md `active_tasks` pointer and read the file directly when they need execution detail.
   ```

2. Update the existing handoff rule:
   ```
   - Before any handoff, rate-limit stop, model swap, or end-of-day pause, commit the current branch state and push it upstream. The handoff must name the branch, latest commit, next task, the path to the active plan file (if `docs/plans/<branch-slug>.md` exists), and any dirty state that intentionally remains.
   ```

**Verification:** `grep -n "docs/plans" AGENTS.md` returns the new rule and the updated handoff line.

---

### T-05 — Update `docs/CONOPS.md` with plan persistence section
**Files:** `docs/CONOPS.md`

**Goal:** Document the plan persistence layer as a first-class architectural concept (analogous to "Knowledge Anchor" and "Universal State Layer").

**Changes:**
Add a new section before `## Bootstrap And Sync Flow`:

```
## Plan Persistence Layer

`execution-planner` writes its output to `docs/plans/<branch-slug>.md` with frontmatter that tracks plan status across the approval and execution lifecycle. This is the durable artifact that enables multi-agent plan continuity: a Claude session can produce a plan, glitch, and a peer Codex or Gemini agent can pick up from the on-disk file without losing the iteration context.

The layer is intentionally lightweight — no policy schema, no renderer pipeline, no validator extension. It's project-governance convention, not a host-rendered primitive. Hosts don't have native plan formats; only skills read plan files.

### Three-Tier State Model

- **Plan file** (`docs/plans/<branch-slug>.md`) — Full task breakdown with status frontmatter. Committed with the branch.
- **MEMORY.md pointer** — One-line entry in `active_tasks`, auto-loaded by all hosts on session start. ~100 bytes.
- **Continuity cursor** (`dev/active/<slug>/cursor.json`) — Per-task position state, managed by `continuity_cursor.py`. Created only when status transitions to `approved`.

### Status Lifecycle

```
awaiting-approval → approved → in-progress → completed
                  ↓
              superseded
```

### Cleanup

`branch-finisher` archives the plan file to `docs/archive/PLANS_COMPLETED.md` on merge and deletes the active file. One plan per branch; re-planning overwrites. No `.history/` directory — the git log is the history.

### Token Hygiene

Plan files are never auto-loaded. Only the MEMORY.md pointer loads on session start. Agents read the full plan on demand when executing or handing off.
```

**Verification:** Read updated CONOPS.md and confirm the new section is present.

---

### T-06 — Seed `docs/archive/PLANS_COMPLETED.md` stub
**Files:** `docs/archive/PLANS_COMPLETED.md`

**Goal:** Create the archive file with a header so `branch-finisher` has a target to append to.

**Content:**
```markdown
# Plans Completed

This file is the bounded-decay archive for plan files. When a branch merges via `branch-finisher`, the plan file in `docs/plans/<branch-slug>.md` is summarized here and removed from the active directory.

## Entries

_No plans archived yet._
```

**Verification:** `test -f docs/archive/PLANS_COMPLETED.md`

---

### T-07 — Add stale-plan warning to `verify-agent-forge.py`
**Files:** `scripts/verify-agent-forge.py`

**Goal:** Flag plan files whose corresponding branch no longer exists (orphans from abandoned work).

**Changes:**
1. Add new check function `_check_stale_plans()`:
   - Walk `docs/plans/*.md`
   - For each, extract `branch` from frontmatter
   - Check `git branch --list <branch>` (also check `git branch -r --list origin/<branch>`)
   - If neither exists, emit a warning (not a hard failure): `WARN: docs/plans/<file>.md references branch '<branch>' which no longer exists; consider archiving or deleting.`
2. Wire into the existing verification flow.

**Verification:** Run `python3 scripts/verify-agent-forge.py` after creating a plan file for a non-existent branch; confirm WARN appears.

---

### T-08 — End-to-end smoke test
**Files:** none (test workflow)

**Goal:** Validate the whole pipeline against a tiny test branch before relying on it for the NRC ship.

**Steps:**
1. On `feat/ship-prep`, run through execution-planner manually (or via skill invocation) for a trivial test plan.
2. Confirm plan file appears at `docs/plans/feat-ship-prep.md` with `status: awaiting-approval`.
3. Confirm MEMORY.md `active_tasks` has the pointer line.
4. Simulate approval: update frontmatter status to `approved`, init continuity cursor.
5. Simulate completion: have `branch-finisher` archive the plan.
6. Confirm `docs/archive/PLANS_COMPLETED.md` has the entry and `docs/plans/feat-ship-prep.md` is gone.

**Verification:** All assertions in steps 2-6 pass.

---

## Out of Scope (Explicit Non-Goals)

- **New policy schema** — No `policies/plans.json`. Plans aren't host-rendered.
- **Host-native plan rendering** — No Claude `.claude/plans/` directory, no Codex equivalent.
- **`spec-architect` parallel changes** — Similar pattern applies to specs in `docs/specs/`, but separate work. Note in lessons learned for future sprint.
- **Replacing `dev/active/<slug>/cursor.json`** — That stays for approved-plan per-task continuity. Plan file is upstream of it.
- **Cross-repo plan sync** — One-repo concern only.
- **Plan format standardization across orgs** — This is Agent Forge convention; other consumers can adopt or fork.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Plan files become outdated as work progresses | tdd-engineer updates status to `in-progress` on first task; branch-finisher updates to `completed` on merge |
| Plan files accumulate from abandoned branches | T-07 stale-plan warning + branch-finisher cleanup on merge |
| Two agents plan the same branch | Already prevented by AGENTS.md branch-discipline rule (separate branches per agent) |
| Frontmatter drift across plans (different formats over time) | T-02 hard-gate makes frontmatter format part of execution-planner's emission rules |
| Approval state lost between sessions | Status field in frontmatter is durable; MEMORY.md pointer reflects it; both committed |

## Integration with NRC Ship

This plan must merge into `feat/ship-prep` **before** the NRC bundle export, because:
1. Coworkers on Windows-native Claude Code will exercise execution-planner. If they hit a session glitch, the persistence layer prevents lost work.
2. The cross-agent continuity story is part of what we're shipping. Without persistent plans, the multi-agent narrative is incomplete.

Ship-prep finalization (Track F or G, TBD) will follow after this lands.

## Acceptance Criteria (For Operator Sign-Off)

- [ ] `docs/plans/<branch-slug>.md` is created BEFORE the human approval gate
- [ ] Plan file uses the specified frontmatter format
- [ ] Status transitions through the documented lifecycle
- [ ] MEMORY.md pointer is updated on each transition
- [ ] Plan files are archived (not deleted) on merge — wisdom preserved
- [ ] No new JSON policy schema introduced
- [ ] Existing `continuity_cursor.py` integration preserved
- [ ] AGENTS.md and CONOPS.md doctrine reflect the new layer
- [ ] Smoke test passes end-to-end

## Approval

When approved, update this file's frontmatter:
- `status: approved`
- `approved_at: <ISO timestamp>`
- `approved_by: <operator>`
- `last_updated: <ISO timestamp>`

Then execute tasks T-01 through T-08 in order.
