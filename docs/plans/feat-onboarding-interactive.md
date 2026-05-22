---
plan_id: feat-onboarding-interactive
branch: feat/onboarding-interactive
status: completed
created: 2026-05-22T18:00:00Z
last_updated: 2026-05-22T18:30:00Z
spec_ref: null
task_count: 5
execution_mode: sequential
approved_at: 2026-05-22T18:00:00Z
approved_by: operator
ship_target: NRC clean-slate bundle, Monday 2026-05-25
title: Onboarding redesign — paced, interactive, install-aware
parent_plan: ~/.claude/plans/yeah-do-the-final-dapper-creek.md
---

# Plan: Onboarding redesign (Track J)

## Why

Track H made the onboarding-guide more thorough. It did not make it fun. The script's tour dumps six sections in one go, doesn't pause for the reader, and doesn't walk a fresh operator through installing the three host CLIs — it just detects whether they're on PATH and says "run bootstrap-workstation.sh." That's a "monkey behind the curtain" moment leaking into the front door.

The fix is a paced, conversational flow with built-in install hand-holding.

## What changes

Rewrite `cmd_tour` and the section functions in `skills/global/onboarding-guide/onboard.py` so the tour:

1. **Paces itself** — one screen at a time, `Press [Enter] to continue` between beats.
2. **Asks questions** that the rest of the tour reacts to (experience, role, install state, deeper-dive offers).
3. **Walks through install hand-holding** for any missing host CLIs. Per-CLI: 2-line "what is it / why pick it," install command, the offer to invoke `bootstrap-workstation.sh`.
4. **Earns the translation table** — leads up to it with "different vendors call this different things" before showing the grid.
5. **Closes with one concrete next action** tuned to the chosen role.

Preserve:
- The existing EXPLAINERS dict (used by `explain` mode).
- The existing six probes (used by `check` mode).
- `cmd_check` and `cmd_explain` (unchanged).
- The tone discipline from SKILL.md (no sycophancy, no condescension, no untranslated jargon).
- The audit log writing.

## Tasks

### J-1. Add interactive helpers
- `pause(prompt: str = "Press [Enter] to continue")` — waits for Enter; non-TTY returns immediately so the smoke tests work.
- `prompt_choice(question: str, options: list[tuple[str, str]], default: str) -> str` — numbered choice prompt, returns the chosen key.
- `ask_yn(question: str, default: bool = True) -> bool` — yes/no.

### J-2. Rewrite tour as paced beats
Eight beats, each ending in a `pause()` or a question:
- Beat 0 — Greet, ask experience.
- Beat 1 — Ask role.
- Beat 2 — "What is this folder?" (one paragraph + live skill count).
- Beat 3 — "Three names for the same thing" (tease) → translation table on Enter.
- Beat 4 — "The seatbelt" (one paragraph + offer to print deny list).
- Beat 5 — "The shared brain" (one paragraph + offer to show live MEMORY.md if any project has one).
- Beat 6 — Install gate: detect missing host CLIs, walk through per-CLI install offers.
- Beat 7 — Role-tuned next action; goodbye.

### J-3. Per-CLI install hand-holding
- For each missing host CLI, print: 2-line description, install URL, exact `bootstrap-workstation.sh` invocation. If the operator chooses "walk me through it," offer to run `bootstrap-workstation.sh` after a final confirmation; otherwise print the command and continue.
- For any host CLI that's already on PATH, say so in one line and skip.

### J-4. Smoke test the new flow
- Non-interactive (piped) full run: must complete without hanging on `input()` calls.
- Interactive mental walkthrough against the two rubrics from SKILL.md (senior engineer + curious high-school student).
- `python3 scripts/verify-agent-forge.py` exits 0.

### J-5. Update SKILL.md to document the new pacing
- Tour mode description: 8 beats, paced, install-aware.
- Document `pause()` / `prompt_choice()` / `ask_yn()` for future extenders.
- Note: `--no-pause` flag for CI / smoke tests.

## Acceptance

- [x] J-1 helpers added (`pause`, `prompt_choice`, `ask_yn`); all non-TTY safe.
- [x] J-2 tour rewritten as 7 paced beats; no beat exceeds ~12 lines before a pause/question.
- [x] J-3 install gate runs per missing CLI; offers `bootstrap-workstation.sh` as one-shot path.
- [x] J-4 smoke tests pass: tour --no-pause runs clean, --quick prints summary, explain/check unchanged, verify-agent-forge.py exits 0/0/0.
- [x] J-5 SKILL.md documents the 7 beats, helpers available for new beats, and the no-walls-of-text acceptance criterion.
