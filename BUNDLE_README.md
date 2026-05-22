# Agent Forge — A Portable Multi-Agent Factory

You just unzipped Agent Forge. This file is the first thing to read.

## What this is

Agent Forge is a small Python-based factory that takes one canonical definition of a coding workflow and renders it into the native shape of three different AI coding command-line tools: Claude Code (Anthropic), OpenAI Codex CLI, and Gemini CLI (Google). Write a skill once, and the same skill shows up in all three tools with the right name, the right file format, and the right safety rules — no copy-paste, no drift.

It also ships:

- A safety gate (`telemetry-guardian`) that runs before every shell command on every host and refuses obviously dangerous patterns like force-pushing to main or wildcard home deletion.
- A shared brain (`MEMORY.md`) that all three hosts can read and write, so what one agent learns is visible to the others.
- A validation pyramid that proves, at deploy time, that all three host CLIs can actually see what the factory shipped.

## What to run first

Pick the command for your platform. Read-only, takes about five minutes.

**Linux or macOS:**
```bash
python3 _agent_forge/skills/global/onboarding-guide/onboard.py tour
```

**Windows (native PowerShell, no WSL required):**
```powershell
python .\_agent_forge\skills\global\onboarding-guide\onboard.py tour
```

The tour will ask two quick questions — your experience level and your role — then walk you through six short sections explaining what every part of the factory is, why it exists, and what to do next. Nothing the tour runs will modify your system.

## What "amazes you" looks like

If you stick around for ten minutes after the tour, you'll see this:

1. The same canonical skill (say, `spec-architect`) appears as `/spec-architect` in Claude Code, as `spec-architect` in the Codex skill registry, and as `/spec-architect` in Gemini CLI — all rendered from one source file.
2. The safety gate intercepts a destructive command on whichever host you try it on, with the same denial message.
3. The shared brain at `MEMORY.md` is updated by one host and immediately readable by the other two.

That's the factory's whole pitch made visible: three different vendors, one author surface, no drift.

For the scripted ten-minute walkthrough, after the tour see `_agent_forge/docs/DEMO_PATH.md` (created in a future sprint; ignore the reference if it isn't present yet).

## When it doesn't work

The tour ends with a `check` command. Re-run it after any fix:

```
python3 _agent_forge/skills/global/onboarding-guide/onboard.py check
```

It reports six green/yellow/red probes and tells you the exact command to fix anything red.

For per-host troubleshooting, see `_agent_forge/docs/QUICKSTART.md` and `_agent_forge/docs/HOST_INTEGRATIONS.md`.

## Where to go next

- Full project overview: `_agent_forge/README.md`
- Durable architecture: `_agent_forge/docs/CONOPS.md`
- Multi-agent contract: `_agent_forge/AGENTS.md`
- Operator quickstart: `_agent_forge/docs/QUICKSTART.md`

## Who built this

Agent Forge is an open framework. Contact information for the maintainer of this specific bundle is in the bundle's `MANIFEST.json` if it was provided at export time; otherwise, work from the public sources listed above.

---

*One source of truth. Three host CLIs. No drift. That's the whole idea.*
