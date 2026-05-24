# Multi-Agent Examples

Real workflows that use Agent Forge's plan persistence + MEMORY bridge across multiple host CLIs. None of these require an orchestration engine; each one is operator-driven (you start each host's session manually), but the canonical files do the handoff work.

## Example 1: GSD Delivery Team

Manifest: `teams/gsd-delivery-team.json`.

**The phases:**
- **Phase 1 (Discuss):** Principal-Architect (Claude) locks in the design and architecture before planning begins. Claude uses `/spec-architect` to discover the spec interactively and write an architecture decision.
- **Phase 2 (Plan):** Execution-Planner (Claude) breaks the approved design into atomic, executable tasks. Claude uses `execution-planner` to write `docs/plans/<branch-slug>.md` with status `approved`.
- **Phase 3 (Execute):** Builder (Codex) orchestrates implementation across fresh context windows. Codex reads the plan file (via the `active_tasks` pointer in `MEMORY.md`), executes each task with `tdd-engineer`, and appends results to `MEMORY.md`.
- **Phase 4 (Review & Gate):** QA-and-Review (Gemini) runs paranoid code review and E2E validation. Gemini reads the updated `MEMORY.md` and diffs, runs `paranoid-reviewer` or `verification-gate`, and gates the merge.

**Handoff artifacts:** Architecture decision, implementation plan, findings report. All three are pinned to `MEMORY.md` for cross-host visibility.

**When to use this pattern:** Large features that benefit from strict phase separation and fresh context windows at each stage.

---

## Example 2: Research Team

Manifest: `teams/research-team.json`.

**The roles:**
- **Research-Scout (Claude):** Gathers the minimum useful source set from local context and primary sources. Claude uses `/evidence-packager` or `/context-engineer` to surface findings without narrative bloat. Stops when the important source surface is covered and obvious dead ends are excluded.
- **Source-Triager (Gemini):** Sorts findings into confirmed facts, conflicts, and uncertainty. Gemini is cost-effective for high-volume triage passes. Triaged findings go to `MEMORY.md` so the next phase can build on them.
- **Evidence-Packager (Claude):** Compresses research into a reusable evidence pack without narrative bloat. Claude uses `evidence-packager` to create a machine-readable output that downstream planners can work from without re-reading the source hunt.

**Handoff artifacts:** Evidence pack, source table, unresolved questions. The evidence pack lives in `MEMORY.md` where the next phase (planning or execution) can reference it.

**When to use this pattern:** Ambiguous problems that need evidence before planning, source-heavy research, and multi-domain investigations that benefit from cost-conscious triage (Gemini) paired with synthesis (Claude).

---

## What These Examples Are NOT

They're not automated. Each phase transition requires the operator to start the next host's CLI. The factory does not have a working orchestration engine (`subagent-dispatcher` is an instruction contract, not a worker). What the factory DOES have: canonical state (`MEMORY.md`, plan files) that survives the host transition.

---

## When to Pick Each Host

- **Pick Claude** for: spec discovery, plan authoring, expert review of complex specs. Claude has the best long-context reasoning and native auto-memory.
- **Pick Codex** for: bounded build tasks with strong sandbox needs (bwrap on Linux, Seatbelt on macOS). Codex's default sandbox protects against supply-chain risks.
- **Pick Gemini** for: vision-required tasks, cost-sensitive review passes, large-file analysis. Gemini CLI is the most cost-efficient non-trivial tier.

---

## How to Start a Multi-Agent Workflow

1. Create a governed project: `bash ~/Projects/_agent_forge/scripts/bootstrap-project.sh --name <name>`.
2. Pick a team manifest that matches your problem (GSD for structured delivery, Research for evidence-heavy work, etc.).
3. Read the team's roles and preferred skills. Start the first host's CLI and invoke the first skill (e.g., `/spec-architect` for principal-architect).
4. When that phase completes, the outputs land in `MEMORY.md` and/or `docs/plans/`. Switch to the next host's CLI.
5. The next host reads `MEMORY.md` on session start. Ask it: "Read the last phase's output and continue." It sees the plan pointer, reads the file, and executes the next phase.
6. Repeat until the workflow completes.

---

## Example Commands

### GSD Delivery Team Walkthrough

```bash
# Start Claude Code
claude

# Phase 1: Discover and design
/spec-architect "Add user authentication with OAuth2"
# Choose approach, approve plan

# Phase 2: Plan implementation
/execution-planner
# Review plan, approve it

# Plan lands at docs/plans/<branch-slug>.md
# Exit Claude

# Start Codex
codex

# Phase 3: Execute from the plan
# Codex auto-loads MEMORY.md and sees the plan pointer
# Ask: "Read the plan and execute it with tdd-engineer"
# Codex runs each task, appends results to MEMORY.md

# Exit Codex

# Start Gemini
gemini

# Phase 4: Review and gate
# Gemini reads the updated MEMORY.md and diffs
# Ask: "Run paranoid-reviewer on the diffs"
# Gemini reports findings and gates the merge
```

### Research Team Walkthrough

```bash
# Start Claude (Research-Scout role)
claude

# Gather sources and findings
/evidence-packager "What are the SOTA 2026 hook standards across AI CLI vendors?"
# Claude surfaces findings in MEMORY.md

# Exit Claude

# Start Gemini (Source-Triager role)
gemini

# Triage and organize
# Gemini reads MEMORY.md (cost-effective for high-volume triage)
# Ask: "Sort these findings into facts, conflicts, and open questions"
# Results append to MEMORY.md

# Exit Gemini

# Start Claude (Evidence-Packager role)
claude

# Synthesize for downstream
# Claude reads the triaged findings from MEMORY.md
# Ask: "Package these into a reusable evidence pack"
# Final evidence pack goes to MEMORY.md for the next phase
```

---

## Limitations and Future Work

The current multi-agent workflow is operator-driven and file-system-based. Future enhancements could include:

- **Automatic agent invocation:** The factory could trigger the next host's CLI when a phase completes, instead of requiring manual `codex` or `gemini` commands.
- **Orchestration engine:** A working `subagent-dispatcher` that reads team manifests and enforces role ordering and escalation rules.
- **Cross-host handoff UI:** A dashboard that shows active plans, phase progress, and who's responsible for the next step.

For now, the canonical files (plan + MEMORY.md) are the handoff artifact, and you (the operator) decide which host runs next.
