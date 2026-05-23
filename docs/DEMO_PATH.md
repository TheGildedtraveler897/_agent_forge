# Demo Path — Ten Minutes That Show What Agent Forge Does

This is the scripted walkthrough a coworker can follow after they unzip the bundle. It is platform-aware (Linux / macOS / native Windows PowerShell) and read-only except where explicitly noted.

By the end of ten minutes, you will have seen:
- The factory deploy itself with one command.
- The onboarding-guide explain itself in your terminal.
- Three different AI coding CLIs see the same canonical skill, each in its own native shape.
- The safety gate refuse a known-bad command on every host with the same policy.

If any step fails, run `python3 _agent_forge/skills/global/onboarding-guide/onboard.py check` — it gives you the exact command to fix anything red.

---

## Step 1 — Unzip the bundle (~30s)

Wherever you keep code on this machine, unzip the bundle.

**Linux / macOS:**
```bash
tar -xzf agent-forge-suitcase-<timestamp>.tar.gz
cd agent-forge-suitcase-<timestamp>
```

**Windows (PowerShell):**
```powershell
Expand-Archive .\agent-forge-suitcase-<timestamp>.zip -DestinationPath .
cd .\agent-forge-suitcase-<timestamp>\
```

You should now have a directory containing `_agent_forge/`, `BUNDLE_README.md`, `START_HERE.txt`, and `MANIFEST.json`.

---

## Step 2 — Deploy the factory (~2 minutes)

This installs Agent Forge into `~/Projects/_agent_forge` on your machine. No admin rights required.

**Linux / macOS:**
```bash
./_agent_forge/scripts/deploy-factory.sh
```

**Windows (PowerShell):**
```powershell
pwsh -File .\_agent_forge\scripts\deploy-factory.ps1
```

The script copies the canonical sources, generates the host-native rendering, and exits with a one-line summary. If it asks to install the host CLIs, say no for this demo — the demo runs entirely from the Python skill helper.

---

## Step 3 — Run the onboarding tour (~3 minutes)

This is the headline. The tour runs **inline in the chat** of whichever host CLI you're using — Claude Code, Codex, or Gemini. The assistant walks you through seven paced beats, asking two short questions along the way.

In Claude Code (or Codex, or Gemini CLI), open any project under `~/Projects/` and type:

```
/onboarding-guide
```

The tour will ask:
1. Have you used any of the three host CLIs before? (`a` many / `o` one / `n` none / `u` check for me)
2. What brings you here today? (`c` curious / `b` builder / `o` operator / `d` decider)

Pick the answers that fit. The seven beats walk through what the folder is, the canonical-first model, the cross-host translation table, the seatbelt, the shared brain, an install gate for any missing host CLI, and a role-tuned next action.

Pay attention to Beat 3 ("The cross-host translation table"). The compact ASCII table the assistant renders there is the entire reason Agent Forge exists: three vendors shipped similar primitives with their own names, and the factory translates between them.

---

## Step 4 — Run the machine check (~30s)

Quick read-only audit of the factory's deployed state.

```bash
python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py check
```

Six green/yellow/red probes. After a fresh deploy you should see green on factory presence, verifier exit, and user-home surfaces. Host CLI probes will be yellow if you haven't installed the host CLIs yet (`claude`, `codex`, `gemini`). That's expected for the demo.

---

## Step 5 — See the same skill in two hosts (~3 minutes)

This step requires at least one host CLI installed. If you have Claude Code:

```bash
claude --version
# In a Claude Code session under any governed project:
/onboarding-guide
```

Notice the slash-command syntax: `/onboarding-guide`. That's Claude's native way of invoking a workflow skill.

If you also have Codex:

```bash
codex --version
# In a Codex session:
# (Codex uses no slash convention — skills are invoked by name via delegation.)
```

Same skill, same `SKILL.md` body, two host-native invocations.

If you have Gemini, the slash-command syntax matches Claude's:

```bash
gemini --version
# In a Gemini session:
/onboarding-guide
```

Three different CLIs, one canonical source, no copy-paste maintenance.

---

## Step 6 — Watch the seatbelt refuse a bad command (~1 minute)

In a real terminal (not the demo), try one of these in any host CLI:

```
git push --force origin main
```

The `telemetry-guardian` hook intercepts the command before it reaches your shell and refuses it. The refusal text names the rule that caught it. Try it on each host CLI you have installed — same policy, same refusal, three different hooks rendered from one `policies/hooks.json`.

Bypass for legitimate use is one env var:
```bash
AGENT_FORGE_GUARDIAN=off git push --force origin main
```

Every bypass is logged to `~/.agent-forge/guardian.log` so an on-call reviewer can audit the decision after the fact.

---

## What you just saw

In ten minutes, you saw the factory's three load-bearing properties:

1. **One author surface, three host shapes.** You wrote nothing; the factory rendered one skill into Claude, Codex, and Gemini native formats simultaneously.
2. **A policy gate that applies uniformly.** The seatbelt refused the same command on every host because the rule was authored once in `policies/hooks.json` and rendered to each host's event model.
3. **A shared brain that crosses vendors.** If you continue the demo by editing `<project>/MEMORY.md` from one host and reading it from another, you'll see the cross-host state layer in action.

That is the whole pitch: three vendors, one canonical source, no drift, with a runtime validator that proves it.

---

## When you have an hour, not ten minutes

- Read `_agent_forge/docs/CONOPS.md` for the durable architecture.
- Read `_agent_forge/AGENTS.md` for the multi-agent workflow discipline chain (spec-architect → execution-planner → tdd-engineer → branch-finisher).
- Read `_agent_forge/docs/ARCHITECTURE_MINDMAP.md` for the comprehensive map of every skill, policy, and rendering surface.
- Run `python3 _agent_forge/skills/global/onboarding-guide/onboard.py explain <topic>` for any concept that needs more depth. Topics include `claude-cli`, `codex-cli`, `gemini-cli`, `agent`, `agent-team`, `skill`, `hook`, `mcp`, `memory`, `triad-validator`, `validation-pyramid`, and more.

If the demo path here didn't work at some step, the gap is documented and recoverable — re-run `onboard.py check` for the diagnosis and the fix command.
