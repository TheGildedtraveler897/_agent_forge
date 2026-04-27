---
name: onboarding-guide
description: Walk a first-time operator through what the Agent Forge factory is, what just got generated on their machine, what the green or red lights mean, and what to do next. Plain-English explanations of the agentic vocabulary (MCP, hooks, sandboxing, memory) translated as they appear. Three modes — guided tour, non-interactive state check, and single-topic explainer. Use right after `bootstrap-project.sh` or any time a new operator opens the repo cold.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Onboarding Guide

A walkthrough for someone meeting the factory for the first time. Aimed at three readers in one document: a smart operator new to coding-agent CLIs, a technical operator who knows git/bash but not agentic vocabulary, and a senior architect skimming for component map and gates.

## Mission

Translate the factory from "a folder with a lot of files" into "I see what each piece does and what to do next" — without sycophancy, without condescension, without jargon that hasn't been translated first.

## Tone discipline (read before extending this skill)

- **No sycophancy.** No "Great question!", no "You're doing amazing!". The operator's time is the scarce resource; respect it.
- **No condescension.** No "Don't worry if this is hard". Just explain it.
- **No jargon without translation.** First mention of every agentic-vocabulary term gets a one-sentence plain-English rewrite in parentheses. Examples:
  - MCP (the open standard for letting an AI agent talk to external tools)
  - hook (a script that runs before or after an AI tool call, allowing or blocking it)
  - sandbox (a restricted environment that limits what a process can read or write)
  - memory layer (one shared file every AI tool reads from and writes to)
- **Ask, don't assume.** When the operator's experience level is unclear, ask one short question and adapt. Do not lecture them through context they already have.
- **Show, don't tell.** Run the actual commands. Show the actual output. Translate it. "Here's what we just verified: [output]. In plain terms: [translation]."

## Modes

The skill ships an executable Python helper at `onboard.py` next to this file. Invoke with `python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py <mode>`.

### `tour` (default)

Interactive guided walkthrough. Five sections; each follows the same shape:

1. **What it is** — one paragraph, plain English, jargon translated.
2. **Why it exists** — one short paragraph naming the problem solved.
3. **Live proof** — runs a command, shows the output, translates it.
4. **What to do next** — explicit next command or "no action needed; this part is healthy".

The five sections:

| # | Section | Concept introduced |
|---|---|---|
| 1 | What is this folder? | The factory and its three host CLIs (Claude / Codex / Gemini). |
| 2 | Three tools, one source of truth | The canonical-first → render-outward model. |
| 3 | The seatbelt | `telemetry-guardian` and the deny list. |
| 4 | The shared brain | `MEMORY.md` cross-host state layer. |
| 5 | What to do next | State-aware: diagnostic if broken, ready-task if green. |

The tour adapts to the operator's reported experience. The first prompt asks one short question: have you used the three host CLIs before, yes / partially / no. The answer changes how much vocabulary translation is inserted into Sections 1–4.

### `check`

Non-interactive machine-state report. Same diagnostics as the tour but no questions, no narration, just the verdicts. Useful for re-running after fixes.

Output: structured one-screen report with one of three colors per check (green / yellow / red), a one-line plain-English explanation, and the exact command to fix anything red.

### `explain <topic>`

Single-concept explainer. Topics: `mcp`, `hook`, `memory`, `sandbox`, `triad-validator`, `guardian`, `factory`, `skill`, `bootstrap`. Each prints a 100–200 word plain-English explanation with one concrete example from the operator's actual repo state.

## Discipline / what this skill does NOT do

The skill is read-only and observational. By design, it does not:

- Modify `MEMORY.md`, `LESSONS_LEARNED.md`, or any canonical source.
- Auto-fix detected problems. It reports the diagnosis and recommends the fix command; the operator runs it.
- Invoke long-running CLI calls (`claude -p` / `codex exec` / `gemini -p`) from within the tour. Per the 2026-04-26 leftover-subprocess-tree lesson, those run from a real terminal only. The tour describes what `validate-triad-runtime.py --probe-invocations` does and points the operator to run it; the tour does not run it itself.
- Modify `bootstrap-project.sh`. The integration hook (calling this skill at end of bootstrap) is documented in `docs/HANDOFF.md` as a future Codex enhancement, not done here.
- Write to `MEMORY.md`. The tour is read-only of canonical state.

The only file the skill writes is its own audit log at `<project>/.forge_state/onboarding.log` — one append-only line per tour run with timestamp + completion-status + sections reached. No PII; no command output captured; no operator answers persisted.

## State-detection contract

The tour and `check` mode both run the same six probes:

1. Is `_agent_forge` deployed at `~/Projects/_agent_forge` with the canonical files (`AGENTS.md`, `policies/hooks.json`, `policies/memory.json`, `registry.json`)?
2. Is `verify-agent-forge.py` exit 0?
3. Are the three host CLIs (`claude`, `codex`, `gemini`) on `PATH`?
4. Is at least one governed project from `projects.json` actually present on disk?
5. Is `validate-triad-runtime.py --project <first-governed>` exit 0 (surface check only; no `--probe-invocations`)?
6. Are user-home host directories (`~/.claude`, `~/.agents`, `~/.gemini`) populated?

Each probe gets a green / yellow / red verdict and, on red, a one-line plain-English diagnosis plus the exact command to fix it. No "see docs/X" rabbit holes.

## Output contract

stdout: the tour itself (or the `check` report, or the `explain` body). Always plain text — no ANSI colors that don't render in some terminals; uses ASCII glyphs `[OK]` / `[WARN]` / `[FAIL]` for verdicts. (If terminal supports color, the helper may add it, but content is readable without.)

stderr: human-readable trace of what the helper is reading from disk. Useful for debugging the helper itself; the operator usually never reads stderr.

Exit codes:
- `tour` and `explain`: always 0 (informational; not a gate).
- `check`: 0 if all six probes green or yellow; 1 if any probe red.

## When to extend

- **New section.** Each section is a function in `onboard.py` named `section_<n>_<topic>`. Add a new function and add it to the `TOUR_SECTIONS` list. Keep it under ~80 lines including translations.
- **New `explain` topic.** Add an entry to the `EXPLAINERS` dict in `onboard.py`. One ~150-word string. Reference a specific file in the operator's repo state if possible.
- **New diagnostic probe.** Add a function to the `PROBES` list. Each probe returns `(verdict, summary, fix_command)`. Verdicts are `"green"`, `"yellow"`, `"red"`.

When extending, re-read the **Tone discipline** section above first. Tone drift is the most common way this skill degrades in maintenance.

## Why this skill exists

Before this skill, a first-time operator who finished `bootstrap-project.sh` saw a wall of `[OK]` lines from `verify-agent-forge.py` and a triad-validator JSON dump and was expected to know what to do with that. Most won't. The factory's strength — canonical-first, three host CLIs, runtime validation gate — is invisible to a fresh operator until someone walks them through it. This skill is that walkthrough, automated, and consistent across all three host CLIs because it is itself just a skill the factory ships.
