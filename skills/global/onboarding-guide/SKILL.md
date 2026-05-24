---
name: onboarding-guide
description: Walk a first-time operator through the Agent Forge factory inline in chat — what it is, what just got generated on their machine, what the green or red lights mean, what to do next. Seven paced beats with prompts between them. Plain-English explanations of agentic vocabulary as terms appear. Use when the user types `/onboarding-guide` in Claude Code, Codex, or Gemini.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Onboarding Guide

## Inline-Delivery Contract (read this first)

**When you (the assistant) are invoked as `/onboarding-guide` in a conversational host CLI (Claude Code, Codex, Gemini), YOU walk the user through the tour right here in the chat.** Render the beats below directly as your reply. Ask the user the prompts marked `PROMPT THE USER:` and wait for their reply between beats. Do **not** spawn a subprocess for the tour. The companion `onboard.py` script is for non-conversational contexts (terminal-only operators, CI) and is invoked only when the user explicitly asks for `check` (machine-state report) or `explain <topic>` (single-concept explainer) via Bash.

**The first reply after `/onboarding-guide` must contain visible chat output** — at minimum, Beat 0's greeting and the experience-level question. A silent or subprocess-only reply is a regression.

If the user asks "what is X?" mid-tour, or types `/onboarding-guide explain <topic>`, read the matching `## <topic>` section from `EXPLAINERS.md` (sibling file in this directory) and serve it back in your reply.

## Mission

Translate the factory from "a folder with a lot of files" into "I see what each piece does and what to do next" — without sycophancy, without condescension, without jargon that hasn't been translated first.

## Tone Discipline (read before extending this skill)

- **No sycophancy.** No "Great question!", no "You're doing amazing!". The operator's time is the scarce resource; respect it.
- **No condescension.** No "Don't worry if this is hard". Just explain it.
- **No jargon without translation.** First mention of every agentic-vocabulary term gets a one-sentence plain-English rewrite in parentheses. Examples:
  - MCP (the open standard for letting an AI agent talk to external tools)
  - hook (a script that runs before or after an AI tool call, allowing or blocking it)
  - sandbox (a restricted environment that limits what a process can read or write)
  - memory layer (one shared file every AI tool reads from and writes to)
- **Ask, don't assume.** When the operator's experience level is unclear, ask one short question and adapt. Do not lecture them through context they already have.
- **Show, don't tell.** Run the actual commands. Show the actual output. Translate it. "Here's what we just verified: [output]. In plain terms: [translation]."

---

## The Seven Beats (Beat 0 through Beat 7)

Each beat is small (≤12 lines of visible output before the next pause or prompt) and ends in either a `PROMPT THE USER:` line or a "press Enter / continue when ready" pause. Render the content as your assistant reply. Render code blocks and tables as Markdown. Do not collapse multiple beats into a single mega-reply; pace them so the user can absorb each one before the next.

---

### Beat 0 — Greeting + Experience Prompt

Render this block as your reply, then wait for the user's answer:

```
========================================================
  Agent Forge — quick tour
========================================================

You just unzipped a factory that makes three AI coding tools
(Claude, Codex, Gemini) speak the same language.

Same skill, same safety rule, same shared brain — rendered
into each tool's native format from one source.

I'll keep this short. Answer the prompt below; I'll pause between
beats so you can absorb each one.

(Last reviewed against vendor docs: 2026-05-23. State of the field
changes; re-verify before relying on specifics.)
```

**PROMPT THE USER:**

> Have you used any of the three AI coding CLIs (Claude Code / OpenAI Codex / Google Gemini CLI) before?
>
> - **(a)** Yes — two or three of them. I'll keep things terse.
> - **(o)** One of them. I'll translate jargon on first use.
> - **(n)** None yet — starting fresh. I'll translate every term.
> - **(u)** Not sure — check my machine for me. (If chosen, run `which claude codex gemini` via Bash and report what's installed; then pick the closest level for the rest of the tour.)

Wait for the user's reply. Record the level mentally; it shapes how much you translate going forward.

---

### Beat 1 — Role Prompt

Render this block as your next reply:

```
Quick second question — what brings you here today?
```

**PROMPT THE USER:**

> - **(c)** Curious — I want to understand what this is.
> - **(b)** Builder — I want to extend or contribute.
> - **(o)** Operator — I'm setting up the factory for a team.
> - **(d)** Decider — I'm evaluating whether to adopt this.

Wait for the user's reply. Record the role; it shapes the role-tuned closing line in Beat 7.

---

### Beat 2 — What Is This Folder?

Render this block as your next reply. Read `~/Projects/_agent_forge/registry.json` via the Read tool first; count the entries under `skills` and substitute the count where indicated.

```
◆ This folder is a factory.

You write a skill once — a short markdown file describing what
an AI tool should do. The factory turns that one file into three
different configurations, one for each AI tool.

You don't copy-paste. You don't maintain three versions.
The factory does the translation.

✓ Right now this factory holds <N> skills.
```

(Where `<N>` is the count from `registry.json`. If the file is unreadable, omit the count line rather than fabricating.)

**PAUSE:** End the reply with "press Enter when ready, or ask 'what is X?' if any term above is unfamiliar" and wait. If the user asks an explainer-style question, read the matching section from `EXPLAINERS.md` and serve it; then continue to Beat 3 when they press Enter.

---

### Beat 3 — The Cross-Host Translation Table

Render this block as your next reply. The tease first; then on the user's next "Enter," render the table.

**First reply (the tease):**

```
◆ Here's the trick.

All three tools share one capability format: the SKILL.md
open standard (agentskills.io, adopted late 2025 / early 2026).
Where they differ is HOW you invoke a skill and what they call
the isolated-context variant.

  Claude:  /skill-name  invokes skills.  @agent-name  spawns subagents.
  Codex:   /skills menu or $mention.     Subagents via delegation.
  Gemini:  Model auto-activates skills.  @subagent-name  for subagents.

Same primitive. Three invocation styles.
```

End with: "press Enter to see all the names side-by-side."

**Second reply (the payoff — render the ASCII table verbatim inside a code fence):**

```
Concept             Claude         Codex           Gemini
-------------------------------------------------------------
Skill format        SKILL.md       SKILL.md        SKILL.md   (agentskills.io)
Skill invocation    /name          /skills, $name  activate_skill tool
Subagent format     YAML md        TOML            YAML md
Subagent invocation @name          delegation      @name
Pre-tool hook       PreToolUse     PreToolUse      BeforeTool
Stop / end event    Stop           Stop            SessionEnd
MCP config          .mcp.json      config.toml     settings.json
Memory target       native         sidecar         sidecar
Boot file           CLAUDE.md      AGENTS.md       GEMINI.md
```

Underneath, add two short lines:

> All three adopted the agentskills.io standard in late 2025 / early 2026.
> The factory still translates per-host quirks the standard doesn't cover.

**PAUSE:** "press Enter to continue."

---

### Beat 4 — The Seatbelt (Telemetry Guardian)

Render this block as your next reply. Optionally, before rendering, run `wc -l ~/.agent-forge/guardian.log 2>/dev/null || echo 0` via Bash to get a live event count; if the file doesn't exist or the count is zero, omit the "logged N events" line.

```
◆ The seatbelt

Agents will run shell commands for you. That's the point.
It's also the risk.

The factory runs one check before every shell command on every
AI tool. It refuses obviously destructive patterns:

  - force-push to main
  - rm -rf $HOME
  - git reset --hard <ref>
  - --no-verify, --no-gpg-sign

Intentionally dumb. Predictability beats sophistication.

✓ It's logged <N> events on this machine.   (only if N > 0)
```

**PAUSE:** "press Enter to continue."

---

### Beat 5 — The Shared Brain (MEMORY.md)

Render this block as your next reply:

```
◆ The shared brain

All three AI tools read one file per project: MEMORY.md.

Build commands. Project quirks. Recent decisions. Known failures.
What Claude learns today, Codex sees tomorrow.

Append-first. Secrets blocked at write time. Only Claude has
native auto-memory; for Codex and Gemini the factory bridges
to sidecar files in .codex/memory/ and .gemini/memory/.
```

**PAUSE:** "press Enter to continue."

---

### Beat 6 — Install Gate

Detect missing host CLIs first. Run `which claude codex gemini` via Bash. For each CLI present, note it as ✓; for each missing, mention it explicitly.

**If all three are present:**

```
◆ Install check

  ✓ claude is on PATH
  ✓ codex  is on PATH
  ✓ gemini is on PATH

All three host CLIs are installed. Nothing to do here.
```

**If any are missing**, render the install lookup table below for only the missing CLIs:

| CLI | Vendor | What it's for | Docs | Install command |
|---|---|---|---|---|
| `claude` | Anthropic | Best memory story; native slash commands and subagents. | https://docs.anthropic.com/claude/docs/claude-code | `npm install -g @anthropic-ai/claude-cli` |
| `codex` | OpenAI | Strongest default sandbox (bwrap on Linux, Seatbelt on macOS). | https://platform.openai.com/docs/codex | Follow the docs link — install method varies by platform. |
| `gemini` | Google | Vision-capable; cheapest non-trivial tier. | https://ai.google.dev/gemini-api/docs/cli | `npm install -g @google/gemini-cli` |

Then offer: "Or install all three at once: `bash ~/Projects/_agent_forge/scripts/bootstrap-workstation.sh`."

**PROMPT THE USER:** "Want me to walk you through installing one of these, or skip ahead?" If they want a walk-through, name the CLI's vendor + tagline + docs URL + install command, then ask which to install next. If they want to skip, continue to Beat 7.

---

### Beat 7 — Role-Tuned Next Action + Goodbye

Render this block as your next reply. Pick the role-specific bullet that matches the role the user gave in Beat 1.

```
◆ That's the tour.

Working mental model now in place:
  - The factory (one source, three deliveries)
  - The cross-host translation table
  - The safety gate
  - The shared brain
```

Then the role-tuned action:

| Role | Next-action paragraph |
|---|---|
| **Curious (c)** | "Read the `state-of-the-field` explainer next — type `/onboarding-guide explain state-of-the-field`. It names what's converged across the three vendors and what hasn't, dated and cited. Then pick one skill that piqued your interest and read its `SKILL.md` end-to-end." |
| **Builder (b)** | "Read `docs/SOTA_2026_AUDIT.md` before authoring a new skill — that file is the verified state of cross-vendor standards. Then use `skill-author` to start authoring. Test on at least two hosts before merging." |
| **Operator (o)** | "Bake `scripts/verify-agent-forge.py` and `scripts/validate-triad-runtime.py` into your team's CI. The structural verifier confirms files on disk; the runtime gate confirms each host's CLI can actually see what the factory shipped — that's the part that catches Gemini event-name drift the structural verifier can't." |
| **Decider (d)** | "`policies/hooks.json` is the auditable deny list — those are your procurement talking points. `docs/SOTA_2026_AUDIT.md` is the procurement-grade evidence trail of what's standardized across the three vendors and what isn't, with primary-source citations." |

End with one short line:

```
Welcome to Agent Forge.
```

---

## Modes

The skill has three modes from the operator's perspective:

| Mode | Where it runs | What it does |
|---|---|---|
| `tour` (default) | **Inline in chat** (this file) | The seven beats above, paced. |
| `check` | Terminal via Bash | Non-interactive machine-state report (six probes). The assistant invokes `python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py check` and shows the output. |
| `explain <topic>` | Inline or terminal | Single-concept explainer. The assistant reads the matching `## <topic>` section from `EXPLAINERS.md` and serves it back; the terminal fallback is `python3 onboard.py explain <topic>` which reads the same file. |

The non-conversational `tour` subcommand of `onboard.py` is now a redirect message ("The tour now runs inline in Claude Code / Codex / Gemini. Type `/onboarding-guide`. For machine-state check, run `python3 onboard.py check`.") — operators in pure-terminal contexts use `check` and `explain`; the inline tour is reserved for host CLIs.

## Discipline / What This Skill Does NOT Do

The skill is read-only and observational. By design, it does not:

- Modify `MEMORY.md`, `LESSONS_LEARNED.md`, or any canonical source.
- Auto-fix detected problems. It reports the diagnosis and recommends the fix command; the operator runs it.
- Invoke long-running CLI calls (`claude -p` / `codex exec` / `gemini -p`) from within the tour. Per the 2026-04-26 leftover-subprocess-tree lesson, those run from a real terminal only. The tour describes what `validate-triad-runtime.py --probe-invocations` does and points the operator to run it; the tour does not run it itself.
- Modify `bootstrap-project.sh`. The integration hook (calling this skill at end of bootstrap) is documented in `docs/HANDOFF.md` as a future enhancement, not done here.
- Write to `MEMORY.md`. The tour is read-only of canonical state.

## State-Detection Contract

The full diagnostic surface (the same six probes shown to the operator via `/onboarding-guide check`) is implemented in `onboard.py`:

1. Is `_agent_forge` deployed at `~/Projects/_agent_forge` with the canonical files (`AGENTS.md`, `policies/hooks.json`, `policies/memory.json`, `registry.json`)?
2. Is `verify-agent-forge.py` exit 0?
3. Are the three host CLIs (`claude`, `codex`, `gemini`) on `PATH`?
4. Is at least one governed project from `projects.json` actually present on disk?
5. Is `validate-triad-runtime.py --project <first-governed>` exit 0 (surface check only; no `--probe-invocations`)?
6. Are user-home host directories (`~/.claude`, `~/.agents`, `~/.gemini`) populated?

Each probe gets a green / yellow / red verdict and, on red, a one-line plain-English diagnosis plus the exact command to fix it. No "see docs/X" rabbit holes.

The inline tour does not run all six probes by default (it would slow Beat 0). Only Probe 3 (`which claude codex gemini`) runs inline, for the install gate at Beat 6. The full six-probe report is available via `/onboarding-guide check` (the assistant invokes `python3 onboard.py check` via Bash and shows the output) or by the operator running the script directly.

## When to Extend

- **New beat.** Add a new section above with the same structure: render block, optional `PROMPT THE USER:`, pause marker. Keep each beat under ~12 lines of visible output. If a beat grows past that, split into two beats with their own pauses.
- **New `explain` topic.** Add a `## <topic>` section to `EXPLAINERS.md` (alphabetical). One ~100–200 word entry. Reference a specific file in the operator's repo state if possible. If the topic is a host-CLI variant, end with "When to pick this host: ..." so a new operator can choose.
- **New diagnostic probe.** Add a function to the `PROBES` list in `onboard.py`. Each probe returns `(verdict, summary, fix_command)`. Verdicts are `"green"`, `"yellow"`, `"red"`. The probe is then automatically available to `check` mode.
- **New host.** If a fourth host CLI is added in the future: add a column to the translation table in Beat 3; add a row to the install-gate lookup in Beat 6; add a tier-0 explainer (`<host>-cli`) to `EXPLAINERS.md`; add a corresponding column to the `_EVENT_ALIASES` map in `scripts/omni_factory.py`. The triad runtime validator extension is out of scope for this skill but tracked in `docs/HOST_INTEGRATIONS.md`.

### Acceptance Criteria for Maintainers

- **Inline-delivery acceptance gate:** Type `/onboarding-guide` in a fresh Claude Code session in this repo. Within the assistant's first reply, Beat 0's greeting and the experience-level prompt must appear as visible chat output. No subprocess attempt. No "did nothing" silence. This is the primary regression gate.
- The seven beats read naturally aloud at a normal pace in under 10 minutes including pauses. If a contributor adds a beat that pushes total length past that, split into two skills or move content into an `explain` topic.
- Every agentic term used in the tour appears either in `EXPLAINERS.md` or in the on-screen jargon-translation aside. If a new term shows up untranslated, that is a regression.
- Cross-host names (PreToolUse / BeforeTool, MCP config file names, etc.) in the Beat 3 table must match the canonical → native mapping in `scripts/omni_factory.py:_EVENT_ALIASES` and in `docs/HOST_INTEGRATIONS.md`. If the table drifts from the code, the code is right and the table needs updating.
- No beat may exceed ~12 lines of visible output before a `PROMPT THE USER:` or pause. Walls of text are the failure mode this design exists to prevent.

When extending, re-read the **Tone Discipline** section above first. Tone drift is the most common way this skill degrades in maintenance.

## Why This Skill Exists

Before this skill, a first-time operator who finished `bootstrap-project.sh` saw a wall of `[OK]` lines from `verify-agent-forge.py` and a triad-validator JSON dump and was expected to know what to do with that. Most won't. The factory's strength — canonical-first, three host CLIs, runtime validation gate — is invisible to a fresh operator until someone walks them through it. This skill is that walkthrough, automated, and consistent across all three host CLIs because it is itself just a skill the factory ships.

Earlier versions ran the tour as a subprocess (`python3 onboard.py tour`) from the host CLI. That broke in conversational contexts: the subprocess has no terminal pipeline back to the chat, so the user typed `/onboarding-guide` and saw nothing. The inline-delivery contract above is the fix: the assistant renders the content directly in the conversation, no subprocess needed for the tour. The script remains for terminal-only modes (`check`, `explain`).
