# Omni-Factory Pathfinder Roadmap

## The 2026 SOTA Horizon
A detailed synthesis of the most advanced features currently available across the Triad (Claude Code, OpenAI Codex, Gemini CLI).

**1. Advanced Orchestration & Mechanics**
- **Multi-Agent & Subagents:** All three hosts now support robust multi-agent orchestration. Claude Code uses a "lead agent" model; Gemini CLI treats "Agent-as-a-Tool" for dynamic routing; Codex utilizes isolated Sandboxing and "Computer Use" for robust environment interaction.
- **Session Teleportation:** Claude Code allows fluid movement of long-running sessions between terminal, web, and mobile environments.
- **Unix Philosophy:** Pipelining logs directly into agents is now a native standard.

**2. MCP Routing Patterns**
- **Transport & Prefixing:** Gemini CLI leads with multi-transport MCP (Stdio, SSE, Streamable HTTP) and server-key prefixing to prevent tool collisions across vast catalogs.
- **Cross-Surface Synchronization:** Claude Code synchronizes MCP servers, settings, and instructions across all IDE and terminal surfaces.
- **Deep Research Integration:** Codex uses specialized MCP routing for high-intensity information gathering and ChatGPT UI integration.

**3. Context-Window Optimization Tricks**
- **Caching & Compaction:** Codex leverages Prompt Caching and automatic Token Compaction. It also employs "Predicted Outputs" to anticipate code patterns.
- **Auto Memory & Selection Context:** Claude Code uses background "Auto Memory" to save project learnings across sessions, preventing context bloat.
- **Tier-Based Persistence:** Gemini CLI's Memory v2 natively writes to `GEMINI.md` and private `MEMORY.md` indexes for cross-session fact persistence.

**4. Background Memory Agents**
- **Chronicle & Routines:** Codex features the "Chronicle" long-term memory system. Claude Code supports "Routines" (scheduled agents for tasks like morning PR reviews).
- **Pattern Injection:** Gemini CLI uses background pattern recognition to automatically inject historical context into the prompt just-in-time.

**5. Hook Lifecycle Events**
- **Safety & Execution Hooks:** Gemini CLI enforces strict JSON-based `stdin/stdout` hooks (pre/post-execution) acting as security guardrails (Allow/Block/Log). Claude supports pre-action and post-action shell hooks (e.g., auto-formatting after edits).
- **Webhooks:** Codex supports event-driven server-side webhooks for asynchronous CI/CD integration.

---

## Architectural Upgrades: The Universal State Layer
Concrete, blueprint-level proposals for upgrading the `omni_factory.py` engine to support these advanced features while **ensuring 100% cross-pollination between Claude, Codex, and Gemini**.

**1. The Cross-Agent Memory Exchange (The `MEMORY.md` Standard)** — ✅ Shipped 2026-04-25
*   **The Problem:** Claude uses "Routines", Codex uses "Subagents", Gemini uses "Agent-as-a-Tool". If they store knowledge natively, they silo.
*   **The Blueprint:** We establish `MEMORY.md` (and a `.forge_state/` directory) as the **Universal State Layer**. 
*   **The Implementation:** Update `omni_factory.py` to enforce that *all* agents read and write to `MEMORY.md`. 
    *   When Claude's Auto-Memory learns a build command, it hooks into `MEMORY.md`. 
    *   When Gemini boots up the next day, its pre-action hook parses `MEMORY.md` and injects it into the prompt.
    *   *Result:* Gemini directly benefits from Claude's overnight work. They share a single brain.
*   **Status:** `policies/memory.json` v1 schema is authoritative (five sections, retention 50/warn-at-40, secrets-deny). `scripts/omni_factory.py` carries `sync_memory()` invoked from all three host syncs. Six governed projects each have `MEMORY.md` + `.forge_state/`. `AGENTS.md` Read Order entry #5 names `MEMORY.md` for every host. Triad validator's `memory_surface_for` now gates overall pass. Evidence: `runtime/validation/triad/20260425-174222/`.

**2. Unified Hook Lifecycle (Cross-CLI Guardrails)** — ✅ Shipped 2026-04-24
*   **Blueprint:** Create a `hooks.json` schema in the factory that compiles down to the native hook formats of each CLI (Gemini's `hooksConfig`, Claude's pre/post-action shell scripts, Codex's config hooks).
*   **Implementation:** Implement standard hooks like `pre-commit-lint` and `post-edit-format`. Crucially, add a `pre-tool-execution` security hook across all CLIs to enforce Agent Forge doctrine before any destructive action (`terraform destroy`, `rm -rf`).
*   **Status:** `policies/hooks.json` is on schema v2 with shared + per-host arrays; three host renderers in `scripts/omni_factory.py` write `.claude/settings.json`, `.codex/hooks.json`, and `.gemini/settings.json`. Triad validator now gates on hook-surface presence per host. Evidence: `runtime/validation/triad/20260424-205818/`. Lesson ledger: 2026-04-24 entry. Future cross-host hooks (`pre-commit-lint`, `post-edit-format`) plug into the same schema.

**3. MCP Namespace Prefixing & Routing**
*   **Blueprint:** Update the factory's MCP generator to automatically prefix tool names (e.g., `forge.github.*`, `forge.jira.*`) to prevent collisions as the catalog grows, mimicking Gemini's SOTA routing.

**4. Continuous Evolution (Anti-Rot Mechanics)**
*   **The Problem:** Roadmaps and contexts decay rapidly. Links break, APIs change, and new tools make old workflows obsolete.
*   **The Blueprint:** We integrate the `sprint-harvester` and a new `routine-auditor` into the Omni-Factory's CI pipeline.
*   **The Implementation:** 
    *   The `routine-auditor` runs nightly via a Codex webhook. It tests all MCP connections, validates that `CLAUDE.md`, `GEMINI.md`, and `MEMORY.md` are structurally sound, and flags any broken links.
    *   The `sprint-harvester` runs at the end of every task to distill hard-won lessons into the `LESSONS_LEARNED.md` and `MEMORY.md` files, ensuring the factory's knowledge base appreciates in value rather than degrading over time.

---

## Capability Backlog
A prioritized list of new skills and teams we must build next to maximize our leverage over the LLMs.

**1. `memory-archivist` (Background Agent)** — ✅ Shipped 2026-04-25
*   **Spec:** A continuous background skill that monitors session diffs and tool usage. It distills facts, project quirks, and build commands, appending them to `MEMORY.md`. It translates Claude's "Routines" and Codex's "Chronicle" outputs into the universal markdown format.
*   **Status:** Lives at `skills/global/memory-archivist/` with `SKILL.md` (workflow class, all-host targets) and `archivist.py` providing `append` / `validate` / `summary` subcommands. Append-first by default; `active_tasks` rewriteable; secrets-deny patterns reject API keys, private keys, and credential-shaped strings. Audit log at `<project>/.forge_state/archivist.log`. Wired into `teams/improvement-team.json` alongside `sprint-harvester` (harvester = durable doctrine candidates; archivist = session-scoped state).

**2. `router-overseer` (Agent-as-a-Tool Dispatcher)**
*   **Spec:** A master routing agent that doesn't write code. Instead, it analyzes the user's prompt and dispatches sub-agents (e.g., `legal-counsel`, `infra-architect`) in parallel, merging their outputs into a cohesive response that is written back to the Universal State Layer.

**3. `telemetry-guardian` (Pre-Action Hook Skill)** — ✅ Shipped 2026-04-24
*   **Spec:** A strict JSON-based hook skill that intercepts destructive tool calls across all three CLIs. It checks the command against a local safety policy, evaluates "Reasoning Effort," and determines whether to Allow, Block, or Log the action.
*   **Status:** Lives at `skills/global/telemetry-guardian/` with `SKILL.md` (expert class, all-host targets) and POSIX `guardian.sh`. Wired into `policies/hooks.json` as the seeded `pre-tool-execution-guardian` record. Deny list covers `--no-verify`, `--no-gpg-sign`, force-push to protected branches, `git reset --hard <ref>`, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777. Bypass via `AGENT_FORGE_GUARDIAN=off` (logged to `~/.agent-forge/guardian.log`).

**4. `routine-auditor` (Scheduled CI/CD Agent)**
*   **Spec:** A webhook-triggered agent that runs overnight. It utilizes Codex's Deep Research MCP to review open PRs, run static analysis, check for broken roadmap links, and leave architectural feedback on GitHub/GitLab before the human team wakes up.

**5. `auto-loop` (Autonomous Research & TDD Agent)**
*   **Spec:** Inspired by Karpathy's `autoresearch`, this agent enters a silent sandbox loop (Propose -> Edit -> Run Test -> Evaluate -> Ratchet). Crucially, to protect users from wasting tokens on bad parameters, this skill MUST include an **interactive wizard hook** at startup. It will ask plain-English questions to help non-experts define the `program.md` goals, identify the correct failing tests, and set hard success metrics before the expensive iteration loop begins.

**6. `wiki-compiler` (Knowledge Base Generator)**
*   **Spec:** An agent designed to end the reliance on brittle RAG systems. You point it at raw PDF documentation, API specs, or a massive codebase, and it runs in the background to "compile" that raw data into a structured, densely hyperlinked set of Markdown files that all other agents can instantly read and understand.

**7. `crew-director` (Capstone Swarm Orchestrator)**
*   **Spec:** Our ultimate SOTA capstone. A high-level orchestration skill that manages complex, multi-stage operations by autonomously spinning up sub-agents. For example, if asked to "Release a new software version," it will independently spawn `auto-loop` to fix tests, `wiki-compiler` to generate the changelog, and `brand-guardian` to update the release graphics—managing handoffs between them without human intervention.