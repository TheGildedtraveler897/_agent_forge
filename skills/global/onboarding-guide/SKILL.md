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

**Paced, interactive walkthrough.** The tour reveals one beat at a time and asks `[Enter]` between beats. It does not dump multiple sections in one go. This is intentional — the design rule is *one screen, one beat, one question or pause.*

Eight beats:

| # | Beat | What happens |
|---|---|---|
| 0 | Greet + experience prompt | One-screen intro; `prompt_choice` asks experience (yes-many / one / none / check-for-me). |
| 1 | Role prompt | `prompt_choice` asks role (curious / builder / operator / decider). |
| 2 | What is this folder? | One short paragraph naming the factory, plus the live skill count as proof. |
| 3 | Meet the Crew | Dynamic breakdown of installed host CLIs tailored to the user's role (Beginner vs Senior). |
| 4 | The Architecture | Hub and Spoke ASCII diagram explaining Agents vs. Subagents, populated with local skills. |
| 5 | The translation table | First a one-screen tease, then the cross-host translation table renders. |
| 6 | The Danger Zone | Seatbelt rules (`telemetry-guardian`) and File Collision warnings. |
| 7 | Sandbox Quest | Interactive handoff providing a harmless, copy-pasteable command to test the CLI. |

Each beat is small (about 10 lines of print before a pause or question). No beat dumps a wall of text; if a beat grows, split it.

Flags:

- `--quick` — skip the paced beats and print a 90-second non-interactive summary (bullets + probe verdicts + first red fix command). Used when an operator wants the gist.
- `--no-pause` — run the full paced tour without waiting for `[Enter]`. Used by smoke tests and CI; not recommended for first-time operators.

The audit log (`<project>/.forge_state/onboarding.log`, when a governed project is present) records the operator's chosen experience level, chosen role, and how many beats they completed.

### `check`

Non-interactive machine-state report. Same diagnostics as the tour but no questions, no narration, just the verdicts. Useful for re-running after fixes.

Output: structured one-screen report with one of three colors per check (green / yellow / red), a one-line plain-English explanation, and the exact command to fix anything red.

### `explain <topic>`

Single-concept explainer. Topics:

- **Tier-0 host CLIs:** `claude-cli`, `codex-cli`, `gemini-cli` — each names the vendor, the boot-file convention, the memory story (native vs sidecar), and ends with "When to pick this host."
- **Core primitives:** `factory`, `skill`, `agent`, `agent-team`, `hook`, `mcp`, `memory`, `sandbox`, `guardian`.
- **Cross-host plumbing:** `host-dirs` (the four `.claude/` / `.codex/` / `.agents/` / `.gemini/` directories and why they exist).
- **Validation:** `triad-validator`, `validation-pyramid`.
- **Lifecycle:** `bootstrap`, `governed-project`, `suitcase`.

Each prints a 100–200 word plain-English explanation with one concrete example from the operator's actual repo state.

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

- **New beat.** Each beat lives inline in `cmd_tour` as a clearly commented block ending in `pause(no_pause=no_pause)` or a `prompt_choice` call. Keep each beat under ~12 lines of `print()` before the pause. If a beat grows past that, split into two beats with their own pauses.
- **New `explain` topic.** Add an entry to the `EXPLAINERS` dict in `onboard.py`. Place new entries alphabetically by key. One ~100–200 word string. Reference a specific file in the operator's repo state if possible. If the topic is a host-CLI variant, end with "When to pick this host: ..." so a new operator can choose.
- **New diagnostic probe.** Add a function to the `PROBES` list. Each probe returns `(verdict, summary, fix_command)`. Verdicts are `"green"`, `"yellow"`, `"red"`.
- **New host.** If a fourth host CLI is added in the future: add a row to the table inside `_print_translation_table` and a column to the `CLI_INFO` dict so the install gate covers it. Add a tier-0 explainer (`<host>-cli`). Add a corresponding column to the `_EVENT_ALIASES` map in `scripts/omni_factory.py`. The triad runtime validator extension is out of scope for this skill but tracked in `docs/HOST_INTEGRATIONS.md`.

### Helpers available for new beats

- `pause(prompt, no_pause)` — wait for `[Enter]`. Non-TTY safe (returns immediately when stdin is piped); `--no-pause` flag also bypasses.
- `prompt_choice(question, options, default)` — numbered choice prompt. Options is a list of `(key, label, description)` tuples. Returns the chosen key. Invalid input returns the default.
- `ask_yn(question, default)` — yes/no prompt. Default is bool; returns bool.
- `_detect_cli_state()` — returns `(present, missing)` for the three host CLIs.
- `_count_skills()` — reads `registry.json` and returns the skill count for live-proof lines.
- `_print_translation_table()` — renders the cross-host name table with aligned columns.
- `install_gate(no_pause)` — the per-CLI install hand-holding flow.

### Acceptance criteria for maintainers

- The tour reads naturally aloud at a normal pace in under 10 minutes including pauses. If a contributor adds a beat that pushes total length past that, split into two skills or move content into an `explain` topic.
- Every agentic term used in the tour appears either in `EXPLAINERS` or in the on-screen jargon-translation aside. If a new term shows up untranslated, that is a regression.
- Cross-host names (PreToolUse / BeforeTool, MCP config file types, etc.) in `_print_translation_table` must match the canonical → native mapping in `scripts/omni_factory.py:_EVENT_ALIASES` and in `docs/HOST_INTEGRATIONS.md`. If the table drifts from the code, the code is right and the table needs updating.
- No beat may exceed ~12 lines of `print()` output before a `pause` or `prompt_choice` call. Walls of text are the failure mode this design exists to prevent.
- ASCII diagrams must remain aligned and readable on standard terminal widths (80 columns). Do not use characters that fail to render on basic UTF-8 terminals.

When extending, re-read the **Tone discipline** section above first. Tone drift is the most common way this skill degrades in maintenance.

## Why this skill exists

Before this skill, a first-time operator who finished `bootstrap-project.sh` saw a wall of `[OK]` lines from `verify-agent-forge.py` and a triad-validator JSON dump and was expected to know what to do with that. Most won't. The factory's strength — canonical-first, three host CLIs, runtime validation gate — is invisible to a fresh operator until someone walks them through it. This skill is that walkthrough, automated, and consistent across all three host CLIs because it is itself just a skill the factory ships.
