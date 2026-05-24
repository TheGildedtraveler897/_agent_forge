# Agent Forge

**A portable governance factory that gives three AI coding command-line tools — Claude Code, OpenAI Codex, and Gemini CLI — equivalent skills, identical safety guardrails, and a unified memory layer (native on Claude, sidecar bridges on Codex and Gemini), generated outward from one canonical source of truth.**

You write a skill, a hook, or a memory section *once*, in `_agent_forge/`. The factory translates it into each host's native shape and validates that all three host CLIs can actually see and use it. No more maintaining three parallel sets of prompts, hooks, and memory files. No vendor lock-in. No silent drift between hosts.

This README is written for two audiences: someone new to "agentic CLI workflows" who wants to understand what this is and why it exists, and a senior architect who wants the concrete component map and current state. Section headers tell you which audience the section is aimed at.

---

## Table of contents

1. [What this is, in one paragraph](#what-this-is-in-one-paragraph) — start here
2. [Mental model](#mental-model) — the diagram in markdown
3. [What you get today](#what-you-get-today) — capability inventory
4. [For beginners — what is an agentic workflow](#for-beginners--what-is-an-agentic-workflow)
5. [For senior architects — the component map](#for-senior-architects--the-component-map)
6. [Quickstart (5 minutes)](#quickstart-5-minutes)
7. [Where to look next](#where-to-look-next) — annotated doc map
8. [Extending the factory](#extending-the-factory)
9. [Governance discipline](#governance-discipline)
10. [Repository layout](#repository-layout)
11. [Honest limitations](#honest-limitations)
12. [FAQ — common stalls and quick answers](#faq--common-stalls-and-quick-answers)

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

## Multi-Agent Workflows

Three agents, one plan.

Claude can spec a feature with `spec-architect`, which writes the plan
to `docs/plans/<branch-slug>.md` with status frontmatter. The plan's
existence and status get pinned to `MEMORY.md`'s `active_tasks`
section, which all three hosts auto-load on session start.

Switch to Codex in the same project. Codex reads `MEMORY.md`, sees the
plan pointer, opens the plan file, and executes the task list with
`tdd-engineer`. Test results and decisions append back to `MEMORY.md`.

Switch to Gemini. Gemini reads the updated `MEMORY.md` plus the diff,
runs `paranoid-reviewer` or `verification-gate`, and gates the merge.

No manual context copy-paste. No three separate prompts of "here's
what we did." The canonical files are the handoff artifact.

What this is NOT (yet): automatic agent invocation. You still start
each host's CLI manually. The factory keeps state in sync; it does
not orchestrate which host runs next. See `subagent-dispatcher/SKILL.md`
for the operator-driven dispatch pattern.

---

## What you get today

| Surface | State | Detail |
|---|---|---|
| **Canonical skills library** | ✅ Production | Workflow discipline (spec → plan → TDD → review → verify → finish), domain experts (legal, infra, brand, finance), meta-skills (skill-author, sprint-harvester, memory-archivist, telemetry-guardian, live-hook-prober). All shipped as portable `SKILL.md` under `skills/global/`. |
| **Governed project model** | ✅ Production | Empty by default. Add your first with `./scripts/bootstrap-project.sh --name <name>` — the bootstrap creates the minimum required files and immediately syncs all three host-native surfaces. |
| **Universal pre-tool guardrail** | ✅ Production | `telemetry-guardian` blocks destructive shell commands before they run. Fires on every host. Bypass is auditable. |
| **Universal cross-host memory layer** | ✅ Production | `MEMORY.md` + `.forge_state/` per project. Five sections (build commands, project quirks, active tasks, recent decisions, known failures). All three hosts read and write the same file. |
| **Append-first knowledge anchor** | ✅ Production | `docs/LESSONS_LEARNED.md`. Doctrine never moves silently. Bounded decay via the `lesson-distiller` skill once entries are promoted. |
| **Triad runtime validator** | ✅ Production | Asks each host's CLI to enumerate skills + verifies hook surface + verifies memory surface + verifies MCP surface. Live invocation probe gate via `--probe-invocations`. |
| **Codex sandbox-aware probe** | ✅ Production | When Codex's bubblewrap blocks shell inspection, the validator escalates to filesystem evidence per documented doctrine. |
| **Suitcase / portability** | ✅ Production | One-shot export + deploy + bootstrap script chain. Move the factory between machines without carrying secrets or per-machine residue. |

---

## Honest limitations

The factory is in a strong position on the canonical-first axis. It is honestly weaker on the runtime-orchestration axis. These are the limitations a fresh operator should know about:

1. **Codex sandbox is bubblewrap-fragile on Linux.** `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted` and `needs access to create user namespaces` are recurring errors. The triad validator escalates to filesystem-evidence per documented doctrine when this fires.
2. **Headless `claude -p` cannot live-probe hooks.** With `--dangerously-skip-permissions`, the entire pre-tool hook system is bypassed (false positive). Without it, the CLI hangs waiting on a permission prompt that has no interactive stdin to deliver. The live-hook-prober treats this as `escalated`. Real Claude live-probing requires either an interactive session or a pre-approved permission rule for the test command.
3. **Host MCP management UIs are not parity proof.** `global-mcp.json` ships with the seeded local `forge-factory` server, and `mcp_pass` verifies rendered aliases plus direct stdio `tools/list`. Host-native `mcp get/list` commands still differ enough that they remain secondary spot checks.
4. **The memory bridge is conservative by design.** Claude has a true native auto-memory path, while Codex and Gemini use project sidecars because current host docs do not expose equivalent stable project fact-memory stores. The sidecars are evidence, not claims of native auto-load parity.
5. **Tool-result delivery stalls** in agent harnesses are real. Two distinct mechanisms have been observed: bridge fragility on bulky compound-bash output, and leftover-subprocess-tree leaks on long-running CLI invocations. Mitigation rules are in §Governance discipline.
6. **Native Windows bootstrap of host CLIs is operator-driven.** The factory's skills and Python helpers work on native Windows Claude Code; installing the Claude CLI on Windows is currently a user-driven step. `bootstrap-workstation.sh` covers Linux and macOS-via-MacPorts.

---

## For beginners — what is an agentic workflow

If you've never used Claude Code, OpenAI Codex, or Gemini CLI before, here's the quick mental model.

An **agentic CLI** is a command-line program that talks to a large language model and can also read your files, edit code, and run shell commands on your behalf. The three best-known are:

- **Claude Code** (Anthropic) — the most polished IDE/terminal hybrid; auto-loads `CLAUDE.md` and project skills.
- **OpenAI Codex** (the CLI tool) — terminal-first, sandboxed by default; auto-loads `AGENTS.md`.
- **Gemini CLI** (Google) — terminal-first; auto-loads `GEMINI.md`; bundles workspace trust prompts.

Each of these hosts has its own dialect for the same primitives:

- **Skills / agents** — named, reusable prompt-and-tool bundles. Claude calls them "skills" and "subagents"; Codex calls them "skills" / "subagents"; Gemini calls them "agents" / "commands" / "skills."
- **Hooks** — programs the host CLI runs automatically at lifecycle events (before/after a tool call, on session start/stop, on user prompt submit). Claude, Codex, and Gemini each use different event names and config files.
- **Memory** — persistent project state that the model can read between sessions. Each host has its own format.
- **MCP servers** — Model Context Protocol; standardized way to expose external tools (DBs, APIs, file systems) to any host.

**Agent Forge holds the canonical authoring layer** for all of this. You write a skill once in `skills/global/<id>/SKILL.md`. The factory generates the Claude version, the Codex version, and the Gemini version. The triad validator asks each host's actual CLI "do you see this skill?" If any host says no, the change is not green.

---

## For senior architects — the component map

### Canonical authoring sources

| File | Purpose | Schema |
|---|---|---|
| `skills/global/<id>/SKILL.md` | Cross-project capability definition | Frontmatter: `name`, `description`, `capability_class` (workflow / expert), `targets` (host list), `delivery_projects` (which projects get it; `[*]` or omit for all), `model_tier`, `context_cost`. Body = durable instruction contract. |
| `skills/projects/<project>/<id>/SKILL.md` | Project-local capability | Same shape; `project: <name>` set automatically. |
| `teams/<name>.json` | Multi-agent team manifest | `roles`, `collapse_condition`, `escalate_condition`, `handoff_artifacts`, per-host `preferred_entries`. |
| `projects.json` | Governed project catalog | List of `{name, root, required_files}`. Empty on a fresh install. |
| `global-mcp.json` | Shared MCP server inventory | v2: `servers` map with semantic `prefix`, host-safe aliases, transport/auth/trust metadata, project routing, and tool filters. Seeded with `forge-factory`. |
| `policies/hooks.json` | Hook lifecycle records | v3: `shared[]` + per-host arrays of `{id, event, matcher, handler, targets, timeout_ms, status_message}`. |
| `policies/memory.json` | Memory section schema | v2: `sections[]`, `retention`, `secrets_policy`, and a `bridge` block for host-local memory synchronization. |
| `policies/distillation.json` | Bounded-decay retention contract | v1: per-target retention rules for `LESSONS_LEARNED.md` and `HANDOFF.md`. |

### Generated host surfaces

| Host | User-home surfaces | Per-project surfaces |
|---|---|---|
| **Claude** | `~/.claude/{agents,commands,skills}` | `<project>/.claude/{agents,commands,skills,settings.json}`, `<project>/.mcp.json` |
| **Codex** | `~/.agents/skills` | `<project>/.agents/skills`, `<project>/.codex/{agents,config.toml,hooks.json}` |
| **Gemini** | `~/.gemini/{agents,commands}` plus `~/.agents/skills`, `~/.gemini/GEMINI.md` | `<project>/GEMINI.md`, `<project>/.gemini/{agents,commands,skills,settings.json}` |
| **Cross-host** | n/a | `<project>/MEMORY.md`, `<project>/.forge_state/{README.md,manifest.json,archivist.log,bridge.json,bridge.log}` |

### The validation pyramid

```
Level 3 — Live invocation gate (deepest, slowest, most truthful)
  validate-triad-runtime.py --probe-invocations
  Fires real tool calls on each host CLI, observes whether hooks fire.
  Catches host-native semantic drift.

Level 2 — Triad surface gate (mandatory after every canonical change)
  validate-triad-runtime.py --project <name>
  Asks each host's CLI to enumerate skills; checks hook, memory, bridge, and MCP surfaces.
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
| `docs/HANDOFF.md` | Rolling operator handoff log. |
| `docs/LESSONS_LEARNED.md` | Append-first knowledge anchor. |
| `docs/TRIAD_RUNTIME_VALIDATION.md` | The live-validation runbook. |
| `docs/TECH_DEBT.md` | Honest open-debt and recently-resolved-debt inventory. |
| `docs/QUICKSTART.md` | First-run flow for a fresh operator. |

### Recent architectural decisions worth knowing

1. **Canonical-first is the only edit point.** `registry.json` is generated compatibility output, not a source of truth. Generated host surfaces under `<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/` are never hand-edited.
2. **Append-first lessons.** Doctrine in `AGENTS.md` and `docs/CONOPS.md` does not move silently. Every change starts as a `LESSONS_LEARNED.md` entry, gets reviewed, and is promoted into doctrine only when durable + broad. Bounded decay via `lesson-distiller` once promoted.
3. **Triad gate is mandatory.** After any canonical change, `validate-triad-runtime.py` must pass. The structural verifier is necessary but insufficient — only the runtime gate confirms the host CLIs can actually reach what we shipped.
4. **Curated allow-lists for cross-host semantics.** Whenever the factory crosses a host-native semantic boundary (event names, sandbox markers, permission strings, MCP tool prefixes), the validator checks against a curated allow-list of known-valid native values, not a substring match.
5. **Native boot files stay native.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` keep their host-specific names. Secondary docs were renamed to host-agnostic forms; boot files were left alone.

---

## Quickstart (5 minutes)

From a fresh Debian/Ubuntu, macOS (MacPorts), or Windows (native) workstation:

```bash
# 1. Get the folder onto the machine.
#    Either clone the repo, or unpack a suitcase bundle produced by:
#      ./scripts/factory-export.sh --mode onboarding
#    on a canonical machine.

# 2. Deploy the framework into your user home.
#    Linux / macOS:
./_agent_forge/scripts/deploy-factory.sh
#    Windows (native PowerShell, no WSL):
pwsh -File .\_agent_forge\scripts\deploy-factory.ps1

# 3. (Optional) Install the host CLIs if you don't already have them.
./_agent_forge/scripts/bootstrap-workstation.sh
#    Note: macOS path requires MacPorts. Windows skips CLI install — install Claude Code yourself.

# 4. Authenticate the host CLIs.
claude        # Anthropic browser login
codex --login # OpenAI Sign in with ChatGPT (optional)
gemini        # Google login (optional)

# 5. Verify factory health (must EXIT=0 with no [FAIL] lines).
python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py

# 6. Bootstrap your first governed project.
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name my-first-app

# 7. Triad-test the result.
python3 scripts/validate-triad-runtime.py --project my-first-app
```

**First time here and want a guided walkthrough?** Inside Claude Code, invoke the `onboarding-guide` skill — five short sections in plain English, with experience-aware adaptations. Read-only.

---

## Where to look next

Annotated map of the documentation tree, ordered roughly by what a new operator should read first.

### Tier 0 — entry points (read first)

| File | Why |
|---|---|
| `README.md` | You are here. |
| `docs/QUICKSTART.md` | First-run flow in one page. |
| `AGENTS.md` | The multi-agent contract every host CLI auto-loads. Read before writing code or skills. |
| `CLAUDE.md` / `GEMINI.md` | Thin host boot adapters. They import the durable docs below. |

### Tier 1 — durable architecture

| File | Why |
|---|---|
| `docs/CONOPS.md` | Durable architecture. Read before changing canonical sources. |
| `docs/HOST_INTEGRATIONS.md` | Per-host rendering rules and event-translation tables. |
| `docs/HANDOFF.md` | Rolling operator handoff log. |
| `docs/LESSONS_LEARNED.md` | Append-first knowledge anchor. |
| `docs/TRIAD_RUNTIME_VALIDATION.md` | How to prove all three hosts work after a change. |

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
python3 scripts/omni_factory.py sync-claude --project <name>
python3 scripts/omni_factory.py sync-codex  --project <name>
python3 scripts/omni_factory.py sync-gemini --project <name>

# 4. Verify.
python3 scripts/verify-agent-forge.py
python3 scripts/validate-triad-runtime.py --project <name>
```

The skill is now visible in all three hosts' CLI under the project.

### Add a new cross-host hook

Edit `policies/hooks.json` `shared` array. The schema is in `docs/HOST_INTEGRATIONS.md` § Unified Hook Lifecycle. The factory will translate the event into Claude `PreToolUse` / Codex `PreToolUse` / Gemini `BeforeTool` automatically. Re-sync all governed projects, run the verifier and triad validator.

### Add a new memory section

Edit `policies/memory.json` `sections` array. Bump `version` if breaking. Re-sync all governed projects so `MEMORY.md` carries the new section anchor. The `memory-archivist` skill will recognize the new section automatically.

### Add a governed project

Add an entry to `projects.json` with `name`, `root`, and `required_files`. Run `./scripts/bootstrap-project.sh --name <name>` (or `--existing` if you're standardizing an existing repo). The script scaffolds the minimum footprint and auto-syncs all three host surfaces.

### Add a shared MCP server

Edit `global-mcp.json`. The MCP namespace prefixing renderer translates semantic prefixes into host-safe server aliases and enforces trust-gated project routing. The seeded local `forge-factory` stdio server is the reference shape for adding more shared servers without credentials.

---

## Governance discipline

Read these before contributing.

1. **Canonical-first.** You only ever edit the canonical sources (`skills/`, `teams/`, `policies/`, `projects.json`, `global-mcp.json`). Generated host surfaces (`<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/`) are never hand-edited.
2. **Triad gate is mandatory.** After any canonical change, `python3 scripts/validate-triad-runtime.py --project <name>` must pass. Surface check is the routine gate; `--probe-invocations` is the deeper gate run on demand.
3. **Append-first lessons.** Doctrine in `AGENTS.md` and `docs/CONOPS.md` does not move silently. Findings start as `LESSONS_LEARNED.md` entries. Promotion is explicit and gated on durability + breadth + reuse across at least two sprints.
4. **Native boot files stay native.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` keep their host-specific names. Secondary docs may use host-agnostic names.
5. **The guardian is non-negotiable.** No `--no-verify`, no `--no-gpg-sign`, no force-push to protected branches, no `git reset --hard <ref>` against non-current branches. The `telemetry-guardian` hook blocks these on every host. Bypass is explicit (`AGENT_FORGE_GUARDIAN=off`) and audited (`~/.agent-forge/guardian.log`).
6. **Prefer narrow tool calls in agent sessions.** Compound `&&`/`;` shell commands with thick mixed output are bridge-fragile. Use one narrow call per question.
7. **Do not invoke long-running CLIs through an agent harness's bash tool.** Running `claude -p`, `codex exec`, or `gemini -p` from within another agent session causes leftover-subprocess-tree stalls. Run them from a real terminal.

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
│   ├── memory.json               ← canonical memory section schema
│   └── distillation.json         ← bounded-decay retention contract
│
├── projects.json                 ← governed project catalog (empty on fresh install)
├── global-mcp.json               ← shared MCP server inventory
├── registry.json                 ← generated compatibility output (do not hand-edit)
│
├── skills/
│   ├── global/                   ← portable cross-project skills
│   │   ├── branch-finisher/
│   │   ├── brand-guardian/
│   │   ├── code-review-doctrine/
│   │   ├── company-onboarder/
│   │   ├── context-engineer/
│   │   ├── corporate-controller/
│   │   ├── evidence-packager/
│   │   ├── execution-planner/
│   │   ├── handoff-archiver/
│   │   ├── infra-architect/
│   │   ├── legal-counsel/
│   │   ├── lesson-distiller/
│   │   ├── live-hook-prober/
│   │   ├── memory-archivist/
│   │   ├── memory-bridge/
│   │   ├── multi-agent-governor/
│   │   ├── onboarding-guide/
│   │   ├── portability-auditor/
│   │   ├── project-bootstrap/
│   │   ├── prompt-auto-activator/
│   │   ├── quality-gate/
│   │   ├── quick-task-runner/
│   │   ├── root-cause-analyst/
│   │   ├── skill-author/
│   │   ├── spec-architect/
│   │   ├── sprint-harvester/
│   │   ├── subagent-dispatcher/
│   │   ├── tdd-engineer/
│   │   ├── telemetry-guardian/
│   │   ├── token-optimizer/
│   │   ├── verification-gate/
│   │   └── workstream-manager/
│   └── projects/                 ← project-local skills (empty on fresh install)
│
├── teams/                        ← canonical team manifests
│
├── scripts/
│   ├── omni_factory.py           ← the canonical generator
│   ├── verify-agent-forge.py     ← structural verifier
│   ├── validate-triad-runtime.py ← runtime gate (CLI enumeration + hook + memory + bridge + MCP)
│   ├── validate-codex-runtime.py ← strict Codex-only probe
│   ├── bootstrap-workstation.sh  ← installs Claude / Codex / Gemini CLIs
│   ├── bootstrap-project.sh      ← scaffolds a new governed project (POSIX)
│   ├── bootstrap-project.ps1     ← Windows-native project bootstrap
│   ├── deploy-and-bootstrap.sh   ← one-shot operator path from a suitcase bundle
│   ├── deploy-factory.sh         ← deploys _agent_forge into ~/Projects (POSIX)
│   ├── deploy-factory.ps1        ← Windows-native user-home deploy
│   ├── factory-export.sh         ← builds a portable suitcase bundle
│   └── sync-claude-adapters.sh / sync-codex-skills.sh / sync-gemini-adapters.sh
│
├── runtime/
│   ├── validation-matrix.json    ← coverage ledger
│   └── validation/               ← timestamped probe artifacts (gitignored except matrix)
│
└── docs/                         ← architecture, runbooks, lessons
    ├── CONOPS.md
    ├── HANDOFF.md
    ├── LESSONS_LEARNED.md
    ├── HOST_INTEGRATIONS.md
    ├── TRIAD_RUNTIME_VALIDATION.md
    ├── TECH_DEBT.md
    ├── QUICKSTART.md
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
    └── FUTURE_WORK_VM_ONBOARDING.md
```

---

## FAQ — common stalls and quick answers

**The verifier passed but a sync didn't write the right file.**
The structural verifier checks file presence and schema, not generated content correctness. Run `python3 scripts/validate-triad-runtime.py --project <name>` — that's the runtime gate.

**The triad validator passed but I think a hook isn't firing.**
Run with `--probe-invocations`. Surface check confirms the rendered file is correct. The live invocation gate fires a real test command and observes whether the hook actually intercepts it.

**A Bash call has been "running" for 5+ minutes with no token motion.**
This is almost certainly a stuck tool-result delivery, not actual reasoning. Interrupt with "are you stuck?" — the agent re-grounds at near-zero cost on the next turn. The working tree is preserved.

**A `claude -p` / `codex exec` / `gemini -p` invocation is hanging.**
Don't run long-running CLI tool calls transitively through another agent's bash tool. Run them from a real terminal or schedule them as Routines.

**I want to run live-hook-prober.**
From a real terminal:

```bash
python3 ~/Projects/_agent_forge/skills/global/live-hook-prober/prober.py \
  --host gemini --project ~/Projects/<your-project> \
  --command "git commit --no-verify -m probe" --expect block
```

Returns single-line JSON. Exit 0 = pass.

**I want to bypass the guardian for one session.**
`export AGENT_FORGE_GUARDIAN=off` for that shell. Every bypass is logged to `~/.agent-forge/guardian.log` so the operator and any auditor can see it. Do not commit code that auto-sets this variable.

**Where do I start if I'm picking this up cold?**
1. Read `README.md` (this file).
2. Read `docs/QUICKSTART.md` for the first-run flow.
3. Read `AGENTS.md` for the multi-agent contract.
4. Run the Quickstart commands above.
5. Inside Claude Code, invoke the `onboarding-guide` skill for an interactive tour.
