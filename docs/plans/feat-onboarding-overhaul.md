---
plan_id: feat-onboarding-overhaul
branch: feat/onboarding-overhaul
status: approved
created: 2026-05-22T16:30:00Z
last_updated: 2026-05-22T16:30:00Z
spec_ref: null
task_count: 8
execution_mode: sequential
approved_at: 2026-05-22T16:30:00Z
approved_by: operator
ship_target: NRC clean-slate bundle, Monday 2026-05-25
title: Onboarding Guide Overhaul (Track H)
parent_plan: ~/.claude/plans/yeah-do-the-final-dapper-creek.md
---

# Plan: Onboarding Guide Overhaul (Track H)

This plan is the Track H extract from the parent sprint plan at `~/.claude/plans/yeah-do-the-final-dapper-creek.md`. Status starts at `approved` because the parent plan was approved by the operator and this is one of its scheduled sub-tracks.

## Context

The `onboarding-guide` skill is the demo entry point for the NRC ship. Five concrete gaps in the current implementation limit its usefulness to the dual audience (senior engineer + curious high-school student):

1. No tier-0 "what is each host CLI" explanation.
2. "Agent" and "agent team" are never translated.
3. No cross-host translation table.
4. No audience-aware routing.
5. Cross-host config directory naming not surfaced.

Also: the bundle delivered to NRC lacks a root-level README a coworker can read on first unzip.

## Tasks

### H-1. Tier-0 host CLI explainers
Add `claude-cli`, `codex-cli`, `gemini-cli` to EXPLAINERS in `skills/global/onboarding-guide/onboard.py`. Each 100–150 words, plain English, ending with "When to pick this host: ..."

### H-2. Translate "agent" and "agent team"
Add `agent` and `agent-team` explainers. Update tour section 2 to name `teams/` and link to the new explainer.

### H-3. Cross-host translation table (new tour section)
Insert a new tour section that renders a compact ASCII table mapping every key concept across Claude / Codex / Gemini. Two-sentence framing underneath: three vendors, similar primitives, different names; the factory translates.

### H-4. Audience-aware routing (linear tour, role-tuned paragraphs)
Add a role prompt after the experience-level prompt: curious / builder / operator / decider. Append one role-tuned paragraph per existing tour section. No new sections; tour length stays within 15%.

### H-5. Surface cross-host config dir naming
Add a `host-dirs` explainer. Add a paragraph in tour section 2 explaining the four directory names (`.claude/`, `.codex/`, `.agents/`, `.gemini/`).

### H-6. Tone pass + length budget
Read the full tour with two rubrics: senior-engineer accuracy + high-school approachability. Trim explainers >200 words. Cut sentences that exist only to soothe. Verify `wc -l onboard.py` stays within ~15% of pre-overhaul (~800 → ~920 ceiling).

### H-7. Update SKILL.md + maintainer acceptance criteria
Document new explainers, new tour section, role-routing flag. Add explicit acceptance criteria for future maintainers.

### H-8. Bundle-root README
New `BUNDLE_README.md` at repo root. One page, plain English, names the first command a coworker should run. Update `factory-export.sh` to include it in the bundle and have `START_HERE.txt` point to it.

## Verification

- `python3 scripts/verify-agent-forge.py` exits 0 on `feat/onboarding-overhaul`.
- `python3 skills/global/onboarding-guide/onboard.py tour` runs end-to-end (manual smoke).
- Each new explainer returns coherent 100–200 word output on `onboard.py explain <topic>`.
- `wc -l onboard.py` ≤ 920.
- Operator read-through against the two rubrics is the qualitative gate.

## Acceptance

- [ ] H-1 three host CLI explainers added
- [ ] H-2 agent + agent-team explainers added, tour section 2 updated
- [ ] H-3 translation table renders as a new tour section
- [ ] H-4 role prompt + role-tuned paragraphs in each section
- [ ] H-5 host-dirs explainer + tour paragraph
- [ ] H-6 tone pass complete, length budget met
- [ ] H-7 SKILL.md updated with maintainer criteria
- [ ] H-8 BUNDLE_README.md present in repo root and in factory-export bundle
