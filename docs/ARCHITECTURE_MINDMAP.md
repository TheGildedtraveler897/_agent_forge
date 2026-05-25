# Agent Forge Architecture Mind Map
*Generated 2026-05-22 | Haiku reconnaissance pass*

---

## MISSION & PHILOSOPHY
**Core Purpose:** Canonical governance factory for portable multi-agent work (Claude/Codex/Gemini) across ~/Projects.

**Key Principle:** Single source of truth → Host-native delivery surfaces via renderers. Not Claude-heavy or Codex-partial; symmetric.

**What It Solves:** 
- Truth spread across multiple files (old: skill.md + registry.json + hand-authored adapters) → **One canonical location per concern**
- Cross-agent handoffs breaking on glitches → **Persistent durable state, plan continuity, memory bridges**
- Host-specific gaps → **Explicit native vs sidecar split; documented exclusions**

---

## CANONICAL SOURCES (What Gets Authored)

### 1. Skills / Capabilities
- **Location:** `skills/global/` (30 skills) + `skills/projects/<project>/`
- **Metadata:** Each `SKILL.md` has frontmatter with:
  - `capability_class`: workflow, expert, governance
  - `targets`: [claude, codex, gemini] or subset
  - `context_cost`: light/medium/heavy
  - `model_tier`: any / opus-only / etc
- **Key Skills (Global):**
  - `execution-planner` — Spec→detailed task plan with embedded RED tests, no TBD
  - `spec-architect` — Adversarial spec discovery, one-Q-at-a-time, section approval
  - `tdd-engineer` — RED/GREEN/REFACTOR execution, 3-fix architecture stop
  - `subagent-dispatcher` — Parallel/sequential delegation with fresh context
  - `memory-bridge` — Session lifecycle sync (MEMORY.md ↔ host-local)
  - `memory-archivist` — Append-only management, secrets deny policy
  - `lesson-distiller` — Archive promoted lessons to bounded-decay file
  - `handoff-archiver` — Archive sprints, keep latest N + operator state
  - `branch-finisher` — Pre-merge gate (tests-must-pass, no hook bypass)
  - `telemetry-guardian` — Pre-tool veto (blocks --no-verify, force-push, wildcard rm)
  - `prompt-auto-activator` — Advisory-only skill trigger (caveman, terse, checkpoint)
  - `onboarding-guide` — First-time operator walkthrough, three modes
  - Plus: root-cause-analyst, skill-author, code-review-doctrine, quality-gate, portability-auditor, context-engineer, etc.

### 2. Hooks
- **Location:** `policies/hooks.json` (schema v3)
- **Event Translation:** Canonical event names (snake_case) → host-native via `_EVENT_ALIASES` allow-list
- **Active Hooks:**
  - `pre-tool-execution-guardian` → Bash invocations (all hosts)
  - `prompt-auto-activator` → User prompt submit (Claude, Codex)
  - `memory-bridge-outbound-*` → Session start per host
  - `memory-bridge-inbound-*` → Session stop per host
- **Anatomy:** id, event, matcher, handler (command/http/mcp_tool), targets, timeout, status_message
- **Host Support:** Only command handlers live on all three; http/mcp_tool are emerging

### 3. Universal Memory & State Layer
- **Location:** `policies/memory.json` (schema v2)
- **Rendered to:** 
  - Native: `<project>/MEMORY.md` (auto-loaded by Claude/Gemini via boot file walk)
  - Sidecar: `<project>/.forge_state/` (manifest, archivist log, bridge state, bridge log)
- **Sections (append-only by default):**
  - `build_commands` — Verified shell commands (test, lint, build, deploy)
  - `project_quirks` — Non-obvious traps, host/env gotchas
  - `active_tasks` — Short-lived work (only rewriteable section)
  - `recent_decisions` — Decisions made, why, arch implications
  - `known_failures` — Reproducible bugs, expected-but-unresolved issues
  - Plus custom sections per project
- **Bridge Lifecycle:** Session start → bridge.py outbound copies MEMORY.md to host-local; session stop → bridge.py inbound imports host notes back via archivist (secrets filter re-applied)

### 4. MCP Servers
- **Location:** `global-mcp.json` (schema v2)
- **Declared Once:** Each server defined exactly once, rendered outward to all hosts
- **Active Server:**
  - `forge-factory` — Local stdio MCP, Python-based, serves `read_handoff` tool across all hosts
- **Per-Record Metadata:**
  - Transport (stdio, HTTP, SSE), auth, trust posture
  - Tool filter (whitelist what tools are exposed)
  - Env passthrough and literals
  - Project routing (shared or project-specific)

### 5. Projects Catalog
- **Location:** `projects.json` (currently empty: [])
- **Planned:** Governed project registry (skills delivery, team assignment, bootstrap variants)

### 6. Teams
- **Location:** `teams/` (manifests as JSON)
- **State:** Conceptual role contracts, collapse/escalation rules, host mapping hints
- **Not yet:** Executable orchestration; primarily documentation

---

## KNOWLEDGE ANCHORS (Durable Wisdom)

### 1. Lessons Learned
- **File:** `docs/LESSONS_LEARNED.md` (append-first)
- **Entry Template:**
  - Date, Context, Lesson, Architectural Decision, Evidence, Promotion Target, Status
  - Status: active | promoted | superseded
- **Lifecycle:**
  - Harvested during sprint via `sprint-harvester` skill
  - Promoted into doctrine (AGENTS.md, CONOPS.md) when durable + broad
  - Archived to `docs/archive/LESSONS_PROMOTED.md` once promoted (with one-line index pointer left behind)
- **Bounded Decay:** `lesson-distiller` skill compacts file on RC/milestone via `policies/distillation.json` contract

### 2. Handoff Log
- **File:** `docs/HANDOFF.md` (sprint summaries + operator state)
- **Sections:**
  - `## What Changed` — Sprint summaries (appended by sprint-harvester)
  - `## Current State` — One-para prose of working state
  - `## Remaining Weaknesses` — Known gaps, blockers
  - `## Next Evolution` — Next sprint/initiative
  - `## Final Verdict` — Ship-readiness statement per milestone
- **Bounded Decay:** `handoff-archiver` archives older sprints to `docs/archive/SPRINTS.md`, keeps latest N + operator sections forever

### 3. Doctrine (Canonical Rules)
- **AGENTS.md** — Multi-agent workflow discipline chain, rules, operator tips
- **CONOPS.md** — Mission, why omni-factory, canonical sources, capability model, hook governance, memory layer, distillation, MCP, bootstrap, security
- **CLAUDE.md** (adapter) — Claude-specific notes, reference to shared docs
- **GEMINI.md** (adapter) — Gemini-specific notes

---

## RENDERING PIPELINE (How Canonical → Host-Native)

### Master Sync Engine: `omni_factory.py`
- **Input:** All canonical sources (skills/, policies/, global-mcp.json)
- **Output:** Host-native surfaces per Claude/Codex/Gemini
- **Rendering Rules:**
  - `targets: [...]` in each canonical record determines which hosts receive it
  - Event alias translation: canonical snake_case → native names (if alias is None, drop from that host)
  - Tool filter: whitelist approach (only listed tools exposed)
  - Memory sections: rendered to MEMORY.md + .forge_state/ manifest

### Validators
- **verify-agent-forge.py** — Schema validation + on-disk evidence checks (are referenced files present?)
- **validate-triad-runtime.py** — Per-host surface check (can Claude/Codex/Gemini CLI actually enumerate the rendered skills/hooks/MCP?)
  - Validates that aliases resolve correctly
  - Smoke-tests MCP `tools/list`
  - Records pass/fail per host

### Host Delivery Surfaces

**Claude:**
- `~/.claude/agents/` — Global agents
- `~/.claude/skills/` — Global commands
- `~/.claude/projects/<encoded>/memory/MEMORY.md` — Auto-loaded machine-local memory
- `<project>/.claude/agents` — Project agents
- `<project>/.claude/skills` — Project commands
- `<project>/.claude/skills` — Project skills
- `<project>/.mcp.json` — Project MCP
- `<project>/CLAUDE.md` (boot file, hierarchical walk)

**Codex:**
- `~/.agents/skills` — Global skills (pre-omni-factory, compatibility)
- `<project>/.agents/skills` — Project skills (pre-omni-factory)
- `<project>/.codex/agents` — Project agents (omni-factory rendered)
- `<project>/.codex/config.toml` — Omni-factory MCP
- `<project>/.codex/hooks.json` — Omni-factory hooks
- `<project>/.codex/memory/AGENTS_MEMORY.md` — Sidecar memory bridge
- `AGENTS.md` (auto-load hierarchical walk)

**Gemini:**
- `~/.gemini/agents` — Global agents
- `~/.gemini/skills` — Global commands
- `~/.agents/skills` — Global Agent Skills
- `~/.gemini/GEMINI.md` (boot file)
- `<project>/.gemini/agents` — Project agents
- `<project>/.gemini/skills` — Project commands
- `<project>/.gemini/skills` — Project skills
- `<project>/.gemini/settings.json` — Project MCP
- `<project>/.gemini/memory/MEMORY.md` — Sidecar memory bridge
- `<project>/GEMINI.md` (boot file)

---

## WORKFLOW DISCIPLINE CHAIN (The Default Playbook)

**For any non-trivial code change under a governed project:**

1. **spec-architect** → Adversarial 1-Q-at-a-time discovery, 2–3 approach options, section-by-section approval
2. **execution-planner** → Decompose into 2–5 min micro-tasks, exact file paths, embedded RED tests, zero TBD
3. **tdd-engineer** → RED/GREEN/REFACTOR execution, watched-failing-test gate, 3-fix stop
4. **[optional] subagent-dispatcher** → Parallel or sequential delegation with fresh context + 2-stage review
5. **verification-gate** → Fresh evidence (tests, code inspection, subagent reports)
6. **branch-finisher** → Pre-merge gate (tests-must-pass, no hook bypass), post-merge re-verify

**Escape Hatches:**
- `root-cause-analyst` — When tdd-engineer hits 3-fix stop or bug needs deep understanding
- `code-review-doctrine` — Giving/receiving code review with STOP-and-ASK on unclear feedback
- `skill-author` — Meta-skill for authoring/revising skills under `skills/`

---

## CURRENT SHIP STATE (NRC Delivery, Monday 2026-05-25)

### Branch: `feat/ship-prep`
- **Target:** Clean COI-compliant production bundle to National Research Council Canada
- **Commits Shipped (Tracks A–E):**
  - **Track A** (`dc3f893`) — Scrub personal-project content for clean production ship
  - **Track B** (`59e2953`) — Port hook helpers to Python (Windows-native execution, no bash)
  - **Track C** (`43c22be`) — `factory-export.sh --mode onboarding` for clean bundle export
  - **Track D** (`05ed429`) — Cross-platform deploy entry points + MacPorts-only macOS polish
  - **Track E** (`a2f838e`) — Distillation validator warning → WARN not FAIL
- **Platform Constraints at NRC:**
  - Windows: WSL blocked → Native Claude Code only → Hooks must be Python
  - macOS: MacPorts only (no Homebrew)
  - Coworkers use: Claude Code on Windows; operator uses Claude/Codex/Gemini on macOS

### Known Clean-Up Gaps (Active Issues)
1. **Plan Persistence** — Awaiting-approval plan was lost on glitch; no disk save
2. **Ship-prep finalization** — COI audit completed 2026-05-23; bundle verified clean.

---

## KEY ARCHITECTURAL PATTERNS

### 1. Omni-Factory (Canonical → Host-Native)
- **Why:** One truth source scales better than hand-authored adapters per host
- **How:** Policy (JSON schema) → Renderers (omni_factory.py) → Host-native surfaces
- **Validated By:** Structural verifier (schema) + triad validator (runtime, per-host)

### 2. Append-First + Bounded Decay
- **Append-first:** New knowledge lands in LESSONS_LEARNED.md; existing doctrine unchanged (prevents silent rewrite)
- **Bounded-decay:** Once promoted, archived via distiller to keep auto-loaded file size < threshold
- **Reversibility:** Archive is the on-disk wisdom anchor; distillation is operator-gated, not automatic

### 3. Native vs Sidecar Splits
- **Native:** Host auto-loads (Claude MEMORY.md, Codex AGENTS.md, etc.)
- **Sidecar:** Governed in lockstep but host doesn't auto-load (Codex `.codex/memory/AGENTS_MEMORY.md`)
- **Why:** Acknowledges host CLI parity gaps; documents conservatism rather than faking equivalence

### 4. Plan Continuity (Current Gap)
- **Spec-approved** → execution-planner generates detailed task plan
- **Plan lands** → Currently only in Claude's context; no disk save
- **Glitch or context overflow** → Next agent (Codex/Gemini) has no plan artifact
- **Desired State:** Plan saved to disk, status tracked (awaiting-approval | approved | superseded), handoff references file path

### 5. Memory Bridge Lifecycle
- **Session start** → `memory-bridge outbound` copies MEMORY.md to host-local auto-memory
- **Agent works** → Host makes local notes
- **Session stop** → `memory-bridge inbound` imports notes back via archivist (secrets re-checked)
- **Next session** → Canonical MEMORY.md includes the notes; all hosts see unified state

---

## SCRIPTS INVENTORY (Tools & Automation)

### Core Sync/Export
- **omni_factory.py** — Master renderer (canonical → host-native)
- **verify-agent-forge.py** — Structural validator (schema + on-disk evidence)
- **validate-triad-runtime.py** — Runtime validator (per-host CLI enumeration + smoke tests)

### Bootstrap & Deploy
- **bootstrap-project.sh** — Create thinnest governed project scaffold
- **bootstrap-workstation.sh** — Workstation setup (dependencies, hooks, MCP, user dirs)
- **bootstrap-project.ps1** — Windows native bootstrap
- **deploy-factory.sh** / **deploy-factory.ps1** — Deploy factory itself to workstations

### Host Sync Helpers (Per-Host)
- **sync-claude-adapters.sh** — Refresh Claude agents/commands/skills
- **sync-codex-skills.sh** — Refresh Codex skills
- **sync-gemini-adapters.sh** — Refresh Gemini agents/commands/skills

### Utilities
- **enforce-branch-discipline.sh** — Pre-check for task branch (blocks work on main/master for non-trivial changes)
- **continuity_cursor.py** — Manage active-task cursor in `dev/active/<slug>/` for session continuity
- **factory-export.sh** — Export clean bundle for distribution (--mode onboarding for NRC)
- **live-hook-prober.py** — Debug/monitor hooks in real-time

### Cost/Analysis
- **codex-cost** — Estimate Codex invocation cost
- **codex_cost_table.py** — Cost table rendering

### MCP
- **scripts/mcp/forge_factory_server.py** — Stdio MCP server (exposes read_handoff tool)

---

## GOVERNANCE RULES (From AGENTS.md)

**Multi-Agent Handoff:**
- Commit branch state before handoff
- Handoff must name: branch, latest commit, next task, dirty state
- **NEW (from today):** Handoff must also reference plan file if one exists

**Branch Discipline:**
- `master`/`main` = integration-only
- Non-trivial work = named task branch
- Simultaneous agents = separate branches (unless deliberately pairing)
- Run `enforce-branch-discipline.sh` preflight

**Workflow Gates:**
- Plans must be approved before execution starts
- Tests must pass before merge
- No `--no-verify`, `--force`, or signature bypass on merge
- Validation-after-merge step in branch-finisher

**Tool Invocation Philosophy:**
- Prefer narrow calls over heroic compound commands
- One question per Bash when inspecting many files
- `&&` / `;` chains only for short related steps
- Tool-result-missing = re-grounding signal, not retry signal

---

## RUNTIME VALIDATION COVERAGE

**Tracked in:** `runtime/validation-matrix.json`

**Coverage Ledger:**
- Claude user and project surfaces (agents, commands, skills, MEMORY, hooks)
- Codex project skills, agents, config, runtime execution
- Gemini user and project surfaces (agents, commands, skills, MEMORY, hooks)
- Bootstrap paths (project + workstation, per-host)

---

## SECURITY & SECRETS POLICY

- Never commit `.env` or auth state
- MCP secrets flow through env vars, not repo literals
- User-home configs touched only when governance declares shared servers
- Project-local surfaces override user-global convenience overlays
- Memory-archivist re-checks secrets-deny policy on inbound host imports

---

## NEXT CRITICAL GAP: Plan Persistence & Continuity

**Current State:**
- `execution-planner` generates detailed task plans
- Plans exist in Claude's context only
- No disk save; no state tracking (awaiting-approval vs approved)
- Multi-agent handoff loses plan on glitch/context overflow

**Desired Outcome (Opus Design Task):**
- Plans auto-save to `docs/plans/<branch>.md` at generation
- Frontmatter tracks status: `awaiting-approval | approved | superseded`
- Handoff references plan file explicitly
- Token-aware: one-line pointer in MEMORY.md, full plan on-disk for cross-agent pickup
- **Integration point:** execution-planner SKILL.md updated to include persistence as core instruction

---

*This artifact is the knowledge base for the Opus planning session. All canonical references verified against current state; all script paths tested; all host surfaces accounted for. Ready for design of plan-persistence layer and integration into execution-planner.*
