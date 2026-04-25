# Agent Forge

A portable governance factory that gives Claude Code, OpenAI Codex, and Gemini CLI the **same skills, the same guardrails, and the same shared memory** under one canonical source of truth. Author once in `_agent_forge/`; the factory generates host-native delivery surfaces outward.

## What you get

- **28 governed skills** — workflow discipline (spec → plan → TDD → review → verify → finish), domain experts (legal, infra, brand, finance), and meta-skills (`skill-author`, `sprint-harvester`, `memory-archivist`, `telemetry-guardian`).
- **Triad runtime validator** — proves all three host CLIs can actually see what the factory shipped, not just that the files exist on disk. Codex sandbox-aware: escalates to filesystem evidence when bubblewrap blocks shell inspection.
- **Universal state layer** — `MEMORY.md` + `.forge_state/` per project. Five canonical sections (build commands, project quirks, active tasks, recent decisions, known failures) shared across all three hosts so an insight in Claude is visible from Codex and Gemini.
- **Universal pre-tool guardrail** — `telemetry-guardian` blocks destructive shell invocations (`--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777) before they run, on every host.
- **Append-first knowledge anchor** — `docs/LESSONS_LEARNED.md` records hard-won lessons before any doctrine is promoted; doctrine never moves silently.
- **Six governed projects already wired** — `jarvis`, `RoboNaaz`, `ZorroClaw`, `homelab`, `ZorroForge/factory`, `playlist-archive`. Add yours with one bootstrap command.

## Who this is for

- Engineers who run multiple AI coding CLIs and don't want to maintain three separate sets of skills, hooks, and memory.
- Operators standing up a new machine, VM, or fresh project who want a one-shot deploy + bootstrap path instead of a runbook with hidden order-of-operations.
- Teams who want every host to enforce the same safety rules and read from the same shared state without trusting a vendor lock-in.

## Quickstart (5 minutes)

From a fresh Debian/Ubuntu or macOS workstation:

1. **Get the folder onto the machine.** Either clone the repo or unpack a suitcase bundle (`scripts/factory-export.sh` from a canonical machine produces `agent-forge-suitcase-<timestamp>.tar.gz`).
2. **One-shot deploy + bootstrap** from inside the unpacked bundle:
   ```bash
   ./_agent_forge/scripts/deploy-and-bootstrap.sh
   ```
   This deploys `_agent_forge` into `~/Projects`, syncs Claude/Codex/Gemini surfaces, and offers to run workstation bootstrap (installs the three CLIs).
3. **Authenticate the CLIs** when prompted (`claude`, `codex --login`, `gemini`). See `docs/WORKSTATION_BOOTSTRAP.md` for org/proxy edge cases.
4. **Verify factory health:**
   ```bash
   python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py
   ```
   Must EXIT=0 with no `[FAIL]` lines.
5. **Bootstrap your first project:**
   ```bash
   cd ~/Projects/_agent_forge
   ./scripts/bootstrap-project.sh --name <your-project>
   ```
   The script auto-syncs Claude/Codex/Gemini project surfaces. No follow-up `sync-*.sh` required.
6. **Triad-test the result** (proves all three hosts can see the new project's skills, hooks, and memory layer):
   ```bash
   python3 scripts/validate-triad-runtime.py --project <your-project>
   ```
   Must show `overall_pass: true` with `hook_pass: true memory_pass: true` for Claude, Codex, and Gemini.

If both step 4 and step 6 are green, the factory is production-ready on this machine.

## Where to look next

- **`AGENTS.md`** — the multi-agent contract. Claude, Codex, and Gemini all auto-load it. Read first if you'll write code or skills.
- **`CLAUDE.md` / `GEMINI.md`** — thin host boot adapters. They import `AGENTS.md`, `docs/CONOPS.md`, `docs/HANDOFF.md`, `docs/LESSONS_LEARNED.md`.
- **`docs/CONOPS.md`** — durable architecture. Read before changing canonical sources.
- **`docs/HANDOFF.md`** — what changed last sprint, in chronological order. Read first if you've been away for a while.
- **`docs/PATHFINDER_ROADMAP.md`** — what's shipped vs what's next on the roadmap.
- **`docs/HOST_INTEGRATIONS.md`** — how the omni-factory translates canonical sources into Claude/Codex/Gemini-native shapes (skills, hooks, MCP, memory).
- **`docs/TRIAD_RUNTIME_VALIDATION.md`** — how to prove all three hosts work after a change.
- **`docs/LESSONS_LEARNED.md`** — battle-tested workarounds, host quirks, and promotion candidates.
- **`docs/VM_OPERATOR_RUNBOOK.md`** / **`docs/WORKSTATION_BOOTSTRAP.md`** — step-by-step operator paths for Debian VM and fresh workstation.
- **`docs/FACTORY_SUITCASE.md`** — how to package and move the factory between machines.

## Extending it

- **Add a new skill:** start from `skills/global/skill-author/SKILL.md` (the meta-skill that enforces canonical Omni-Factory frontmatter).
- **Add a new cross-host hook:** edit `policies/hooks.json` (schema in `docs/HOST_INTEGRATIONS.md` § Unified Hook Lifecycle). Hooks are written once and rendered into Claude `.claude/settings.json`, Codex `.codex/hooks.json`, and Gemini `.gemini/settings.json` automatically.
- **Add a new memory section:** edit `policies/memory.json` (schema in `docs/HOST_INTEGRATIONS.md` § Universal State Layer). The schema renders into `<project>/MEMORY.md` for every governed project.
- **Add a governed project:** add it to `projects.json`, then run the bootstrap command above.
- **Add a shared MCP server:** edit `global-mcp.json` (currently empty by design until the first real shared server is added).

## Governance discipline (read before contributing)

- **Canonical sources are first.** Edit `skills/`, `teams/`, `policies/`, `projects.json`, `global-mcp.json` — then sync. Generated surfaces (`<project>/.claude/`, `<project>/.codex/`, `<project>/.gemini/`) are never hand-edited.
- **Triad validator is the mandatory final gate.** After any canonical change, `python3 scripts/validate-triad-runtime.py --project <name>` must pass before the work is considered done. The structural verifier confirms files exist; only the triad validator confirms the three host CLIs can actually reach them.
- **Append-first.** New lessons go into `docs/LESSONS_LEARNED.md`. Doctrine in `AGENTS.md` and `docs/CONOPS.md` does not move silently — promotion is explicit and gated.
- **Native boot files stay native.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` keep their host-specific names.
- **No `--no-verify`, no force-push to protected branches, no `--no-gpg-sign`.** The `telemetry-guardian` hook blocks these on every host. If you need a one-time bypass, set `AGENT_FORGE_GUARDIAN=off` for that session — every bypass is logged to `~/.agent-forge/guardian.log`.

## Layout

```
_agent_forge/
├── README.md                     ← you are here
├── AGENTS.md                     ← multi-agent contract (all hosts auto-load)
├── CLAUDE.md / GEMINI.md         ← thin host boot adapters
├── policies/
│   ├── hooks.json                ← canonical hook schema (renders to all three hosts)
│   └── memory.json               ← canonical memory section schema
├── projects.json                 ← governed project catalog
├── global-mcp.json               ← shared MCP server inventory (currently empty)
├── registry.json                 ← generated compatibility output (do not hand-edit)
├── skills/
│   ├── global/                   ← portable cross-project skills (28 of them)
│   └── projects/<project>/       ← project-local skills
├── teams/                        ← canonical team manifests
├── scripts/
│   ├── omni_factory.py           ← the canonical generator
│   ├── verify-agent-forge.py     ← structural verifier (file presence + schema)
│   ├── validate-triad-runtime.py ← runtime gate (CLI enumeration + hook + memory)
│   ├── validate-codex-runtime.py ← strict Codex-only probe
│   ├── bootstrap-workstation.sh  ← installs Claude / Codex / Gemini CLIs
│   ├── bootstrap-project.sh      ← scaffolds a new governed project
│   ├── deploy-and-bootstrap.sh   ← one-shot operator path from a suitcase bundle
│   ├── deploy-factory.sh         ← deploys _agent_forge into ~/Projects
│   ├── factory-export.sh         ← builds a portable suitcase bundle
│   └── sync-claude-adapters.sh / sync-codex-skills.sh / sync-gemini-adapters.sh
├── runtime/
│   ├── validation-matrix.json    ← coverage ledger; survives across runs
│   └── validation/               ← timestamped probe artifacts (gitignored)
├── exports/                      ← suitcase bundles (gitignored)
└── docs/                         ← architecture, runbooks, lessons, roadmap
```

## Help

- Open issues against this repo, or ping the canonical operator.
- For Claude/Codex/Gemini-specific quirks, check `docs/LESSONS_LEARNED.md` first — most host-quirk problems have already been documented there.
