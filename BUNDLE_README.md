# Agent Forge — A Portable Multi-Agent Factory

You just unzipped Agent Forge. This file is the first thing to read.

## What this is

Agent Forge is a small Python-based factory that takes one canonical definition of a coding workflow and renders it into the native shape of three different AI coding command-line tools: Claude Code (Anthropic), OpenAI Codex CLI, and Gemini CLI (Google). Write a skill once, and the same skill shows up in all three tools with the right name, the right file format, and the right safety rules — no copy-paste, no drift.

It also ships:

- A safety gate (`telemetry-guardian`) that runs before every shell command on every host and refuses obviously dangerous patterns like force-pushing to main or wildcard home deletion.
- A shared brain (`MEMORY.md`) that all three hosts can read and write, so what one agent learns is visible to the others.
- A validation pyramid that proves, at deploy time, that all three host CLIs can actually see what the factory shipped.

## What to run first

**Step 1 — Deploy the factory** (one-time setup, about 30 seconds, makes no destructive changes):

**Linux or macOS:**
```bash
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

**Windows ZIP transfer (native PowerShell, no WSL required):**
```powershell
powershell.exe -ExecutionPolicy Bypass -File .\agent-forge-suitcase-<timestamp>-deploy-and-bootstrap.ps1 -BundleZip .\agent-forge-suitcase-<timestamp>.zip -DestinationRoot .\af
```

This copies the canonical factory into `~/Projects/_agent_forge` and renders Claude / Codex / Gemini surfaces into your user-home host directories. Windows defaults to Claude-only; pass `-AllHosts` after Codex and Gemini are installed. The Windows entry point unblocks the ZIP before extraction, avoids Explorer's partial-extract failure mode, and warns when the destination path is long enough to risk MAX_PATH issues.

If the bundle is already safely extracted, Windows operators can run:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\_agent_forge\scripts\deploy-factory.ps1 -ClaudeOnly
```

**Step 2 — Run the inline onboarding tour.** Open Claude Code (or Codex, or Gemini CLI) in any project, and type:

```
/onboarding-guide
```

The assistant walks you through eight paced beats right in the chat — what the factory is, the cross-host translation table, the safety gate, the shared brain, the cross-host handoff, and a per-host install gate. The tour is read-only; nothing it shows you modifies your system.

**Step 3 — Machine state check (optional, for terminal-only operators):**

```
python3 _agent_forge/skills/global/onboarding-guide/onboard.py check
```

Six probes, plain-English verdicts, exact fix command on any red.

## What "amazes you" looks like

If you stick around for ten minutes after the tour, you'll see this:

1. The same canonical skill (say, `spec-architect`) appears as `/spec-architect` in Claude Code, as `spec-architect` in the Codex skill registry, and as `/spec-architect` in Gemini CLI — all rendered from one source file.
2. The safety gate intercepts a destructive command on whichever host you try it on, with the same denial message.
3. The shared brain at `MEMORY.md` is updated by one host and immediately readable by the other two.

That's the factory's whole pitch made visible: three different vendors, one author surface, no drift.

For the scripted ten-minute walkthrough see `_agent_forge/docs/DEMO_PATH.md`.

## When it doesn't work

Run the machine-state check after any fix:

```
python3 _agent_forge/skills/global/onboarding-guide/onboard.py check
```

It reports six green/yellow/red probes and tells you the exact command to fix anything red.

For per-host troubleshooting, see `_agent_forge/docs/QUICKSTART.md` and `_agent_forge/docs/HOST_INTEGRATIONS.md`.

Windows troubleshooting:

- If PowerShell refuses to run a script, use the `powershell.exe -ExecutionPolicy Bypass -File ...` form shown above.
- If extraction appears incomplete, do not use Explorer's Extract All. Re-run `deploy-and-bootstrap.ps1`; it calls `Unblock-File` before `Expand-Archive` and validates the extracted tree.
- If extraction fails under a deeply nested folder, move the ZIP to a short path such as `C:\af` and re-run. This avoids MAX_PATH edge cases.
- If newly installed tools are not on PATH, close PowerShell and open a new terminal.

## Where to go next

- Full project overview: `_agent_forge/README.md`
- Durable architecture: `_agent_forge/docs/CONOPS.md`
- Multi-agent contract: `_agent_forge/AGENTS.md`
- Operator quickstart: `_agent_forge/docs/QUICKSTART.md`

## Who built this

Agent Forge is an open framework. Contact information for the maintainer of this specific bundle is in the bundle's `MANIFEST.json` if it was provided at export time; otherwise, work from the public sources listed above.

---

*One source of truth. Three host CLIs. No drift. That's the whole idea.*
