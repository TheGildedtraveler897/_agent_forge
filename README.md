# Agent Forge

**A portable governance factory that gives three AI coding command-line tools — Claude Code, OpenAI Codex, and Gemini CLI — the same skills, the same safety guardrails, and the same shared memory, generated outward from one canonical source of truth.**

You write a skill, a hook, or a memory section *once*, in `_agent_forge/`. The factory translates it into each host's native shape and validates that all three host CLIs can actually see and use it. No more maintaining three parallel sets of prompts, hooks, and memory files. No vendor lock-in. No silent drift between hosts.

This README is written for two audiences: someone new to "agentic CLI workflows" who wants to understand what this is and why it exists, and a senior architect who wants the concrete component map and current state. Section headers tell you which audience the section is aimed at.

---

## Table of contents

1. [What this is, in one paragraph](#what-this-is-in-one-paragraph) — start here
2. [Mental model](#mental-model) — the diagram in markdown
3. [What you get today](#what-you-get-today) — capability inventory
4. [For beginners — what is an agentic workflow](#for-beginners--what-is-an-agentic-workflow)
5. [For senior architects — the component map](#for-senior-architects--the-component-map)
6. [The five recent improvements explained](#the-five-recent-improvements-explained)
7. [Quickstart (5 minutes)](#quickstart-5-minutes)
8. [Where to look next](#where-to-look-next) — annotated doc map
9. [Extending the factory](#extending-the-factory)
10. [Governance discipline](#governance-discipline)
11. [Repository layout](#repository-layout)
12. [Honest limitations](#honest-limitations)
13. [FAQ — common stalls and quick answers](#faq--common-stalls-and-quick-answers)

---

## What this is, in one paragraph

The Omni-Factory is a single repository (`_agent_forge`) that holds **canonical definitions** for everything an AI coding agent needs — skills (reusable workflows), hooks (safety rules and automation), memory (cross-host shared brain), team manifests (named multi-agent patterns), and MCP server inventory (third-party tool integrations) — and a single Python engine (`scripts/omni_factory.py`) that *generates* host-native delivery files for Claude Code, OpenAI Codex, and Gemini CLI from those canonical sources. After every change, a runtime validator (`scripts/validate-triad-runtime.py`) asks each host's actual CLI "can you see what we just generated?" and refuses to call the change green until all three say yes. The result: a coding stack where the same skill or safety rule fires identically on every AI tool you use, without you maintaining three separate copies.

---

## Mental model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CANONICAL SOURCES                              │
│                       (you author these once)                           │
│                                                                         │
│  skills/**/SKILL.md       teams/*.json       projects.json              │
│  policies/hooks.json      policies/memory.json     global-mcp.json      │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     scripts/omni_factory.py                             │
│            (the engine — reads canonical, renders native)               │
└────┬─────────────────────────────┬──────────────────────────────┬───────┘
     │                             │                              │
     ▼                             ▼                              ▼
┌──────────────────┐    ┌────────────────────┐    ┌─────────────────────┐
│  Claude Code     │    │   OpenAI Codex     │    │   Gemini CLI        │
│                  │    │                    │    │                     │
│ ~/.claude/...    │    │ ~/.agents/skills   │    │ ~/.gemini/...       │
│ <project>/       │    │ <project>/         │    │ <project>/          │
│   .claude/       │    │   .agents/skills   │    │   .gemini/          │
│   .mcp.json      │    │   .codex/...       │    │   GEMINI.md         │
└──────────────────┘    └────────────────────┘    └─────────────────────┘
                                   │
        ┌──────────────────────────┴───────────────────────┐
        ▼                                                  ▼
┌─────────────────────────────┐              ┌──────────────────────────┐
│  CROSS-HOST SHARED BRAIN    │              │   VALIDATION GATE        │
│  <project>/MEMORY.md        │              │  verify-agent-forge.py   │
│  <project>/.forge_state/    │              │  validate-triad-runtime  │
│   (one file, three hosts    │              │  (asks each host's CLI:  │
│    read and write to it)    │              │   "can you see this?")   │
└─────────────────────────────┘              └──────────────────────────┘
```

**The three rules that make this work:**
1. **Canonical-first.** You only ever edit the canonical sources (top of the diagram). The host-native files (middle of the diagram) are generated and never hand-edited.
2. **Generate identically.** `omni_factory.py` is the single engine. If a change should land on all three hosts, the engine guarantees it. If it should only land on one, you say so explicitly in the canonical record.
3. **Validate live.** After every change, the triad runtime validator asks each host's actual CLI to enumerate what it sees. The gate is "all three hosts agree" — not "files exist on disk."

---

## What you get today

| Surface | State | Detail |
|---|---|---|
| **29 governed skills** | ✅ Production | Workflow discipline (spec → plan → TDD → review → verify → finish), domain experts (legal, infra, brand, finance), meta-skills (skill-author, sprint-harvester, memory-archivist, telemetry-guardian, live-hook-prober). |
| **Six governed projects pre-wired** | ✅ Production | `jarvis`, `RoboNaaz`, `ZorroClaw`, `homelab`, `ZorroForge/factory`, `playlist-archive`. Add yours with one bootstrap command. |
| **Universal pre-tool guardrail** | ✅ Production | `telemetry-guardian` blocks destructive shell commands before they run. Fires on every host. Bypass is auditable. |
| **Universal cross-host memory layer** | ✅ Production | `MEMORY.md` + `.forge_state/` per project. Five sections (build commands, project quirks, active tasks, recent decisions, known failures). All three hosts read and write the same file. |
| **Append-first knowledge anchor** | ✅ Production | `docs/LESSONS_LEARNED.md`. Doctrine never moves silently. |
| **Triad runtime validator** | ✅ Production | Asks each host's CLI to enumerate skills + verifies hook surface + verifies memory surface. Live invocation probe gate via `--probe-invocations`. |
| **Codex sandbox-aware probe** | ✅ Production | When Codex's bubblewrap blocks shell inspection, the validator escalates to filesystem evidence per documented doctrine. |
| **Suitcase / portability** | ✅ Production | One-shot deploy + bootstrap script. Move the factory between machines without carrying secrets or per-machine residue. |
| **Full SOTA recon ledger** | ✅ Recorded | `docs/PATHFINDER_LEDGER.md` — 700+ lines of researched intelligence on Claude Code 26-event hook lifecycle, Codex CLI v0.122–0.125 changelog, Gemini CLI v0.39, NVIDIA Nemotron bash-computer-use paradigm, multi-agent orchestration frameworks, MCP routing. |
| **Forward roadmap** | ✅ Authored | `docs/PATHFINDER_ROADMAP.md` (architectural upgrades + capability backlog) + `docs/SPRINT_BACKLOG.md` (the next three sprints with copy-pasteable Codex execution prompts). |

---

## For beginners — what is an agentic workflow

If you've never used Claude Code, OpenAI Codex, or Gemini CLI before, here's the quick mental model.

**A "coding agent CLI"** is a command-line tool you point at a project. You ask it in plain English to do something — "write tests for the auth module", "fix this bug", "refactor this function" — and it reads your code, edits files, runs commands, runs tests, and reports back. It can do multi-step work autonomously, ask you questions when it's stuck, and (with the right configuration) connect to external services.

**Three big ones in 2026:**
- **Claude Code** (Anthropic) — most polished IDE/desktop/web/terminal experience.
- **OpenAI Codex** (OpenAI) — strongest sandboxing and deep-research integration.
- **Gemini CLI** (Google) — best multi-transport MCP routing and hierarchical context.

Each one has its own way to:
- Define a **skill** (a reusable workflow you can trigger by name).
- Configure a **hook** (a safety check that runs before or after every tool call — for example, "block any `git push --force` to main").
- Persist **memory** across sessions (so the AI remembers your build commands and project quirks instead of re-learning them every conversation).
- Connect to **MCP servers** (the open standard for letting an AI agent talk to external tools — GitHub, Slack, your own internal services).
- Spawn **subagents** (specialized helpers that run in parallel with their own context).

The problem if you want to use *all three*: every host's configuration files have different shapes, different naming conventions, and different sandboxing models. Maintaining three parallel sets of skills/hooks/memory is tedious and silently drifts apart.

**This factory solves that.** You define the skill once. The factory generates the Claude version, the Codex version, and the Gemini version automatically. You define the safety rule once. All three hosts enforce it identically. You write a build command into the shared memory file. All three hosts read it on next session.

**The five terms you'll see most often:**
- **Skill** — a packaged workflow (one folder, one `SKILL.md`). Triggered by name in any host.
- **Hook** — a script that runs before/after a tool call to allow, block, or modify it. Universal pre-tool deny list = `telemetry-guardian`.
- **MCP** (Model Context Protocol) — open standard for AI ↔ external tool integration. We declare servers in `global-mcp.json`; the factory writes each host's native config.
- **Memory** — `MEMORY.md` per project. Cross-host shared facts about the project. Section anchors are stable; entries are append-first.
- **Sandboxing** — how the host CLI restricts what tools can do. Codex uses Linux bubblewrap, Claude has permission modes, Gemini has trusted-folder gates. The factory respects each.

---

## For senior architects — the component map

### Canonical authoring sources

| File | Purpose | Schema |
|---|---|---|
| `skills/global/<id>/SKILL.md` | Cross-project capability definition | Frontmatter: `name`, `description`, `capability_class` (workflow / expert), `targets` (host list), `delivery_projects` (which projects get it; `[*]` or omit for all), `model_tier`, `context_cost`. Body = durable instruction contract. |
| `skills/projects/<project>/<id>/SKILL.md` | Project-local capability | Same shape; `project: <name>` set automatically. |
| `teams/<name>.json` | Multi-agent team manifest | `roles`, `collapse_condition`, `escalate_condition`, `handoff_artifacts`, per-host `preferred_entries`. |
| `projects.json` | Governed project catalog | List of `{name, root, required_files}`. |
| `global-mcp.json` | Shared MCP server inventory | `servers` map; currently empty by design until first real shared server. |
| `policies/hooks.json` | Hook lifecycle records | v2: `shared[]` + per-host arrays of `{id, event, matcher, command, targets, timeout_ms, status_message}`. |
| `policies/memory.json` | Memory section schema | v1: `sections[]` of `{id, name, append_only, host_writers, host_readers, description}`, `retention`, `secrets_policy`. |

### Generated host surfaces

| Host | User-home surfaces | Per-project surfaces |
|---|---|---|
| **Claude** | `~/.claude/{agents,commands}` | `<project>/.claude/{agents,commands,skills,settings.json}`, `<project>/.mcp.json` |
| **Codex** | `~/.agents/skills` | `<project>/.agents/skills`, `<project>/.codex/{agents,config.toml,hooks.json}` |
| **Gemini** | `~/.gemini/{agents,commands,skills}`, `~/.gemini/GEMINI.md` | `<project>/GEMINI.md`, `<project>/.gemini/{agents,commands,skills,settings.json}` |
| **Cross-host** | n/a | `<project>/MEMORY.md`, `<project>/.forge_state/{README.md,manifest.json,archivist.log}` |

### The validation pyramid

```
Level 3 — Live invocation gate (deepest, slowest, most truthful)
  validate-triad-runtime.py --probe-invocations
  Fires real tool calls on each host CLI, observes whether hooks fire.
  Catches host-native semantic drift (the C1 class).

Level 2 — Triad surface gate (mandatory after every canonical change)
  validate-triad-runtime.py --project <name>
  Asks each host's CLI to enumerate skills; checks hook surface, memory surface.
  Codex sandbox-blocked falls back to filesystem-escalated evidence.

Level 1 — Structural verifier (cheapest, run constantly)
  verify-agent-forge.py
  File presence + schema parsing + cross-references resolve.
```

### Doctrine surfaces (read in this order)

| File | Purpose |
|---|---|
| `AGENTS.md` | Multi-agent contract. All three host CLIs auto-load it. |
| `CLAUDE.md` / `GEMINI.md` | Thin host boot adapters. Both import `AGENTS.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, `docs/LESSONS_LEARNED.md`. |
| `docs/CONOPS.md` | Durable architecture. |
| `docs/HOST_INTEGRATIONS.md` | Per-host rendering rules and event-name translation tables. |
| `docs/HANDOFF.md` | Last-sprint summary in chronological order. |
| `docs/LESSONS_LEARNED.md` | Append-first knowledge anchor. |
| `docs/PATHFINDER_LEDGER.md` | Raw research archive (sprawling brain-dumps). |
| `docs/PATHFINDER_ROADMAP.md` | Actionable architectural upgrades + capability backlog. |
| `docs/SPRINT_BACKLOG.md` | Concrete next-three-sprints with copy-pasteable Codex prompts. |
| `docs/TRIAD_RUNTIME_VALIDATION.md` | The live-validation runbook. |
| `docs/TECH_DEBT.md` | Honest open-debt and recently-resolved-debt inventory. |

### Recent architectural decisions worth knowing

1. **Canonical-first is the only edit point.** `registry.json` is generated compatibility output, not a source of truth. Generated host surfaces under `<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/` are never hand-edited.
2. **Append-first lessons.** Doctrine in `AGENTS.md` and `docs/CONOPS.md` does not move silently. Every change starts as a `LESSONS_LEARNED.md` entry, gets reviewed, and is promoted into doctrine only when durable + broad.
3. **Triad gate is mandatory.** After any canonical change, `validate-triad-runtime.py` must pass. The structural verifier is necessary but insufficient — only the runtime gate confirms the host CLIs can actually reach what we shipped.
4. **Curated allow-lists for cross-host semantics.** Whenever the factory crosses a host-native semantic boundary (event names, sandbox markers, permission strings, MCP tool prefixes), the validator checks against a curated allow-list of known-valid native values, not a substring match. This was the lesson of the C1 Gemini event-name drift.
5. **Native boot files stay native.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` keep their host-specific names. Secondary docs were renamed to host-agnostic forms; boot files were left alone.

---

## The five recent improvements explained

These are the five biggest architectural changes shipped in the prior sprint cycles. Each has a "What it solves" / "How it works" / "Why this shape" structure.

### 1. The `omni_factory.py` engine

**What it solves.** Before this engine, the factory had three things spread across three places: a `registry.json` that was supposed to be canonical, a set of hand-authored Claude adapters under `claude/`, and partial Codex/Gemini support in shell scripts. Authoring a new skill meant editing three places and hoping they stayed consistent. They didn't.

**How it works.** `scripts/omni_factory.py` is the single Python engine that:
- Reads canonical sources (`skills/`, `teams/`, `projects.json`, `global-mcp.json`, `policies/`).
- Discovers capability metadata from each `SKILL.md` frontmatter.
- Renders host-native delivery surfaces for Claude, Codex, and Gemini per the canonical declarations.
- Manages a `runtime/managed-state.json` ledger so it knows which generated files it owns and won't accidentally clobber user-tracked files.
- Exposes subcommands: `sync-claude`, `sync-codex`, `sync-gemini`, `render-registry`, `verify`.

**Why this shape.** A single engine means: one place to fix a rendering bug, one place to add a new host, one place to enforce naming conventions. The `registry.json` becomes generated compatibility output instead of a source of truth — which is the right place for a lookup table that downstream tools may want.

Sub-commands are deterministic. Run them ten times: identical output. This is what makes the suitcase doctrine work — re-deploy the factory anywhere, run the syncs, get exactly the same generated surfaces.

### 2. The `MEMORY.md` universal state layer

**What it solves.** Each host CLI has its own auto-memory system: Claude Code writes to `~/.claude/projects/<repo>/memory/MEMORY.md`, Gemini has its own indexes, Codex relies on AGENTS.md auto-discovery + session resume. Each is invisible to the others. A build command Claude learned overnight does not propagate to Gemini in the morning.

**How it works.** Every governed project gets a canonical `MEMORY.md` at its root, generated from `policies/memory.json`. The file has stable section anchors:

```
## Build Commands
<!-- section:build_commands -->
- 2026-04-26T17:39:31Z [claude] — tests run with pytest -xvs tests/

## Project Quirks
<!-- section:project_quirks -->
- ...
```

Five sections: `build_commands`, `project_quirks`, `active_tasks` (the only rewriteable section), `recent_decisions`, `known_failures`. Append-first. Secrets-deny patterns reject API keys, private keys, and credential-shaped strings at write time.

The `memory-archivist` skill exposes three subcommands:
- `append --project <root> --section <id> --entry "<text>" --source <host>` — timestamped append.
- `validate --project <root>` — confirms anchors and manifest are intact; warns at retention threshold.
- `summary --project <root>` — per-section counts.

All three hosts read this file: Claude/Codex via the AGENTS.md Read Order entry; Gemini via `@MEMORY.md` import in the generated `GEMINI.md`.

**Why this shape.** A single canonical file is the simplest possible cross-host shared state. No complex sync logic; no eventual-consistency edge cases; no per-host translation. Section anchors are stable identifiers so the archivist can find the right insertion point regardless of how human-prose flowing text changes around them. The append-first discipline guarantees that older sessions' learnings are never silently destroyed by newer ones.

**What's still incomplete.** The bridge to each host's *native* auto-memory — so a fact Claude learns and saves into its own auto-memory automatically reaches our canonical `MEMORY.md` — is **not yet shipped**. That's Sprint 3 (Capability B2 `memory-bridge`).

### 3. The `telemetry-guardian` universal pre-tool veto

**What it solves.** Three hosts, three different ways to register a "block dangerous commands" hook, three opportunities to forget one. Without a universal guardrail, an overeager AI agent can `git push --force origin main`, `rm -rf $HOME`, or `terraform destroy` without scope — and no one stops it.

**How it works.** `policies/hooks.json` v2 has a `shared` array. The seeded record there is `pre-tool-execution-guardian` with `command: bash ~/Projects/_agent_forge/skills/global/telemetry-guardian/guardian.sh`. The omni-factory renderer translates this single record into:
- Claude `<project>/.claude/settings.json` `hooks.PreToolUse`.
- Codex `<project>/.codex/hooks.json` `hooks.pre_tool_use`.
- Gemini `<project>/.gemini/settings.json` `hooks.BeforeTool`.

When any host attempts a Bash tool call, the guardian script reads the JSON invocation on stdin, matches the command against a deny list, and either exits 0 (allow) or 1 (block). The deny list:

| Pattern | Why blocked |
|---|---|
| `--no-verify` | Bypasses pre-commit hooks. |
| `--no-gpg-sign`, `-c commit.gpgsign=false` | Bypasses commit signing. |
| `git push ... --force` to `main`/`master`/`develop` | Force-push to protected branches. |
| `git reset --hard <ref>` against non-current branch | Destructive history rewrite. |
| `rm -rf $HOME`, `rm -rf ~`, `rm -rf /`, `rm -rf /*` | Wildcard root/home deletion. |
| `terraform destroy` without `-target` | Unscoped infra teardown. |
| `dd of=/dev/sda` | Whole-disk write. |
| `chmod -R 777 ~` | Permissions nuke. |

Bypass is via `AGENT_FORGE_GUARDIAN=off` for that session. Every bypass and every block is logged to `~/.agent-forge/guardian.log`.

**Why this shape.** The guardian is intentionally dumb. It does not reason, does not call out to a model, does not do anything fancy. The deny list is fixed-string or simple `grep -E`. This is *exactly* the property you want in a safety gate: predictability beats sophistication. Bypass is explicit and audited so when an operator legitimately needs to override, the override leaves a trail.

### 4. `sprint-harvester` + `memory-archivist`

**What they solve.** Two related but distinct problems. **Sprint-harvester** captures *durable* lessons (architectural decisions, host quirks, validation patterns) at end-of-sprint and proposes them for `LESSONS_LEARNED.md`. **Memory-archivist** captures *session-scoped* facts (this build command works, this quirk surprised me, this task is in flight) into the per-project `MEMORY.md`. Without both, sprints either burn out their hard-won wisdom (no harvest) or silently rewrite doctrine (no anchor).

**How they work.**
- `sprint-harvester` is invoked at end-of-sprint. It reads the diff, the validation artifacts, the handoff doc, and the session context. It produces normalized lesson entries with `Date / Context / Lesson / Architectural Decision / Evidence / Promotion Target / Status`. Output is appended to `LESSONS_LEARNED.md`. Doctrine in `AGENTS.md` / `CONOPS.md` is **never** silently rewritten.
- `memory-archivist` runs whenever a verified fact is worth carrying past the current session but is not durable enough for the lesson ledger. Three subcommands (`append`, `validate`, `summary`). Secrets-deny patterns at write time. Audit log at `<project>/.forge_state/archivist.log`. Wired into `teams/improvement-team.json` alongside the harvester.

| Skill | Scope | Target file | Discipline |
|---|---|---|---|
| `sprint-harvester` | Durable, broad lessons that may promote into doctrine | `docs/LESSONS_LEARNED.md` | Append-first; promotion-gated. |
| `memory-archivist` | Session-scoped state shared across hosts | `<project>/MEMORY.md` | Append-first; retention-bounded. |

**Why this shape.** Two tiers because durable doctrine and session-state are categorically different. A "this works on Tuesday" build command should not bind every future operator forever. A "Codex sandbox blocks `bwrap` loopback" finding should. Forcing both through the same tier would either lose durable lessons in noise or pollute lessons with trivia.

### 5. Live-hook-prober + tightened triad validator

**What they solve.** The Token-Burn Reconnaissance recon (2026-04-25) discovered that the Gemini event-name aliases in `omni_factory.py` were silently wrong. We had `preToolUse` mapped where Gemini's dispatcher expects `BeforeTool`. The triad validator passed for two full sprints because it did substring matching against the command path string ("guardian.sh" was indeed in the body) instead of verifying the rendered event key matched a real Gemini event name. **The hook was never firing on Gemini.** The validator was lying.

**How they work.** Two changes shipped in Sprint 1 (commits `f2cea42` + `a15200f`):

- `_EVENT_ALIASES["gemini"]` corrected: `pre_tool_use → BeforeTool`, `post_tool_use → AfterTool`, `session_start → SessionStart`, `stop → SessionEnd`.
- `hook_surface_for()` in the validator now also requires the per-host expected event key (`PreToolUse` / `pre_tool_use` / `BeforeTool`) to be a top-level key in the rendered hooks payload, not just a substring of any value somewhere in the JSON.
- A new skill `live-hook-prober` (`skills/global/live-hook-prober/prober.sh`) fires a real `git commit --no-verify` on the target host and observes whether the seeded guardian hook actually intercepts it.
- The triad validator gains a `--probe-invocations` flag (default OFF, opt-in because each probe is a real CLI call). When set, after the surface checks pass, it runs the live probe per host.

**Why this shape.** Surface validation that does substring matching against arbitrary JSON catches structural disappearance ("the hook record was deleted") but not semantic drift ("the hook record exists with a meaningless event name"). The strict fix is to enumerate the host's expected event vocabulary as a curated allow-list and require the rendered surface to use one of those exact keys. The pattern generalizes: any cross-host semantic surface (event names, sandbox markers, permission strings, MCP tool prefixes) needs a curated allow-list, not a loose substring or "contains" check.

The live probe gate is the deeper truth. The Gemini probe now has a real on-disk artifact (`runtime/validation/hook-probe/20260426-035313/gemini/`) showing `verdict: pass`, `observed: block`, `exit 0` — the first end-to-end runtime proof that the cross-host promise of the Omni-Factory is real on Gemini.

---

## Quickstart (5 minutes)

From a fresh Debian/Ubuntu or macOS workstation:

```bash
# 1. Get the folder onto the machine.
#    Either clone the repo, or unpack a suitcase bundle produced by:
#      ~/Projects/_agent_forge/scripts/factory-export.sh
#    on a canonical machine (creates agent-forge-suitcase-<timestamp>.tar.gz).

# 2. From inside the unpacked bundle, run the one-shot deploy + bootstrap.
./_agent_forge/scripts/deploy-and-bootstrap.sh
#   This deploys _agent_forge into ~/Projects, syncs the global Claude /
#   Codex / Gemini surfaces, and offers to run the workstation bootstrap
#   (which installs the three host CLIs).

# 3. Authenticate the host CLIs when prompted.
claude        # Anthropic browser login
codex --login # OpenAI Sign in with ChatGPT
gemini        # Google login (and accept workspace trust prompt)

# 4. Verify factory health (must EXIT=0 with no [FAIL] lines).
python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py

# 5. Bootstrap a new governed project.
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
#   The script auto-syncs Claude / Codex / Gemini project-local surfaces
#   and the universal MEMORY.md / .forge_state. No follow-up sync needed.

# 6. Triad-test the result. Surface check:
python3 scripts/validate-triad-runtime.py --project <your-project>
#   Expected: overall PASS, all three hosts hook+ mem+, expected count 29.

#    Live invocation gate (opt-in, slower, real CLI calls):
python3 scripts/validate-triad-runtime.py --project <your-project> --probe-invocations
#   Expected: gemini live+ (hook fires for real), codex live~ (sandbox-
#   escalated per doctrine), claude live~ (headless-permission-constraint
#   per documented limitation).
```

Steps 4 + 6 green = factory is production-ready on this machine.

**First time here and want a guided walkthrough?** Run `python3 ~/Projects/_agent_forge/skills/global/onboarding-guide/onboard.py tour` — five short sections in plain English, with experience-aware adaptations and a `--quick` 90-second summary mode. Read-only.

---

## Where to look next

Annotated map of the documentation tree, ordered roughly by what a new operator should read first.

### Tier 0 — entry points (read first)

| File | Why |
|---|---|
| `README.md` | You are here. |
| `AGENTS.md` | The multi-agent contract every host CLI auto-loads. Read before writing code or skills. |
| `CLAUDE.md` / `GEMINI.md` | Thin host boot adapters. They import the durable docs below. |

### Tier 1 — durable architecture & active state

| File | Why |
|---|---|
| `docs/CONOPS.md` | Durable architecture. Read before changing canonical sources. |
| `docs/HANDOFF.md` | Last-sprint summary. Read first if you've been away. |
| `docs/LESSONS_LEARNED.md` | Battle-tested workarounds, host quirks, promotion candidates. |
| `docs/HOST_INTEGRATIONS.md` | Per-host rendering rules and event-translation tables. |
| `docs/PATHFINDER_LEDGER.md` | Raw research archive. Read for *why*. |
| `docs/PATHFINDER_ROADMAP.md` | Actionable upgrades + capability backlog. Read for *what's next*. |
| `docs/SPRINT_BACKLOG.md` | The next three sprints with copy-pasteable Codex execution prompts. Read to *start working*. |
| `docs/TRIAD_RUNTIME_VALIDATION.md` | How to prove all three hosts work after a change. |
| `docs/NEXT_AGENT_PROMPT.md` | Pickup-prompt for a fresh agent picking up this thread. |

### Tier 2 — operator runbooks

| File | Why |
|---|---|
| `docs/VM_OPERATOR_RUNBOOK.md` | Step-by-step Debian VM bring-up. |
| `docs/WORKSTATION_BOOTSTRAP.md` | Fresh workstation setup. |
| `docs/FACTORY_SUITCASE.md` | How to package and move the factory between machines. |
| `docs/PORTABILITY.md` | What's safe to carry, what gets re-rendered. |
| `docs/OPERATOR_TEMPLATES.md` | Task-brief / evidence-pack / handoff templates. |

### Tier 3 — supporting docs

| File | Why |
|---|---|
| `docs/AGENTS_AND_TEAMS.md` | Skills vs agents vs teams concept layer. |
| `docs/TEAM_RUNBOOKS.md` / `docs/TEAM_SELECTION.md` | Which team for which job; how to drive each. |
| `docs/GOVERNANCE.md` | Governance audit + bootstrap + skill delivery rules. |
| `docs/EVALUATION.md` | Severity tiers, scorecard schema. |
| `docs/CONTEXT_ENGINEERING.md` | Compaction rules, model escalation. |
| `docs/TECH_DEBT.md` | Honest open-debt and recently-resolved-debt inventory. |
| `docs/PREMIUM_FACTORY_RUN.md` | Premium-tier prompt for factory improvements. |
| `docs/FUTURE_WORK_VM_ONBOARDING.md` | Historical record of the VM-onboarding remediation. |
| `docs/OPEN_MODEL_ROADMAP.md` | Phase 2 open-model expansion (Ollama / OpenRouter). |

---

## Extending the factory

Most extensions are one canonical edit + one sync.

### Add a new skill

```bash
# 1. Author the skill.
mkdir skills/global/<id>
$EDITOR skills/global/<id>/SKILL.md
#   See skills/global/skill-author/SKILL.md for the canonical frontmatter.

# 2. Re-render the registry.
python3 scripts/omni_factory.py render-registry > registry.json

# 3. Re-sync each governed project (or just the one you want).
python3 scripts/omni_factory.py sync-claude --project jarvis
python3 scripts/omni_factory.py sync-codex  --project jarvis
python3 scripts/omni_factory.py sync-gemini --project jarvis

# 4. Verify.
python3 scripts/verify-agent-forge.py
python3 scripts/validate-triad-runtime.py --project jarvis
```

The skill is now visible in all three hosts' CLI under the project.

### Add a new cross-host hook

Edit `policies/hooks.json` `shared` array. The schema is in `docs/HOST_INTEGRATIONS.md` § Unified Hook Lifecycle. The factory will translate the event into Claude `PreToolUse` / Codex `pre_tool_use` / Gemini `BeforeTool` automatically. Re-sync all governed projects, run the verifier and triad validator.

### Add a new memory section

Edit `policies/memory.json` `sections` array. Bump `version` if breaking. Re-sync all governed projects so `MEMORY.md` carries the new section anchor. The `memory-archivist` skill will recognize the new section automatically.

### Add a governed project

Add an entry to `projects.json` with `name`, `root`, and `required_files`. Run `./scripts/bootstrap-project.sh --name <name>` (or `--existing` if you're standardizing an existing repo). The script scaffolds the minimum footprint and auto-syncs all three host surfaces.

### Add a shared MCP server

Edit `global-mcp.json`. The MCP namespace prefixing renderer (Sprint 4 in `docs/SPRINT_BACKLOG.md`) is the canonical place for cross-host translation. Until that ships, the file is structurally wired but operationally untested with real entries.

---

## Governance discipline

Read these before contributing.

1. **Canonical-first.** You only ever edit the canonical sources (`skills/`, `teams/`, `policies/`, `projects.json`, `global-mcp.json`). Generated host surfaces (`<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/`) are never hand-edited.
2. **Triad gate is mandatory.** After any canonical change, `python3 scripts/validate-triad-runtime.py --project <name>` must pass. Surface check is the routine gate; `--probe-invocations` is the deeper gate run on demand. The structural verifier confirms files exist; only the triad validator confirms the host CLIs can actually reach them.
3. **Append-first lessons.** Doctrine in `AGENTS.md` and `docs/CONOPS.md` does not move silently. Findings start as `LESSONS_LEARNED.md` entries. Promotion is explicit and gated on durability + breadth + reuse across at least two sprints.
4. **Native boot files stay native.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` keep their host-specific names. Secondary docs may use host-agnostic names.
5. **The guardian is non-negotiable.** No `--no-verify`, no `--no-gpg-sign`, no force-push to protected branches, no `git reset --hard <ref>` against non-current branches. The `telemetry-guardian` hook blocks these on every host. Bypass is explicit (`AGENT_FORGE_GUARDIAN=off`) and audited (`~/.agent-forge/guardian.log`).
6. **Prefer narrow tool calls in agent sessions.** Compound `&&`/`;` shell commands with thick mixed output are bridge-fragile and produce silent tool-result delivery stalls in agent harnesses. Use one narrow call per question. Reserve compound chains for short related steps where rolling back partial completion is fine.
7. **Do not invoke long-running CLIs through an agent harness's bash tool.** Running `claude -p`, `codex exec`, or `gemini -p` from within another agent session causes leftover-subprocess-tree stalls (the live-hook-prober is the canonical example). Run them from a real terminal or as a scheduled Routine.

---

## Repository layout

```
_agent_forge/
├── README.md                     ← you are here
├── AGENTS.md                     ← multi-agent contract (auto-loaded by all hosts)
├── CLAUDE.md / GEMINI.md         ← thin host boot adapters
│
├── policies/
│   ├── hooks.json                ← canonical hook schema (renders to all three hosts)
│   └── memory.json               ← canonical memory section schema
│
├── projects.json                 ← governed project catalog
├── global-mcp.json               ← shared MCP server inventory (intentionally empty until first server)
├── registry.json                 ← generated compatibility output (do not hand-edit)
│
├── skills/
│   ├── global/                   ← portable cross-project skills (29 of them)
│   │   ├── branch-finisher/
│   │   ├── brand-guardian/
│   │   ├── code-review-doctrine/
│   │   ├── company-onboarder/
│   │   ├── context-engineer/
│   │   ├── corporate-controller/
│   │   ├── doctrine-review/      (slash commands referenced from team manifests)
│   │   ├── evidence-packager/
│   │   ├── execution-planner/
│   │   ├── infra-architect/
│   │   ├── legal-counsel/
│   │   ├── live-hook-prober/     ← deepest validation gate (Sprint 1, 2026-04-26)
│   │   ├── memory-archivist/     ← session-scoped state writer (Sprint Apr-25)
│   │   ├── multi-agent-governor/
│   │   ├── portability-auditor/
│   │   ├── project-bootstrap/
│   │   ├── quality-gate/
│   │   ├── root-cause-analyst/
│   │   ├── skill-author/
│   │   ├── spec-architect/
│   │   ├── sprint-harvester/     ← durable lesson harvester
│   │   ├── subagent-dispatcher/
│   │   ├── tdd-engineer/
│   │   ├── telemetry-guardian/   ← universal pre-tool veto
│   │   └── verification-gate/
│   └── projects/<project>/       ← project-local skills
│
├── teams/                        ← canonical team manifests (planning, delivery, assessment, improvement, etc.)
│
├── scripts/
│   ├── omni_factory.py           ← the canonical generator
│   ├── verify-agent-forge.py     ← structural verifier
│   ├── validate-triad-runtime.py ← runtime gate (CLI enumeration + hook + memory + live invocation)
│   ├── validate-codex-runtime.py ← strict Codex-only probe
│   ├── bootstrap-workstation.sh  ← installs Claude / Codex / Gemini CLIs
│   ├── bootstrap-project.sh      ← scaffolds a new governed project
│   ├── deploy-and-bootstrap.sh   ← one-shot operator path from a suitcase bundle
│   ├── deploy-factory.sh         ← deploys _agent_forge into ~/Projects
│   ├── factory-export.sh         ← builds a portable suitcase bundle
│   └── sync-claude-adapters.sh / sync-codex-skills.sh / sync-gemini-adapters.sh
│
├── runtime/
│   ├── validation-matrix.json    ← coverage ledger; survives across runs
│   └── validation/               ← timestamped probe artifacts (gitignored except matrix)
│
├── exports/                      ← suitcase bundles (gitignored)
│
└── docs/                         ← architecture, runbooks, lessons, roadmap, sprint backlog
    ├── CONOPS.md
    ├── HANDOFF.md
    ├── LESSONS_LEARNED.md
    ├── HOST_INTEGRATIONS.md
    ├── PATHFINDER_LEDGER.md       ← raw research archive
    ├── PATHFINDER_ROADMAP.md      ← actionable upgrades + capability backlog
    ├── SPRINT_BACKLOG.md          ← Codex hand-off prompts
    ├── TRIAD_RUNTIME_VALIDATION.md
    ├── TECH_DEBT.md
    ├── NEXT_AGENT_PROMPT.md
    ├── VM_OPERATOR_RUNBOOK.md
    ├── WORKSTATION_BOOTSTRAP.md
    ├── FACTORY_SUITCASE.md
    ├── PORTABILITY.md
    ├── OPERATOR_TEMPLATES.md
    ├── AGENTS_AND_TEAMS.md
    ├── TEAM_RUNBOOKS.md
    ├── TEAM_SELECTION.md
    ├── GOVERNANCE.md
    ├── EVALUATION.md
    ├── CONTEXT_ENGINEERING.md
    ├── PREMIUM_FACTORY_RUN.md
    ├── FUTURE_WORK_VM_ONBOARDING.md
    └── OPEN_MODEL_ROADMAP.md
```

---

## Honest limitations

The factory is in a strong position on the canonical-first axis. It is honestly weaker on the runtime-orchestration axis. These are the limitations a fresh operator should know about:

1. **Codex sandbox is bubblewrap-fragile on Linux.** `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted` and `needs access to create user namespaces` are recurring errors. The triad validator escalates to filesystem-evidence per documented doctrine when this fires; the live invocation probe escalates to `sandbox_blocked`. This is documented and accepted.
2. **Headless `claude -p` cannot live-probe hooks.** With `--dangerously-skip-permissions`, the entire pre-tool hook system is bypassed (false positive). Without it, the CLI hangs waiting on a permission prompt that has no interactive stdin to deliver. The live-hook-prober treats this as `escalated`. Real Claude live-probing requires either an interactive session or a pre-approved permission rule for the test command — both out of scope for an automated triad gate. Roadmap fix: Capability B4 (`forge-shell`) provides the persistent shell context that closes this.
3. **No real shared MCP server has landed yet.** `global-mcp.json` is intentionally empty until the first real shared server lands. The MCP renderer is structurally wired but operationally unproven with real entries. Sprint 4 (Architectural Upgrade A3) is the moment this becomes real.
4. **Cross-host auto-memory bridge is not yet shipped.** `MEMORY.md` is the canonical cross-host file, but the bridge to each host's *native* auto-memory store is not built. A fact Claude saves into its own auto-memory does not propagate to Gemini or to our canonical file. Sprint 3 (Capability B2 `memory-bridge`) is the fix.
5. **Tool-result delivery stalls** in agent harnesses are real. Two distinct mechanisms have been observed: bridge fragility on bulky compound-bash output, and leftover-subprocess-tree leaks on long-running CLI invocations. The mitigation rules are in §Governance discipline.
6. **No git remote yet.** The factory is local-only. The watchdog routine documented in `docs/TECH_DEBT.md` is blocked on a public git remote being available.
7. **Real Debian VM and macOS suitcase proofs still pending.** The path is structurally wired but has not yet been exercised end-to-end on a fresh machine by a real operator.

---

## FAQ — common stalls and quick answers

**The verifier passed but a sync didn't write the right file.**
The structural verifier checks file presence and schema, not generated content correctness. Run `python3 scripts/validate-triad-runtime.py --project <name>` — that's the runtime gate.

**The triad validator passed but I think a hook isn't firing.**
Run with `--probe-invocations`. Surface check confirms the rendered file is correct. The live invocation gate fires a real test command and observes whether the hook actually intercepts it. The C1 Gemini bug shipped because surface check passed but live probe would have caught it.

**A Bash call has been "running" for 5+ minutes with no token motion.**
This is almost certainly a stuck tool-result delivery, not actual reasoning. Interrupt with "are you stuck?" — the agent re-grounds at near-zero cost on the next turn. The working tree is preserved.

**A `claude -p` / `codex exec` / `gemini -p` invocation is hanging.**
Don't run long-running CLI tool calls transitively through another agent's bash tool. Run them from a real terminal or schedule them as Routines. See the leftover-subprocess-tree class in §Governance discipline.

**I want to run live-hook-prober.**
From a real terminal:

```bash
bash ~/Projects/_agent_forge/skills/global/live-hook-prober/prober.sh \
  --host gemini --project ~/Projects/jarvis \
  --command "git commit --no-verify -m probe" --expect block
```

Returns single-line JSON. Exit 0 = pass.

**I want to bypass the guardian for one session.**
`export AGENT_FORGE_GUARDIAN=off` for that shell. Every bypass is logged to `~/.agent-forge/guardian.log` so the operator and any auditor can see it. Do not commit code that auto-sets this variable.

**Where do I start if I'm picking this up cold?**
1. Read `README.md` (this file).
2. Read `AGENTS.md`.
3. Read `docs/HANDOFF.md` for what just shipped.
4. Read `docs/PATHFINDER_ROADMAP.md` for what's next.
5. Read `docs/SPRINT_BACKLOG.md` for the exact next sprint's execution prompt.
6. Run the Quickstart commands above.
7. Look at `docs/PATHFINDER_LEDGER.md` only if you need *why* — it's the raw research archive.

**Where does Codex start for the next sprint?**
`docs/SPRINT_BACKLOG.md`. The Sprint 2 prompt is copy-pasteable into a Codex session. It commands Codex to read the right docs first, web-search to verify current API specifics, follow the architectural rules, and stop at the defined exit gates.
