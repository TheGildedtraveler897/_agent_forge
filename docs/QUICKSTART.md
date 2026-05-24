# Agent Forge Quickstart

This is the five-minute first-run flow for a fresh operator. If you have the bundle unpacked and want it working, read this top-to-bottom.

## Prerequisites

| Platform | Required | Notes |
|---|---|---|
| Linux (Debian/Ubuntu) | Python 3.10+, git, tar, jq | `apt install python3 git tar jq` |
| macOS | Python 3.10+, git, tar, jq | MacPorts: `sudo port install python311 git jq`. The factory's macOS bootstrap path is MacPorts-only. |
| Windows | Python 3.10+, git, PowerShell 5.1+ | Install Python from python.org; install git from git-scm.com. PowerShell ships with Windows. No WSL required for the Claude Code workflow. |

You also need at least one host CLI installed:

- **Claude Code** — required for the primary workflow. Install per Anthropic's instructions for your platform.
- **OpenAI Codex CLI** — optional, for multi-host workflows.
- **Gemini CLI** — optional, for multi-host workflows.

## Step 1 — Get the bundle onto the machine

Either clone the repository, or unpack a suitcase zip that was produced by `scripts/factory-export.sh --mode onboarding` on a canonical machine.

```
unzip agent-forge-suitcase-<timestamp>.zip
cd agent-forge-suitcase-<timestamp>/
```

## Step 2 — Deploy the framework into your user home

This copies the canonical skills, hooks, and policies into your host CLI's user-home directories so Claude Code (and Codex/Gemini if you have them) can see them.

**Linux / macOS:**

```bash
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

**Windows ZIP transfer (native PowerShell, no WSL):**

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\agent-forge-suitcase-<timestamp>-deploy-and-bootstrap.ps1 -BundleZip .\agent-forge-suitcase-<timestamp>.zip -DestinationRoot .\af
```

The Windows deploy script unblocks the ZIP, extracts it with `Expand-Archive`, validates that `_agent_forge\AGENTS.md`, `docs\`, and `policies\` exist, then runs `deploy-factory.ps1`. If you already have a safely extracted bundle, run `powershell.exe -ExecutionPolicy Bypass -File .\_agent_forge\scripts\deploy-factory.ps1 -ClaudeOnly`.

This writes to:

- `~/.claude/skills/` on Linux/macOS, `%USERPROFILE%\.claude\skills\` on Windows
- `~/.codex/...` if you have Codex installed
- `~/.gemini/...` if you have Gemini installed

The deploy is idempotent — run it again any time the canonical factory changes.

## Step 3 — (Optional) Install host CLIs

If you don't already have Claude Code / Codex / Gemini installed, the workstation bootstrap can install them on Linux or macOS-via-MacPorts:

```bash
./_agent_forge/scripts/bootstrap-workstation.sh
```

Windows operators can run the detection helper:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\_agent_forge\scripts\bootstrap-workstation.ps1
```

Pass `-Install` to let it use `winget` for Python, Git, and Node.js LTS. Codex and Gemini runtime testing on Windows should use WSL2 unless their CLIs already work in native PowerShell.

## Step 4 — Authenticate

For each host CLI you intend to use:

```bash
claude        # Anthropic browser login
codex --login # OpenAI account login (optional)
gemini        # Google login (optional)
```

## Step 5 — Verify factory health

From inside the unpacked bundle (or after cloning, from `~/Projects/_agent_forge`):

```bash
python3 scripts/verify-agent-forge.py
```

Expected: exit 0 with no `[FAIL]` lines. The verifier checks file presence, schema parsing, and cross-references.

## Step 6 — Bootstrap your first governed project

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name my-first-app
```

On Windows (native PowerShell):

```powershell
pwsh -File .\scripts\bootstrap-project.ps1 -Name my-first-app
```

The bootstrap creates the minimum required files at `~/Projects/my-first-app/` (`AGENTS.md`, `CLAUDE.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, `.claude/CLAUDE.md`), appends an entry to `projects.json`, and syncs all three host-native surfaces.

## Step 7 — Triad-test the result

```bash
python3 scripts/validate-triad-runtime.py --project my-first-app
```

Expected: `overall pass=true` with `hook_pass + memory_pass + bridge_pass + mcp_pass` green for each host you have installed. Codex without bubblewrap support escalates to `filesystem` evidence per documented doctrine.

## Step 8 — Take the interactive tour

Inside Claude Code, with `~/Projects/my-first-app` as the working directory, invoke the `onboarding-guide` skill:

```
/onboarding-guide
```

The tour runs inline in the chat — eight paced beats, two short prompts (experience and role), the cross-host translation table, the shared brain, the cross-host handoff, and a per-host install gate. Read-only.

## Step 9 — First demo task

From inside Claude Code at `~/Projects/my-first-app`, ask Claude to build a small thing using the full skill chain:

> Build me a simple Python CLI that takes a YAML config and prints a formatted summary. Use the spec-architect → execution-planner → tdd-engineer → verification-gate flow.

You should see Claude invoke each workflow skill in turn, with embedded RED tests, watched-failing-test gates, and a fresh-evidence completion gate at the end.

## Troubleshooting

**`verify-agent-forge.py` reports `[FAIL]`:** Run it again with `-v` for verbose output. Most failures are schema-validation issues in a recently edited canonical source.

**Hook isn't firing:** Run `validate-triad-runtime.py --probe-invocations`. This fires a real test command and observes whether the hook actually intercepts it. Surface check is necessary but not sufficient.

**Claude Code on Windows doesn't see the skills:** Confirm the `deploy-factory.ps1` script wrote to `%USERPROFILE%\.claude\skills\`. Check the script's output for any permission errors.

**Windows ZIP extracts incompletely:** Move the ZIP to a short path such as `C:\af`, then run `deploy-and-bootstrap.ps1`. It unblocks the ZIP before extraction and fails fast if `AGENTS.md`, `docs\`, or `policies\` are missing.

**PowerShell execution policy blocks scripts:** Use `powershell.exe -ExecutionPolicy Bypass -File <script.ps1>` for the local trusted bundle after reviewing its source.

**Installed tools are still missing from PATH:** Close the terminal and open a new PowerShell window.

**`MacPorts is required` error on macOS:** Install MacPorts from <https://www.macports.org/install.php>. The factory's macOS bootstrap path is MacPorts-only per supported-platform policy.

## Where to go next

- `README.md` § Repository layout — what each top-level directory holds.
- `docs/CONOPS.md` — durable architecture.
- `docs/HOST_INTEGRATIONS.md` — per-host rendering rules.
- `docs/LESSONS_LEARNED.md` — append your first lesson when you hit something non-obvious.
