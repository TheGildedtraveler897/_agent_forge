# Agent Forge — SOTA 2026 Drift Audit

**Last verified:** 2026-05-22
**Verification method:** Three parallel Explore subagents (primary-source WebFetch on vendor docs, academic citation verification via arXiv / ACL Anthology / NeurIPS proceedings, current-state inventory of `~/Projects/_agent_forge`).
**Authority:** This file is the load-bearing research anchor for SOTA decisions. Re-verify against vendor docs before relying on specifics — vendor docs change without notice. If a vendor's CLI now does something this audit describes differently, the vendor wins. Update this file in the same commit.

---

## How To Use This File

When a future sprint asks "are we still SOTA-aligned?", read this file first. Each claim names its primary source. Re-fetch the source before acting; if the source has changed materially, update the claim here in the same commit. Do not silently rewrite a prior claim — append a dated revision note so the audit history is intact.

When proposing an architectural change that cites "industry SOTA," verify the citation against this file. If the citation isn't here or doesn't match, either add it (with primary source) or treat the claim as unverified.

---

## Section 1 — Cross-Vendor Convergence (What Has Standardized)

### 1.1 Skills — the [agentskills.io](https://agentskills.io) open standard

All three vendors (Anthropic Claude Code, OpenAI Codex, Google Gemini CLI) ship skills based on the Agent Skills open standard:

- **Format:** A folder containing `SKILL.md` (required) with YAML frontmatter and Markdown body.
- **Required frontmatter fields:** `name`, `description`.
- **Optional sibling files:** `scripts/`, `references/`, `assets/`.
- **Progressive disclosure contract:** Agents load only `name` + `description` at startup; the full skill body loads only when the skill is invoked. This is the design pattern that keeps the agent's working context lean despite large skill libraries.

**Primary sources:**
- [agentskills.io](https://agentskills.io) — standard authority
- [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- [Codex skills docs](https://developers.openai.com/codex/skills)
- Gemini CLI skills support (in repo: `github.com/google-gemini/gemini-cli/tree/main/docs`)

**Agent Forge alignment:** Strong. All 30 skills use `SKILL.md` with frontmatter (`name`, `description`, `capability_class`, `targets`, `context_cost`, `model_tier`, optional `delivery_projects`). The factory adds `capability_class` and `targets` as local extensions (see Section 4).

### 1.2 MCP — Model Context Protocol 2025-11-25

All three vendors implement the Model Context Protocol [2025-11-25 specification](https://modelcontextprotocol.io/specification/latest):

- **Transport:** JSON-RPC 2.0, stateful.
- **Server features:** Resources (context), Prompts (templates), Tools (functions).
- **Client features:** Sampling (agentic LLM calls), Roots (filesystem boundaries).
- **Field names are identical across hosts.**

Per-host config locations differ (Claude `.mcp.json`, Codex `.codex/config.toml`, Gemini `.gemini/settings.json`), but the server-declaration schema is the same.

**Primary sources:**
- [MCP specification (latest)](https://modelcontextprotocol.io/specification/latest)
- [MCP docs index](https://modelcontextprotocol.io/llms.txt)

**Agent Forge alignment:** Strong. `global-mcp.json` (schema v2, Agent Forge-internal versioning) declares servers once; renderers translate to host-native locations. The 2026-05-22 lesson removed `sh -c` shell wrappers so env-var expansion happens at render time (Windows-portable).

---

## Section 2 — What Has NOT Converged

### 2.1 Subagents

Three different schemas. Not interchangeable.

| Vendor | File format | Location | Notable fields |
|---|---|---|---|
| **Claude Code** | Markdown with YAML frontmatter | `.claude/agents/` (project) or `~/.claude/agents/` (user) | `name`, `description`, `tools`, `model`, agent body |
| **OpenAI Codex** | **TOML** | `~/.codex/agents/` or `.codex/agents/` | `[agent]` section: `name`, `description`, `developer_instructions`, `sandbox_mode`, `model` |
| **Gemini CLI** | Markdown with YAML frontmatter | `.gemini/agents/` | `name`, `description`, `kind`, `tools`, `model`, `temperature`, `mcpServers` (object) |

A YAML frontmatter file written for Claude is **not** loadable by Codex. The factory must render different file formats per host.

**Primary sources:**
- [Claude subagents](https://code.claude.com/docs/en/sub-agents)
- [Codex subagents](https://developers.openai.com/codex/subagents)
- [Gemini subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md)

**Agent Forge alignment:** Verified in Track 4a of `docs/plans/feat-sota-2026-alignment.md`. If drift confirmed, the renderer is fixed there.

### 2.2 Hooks

Gemini fires semantically distinct lifecycle events that don't map 1:1 to Claude/Codex.

| Canonical concept | Claude | Codex | Gemini |
|---|---|---|---|
| Before tool execution | `PreToolUse` | `PreToolUse` | `BeforeTool` |
| After tool execution | `PostToolUse` | `PostToolUse` | `AfterTool` |
| Before tool selection | (none) | (none) | `BeforeToolSelection` |
| Before model inference | (none) | (none) | `AfterModel` (note: name is post-model-response) |
| Before subagent spawn | `SubagentStart` | `SubagentStart` | `BeforeAgent` (semantically broader) |
| After subagent finish | `SubagentStop` | `SubagentStop` | `AfterAgent` |
| Session start | `SessionStart` | `SessionStart` | `SessionStart` |
| Session end | `SessionEnd` | (none) | `SessionEnd` |
| Stop / interrupt | `Stop` | `Stop` | (uses `SessionEnd`) |
| Permission request | `PermissionRequest` | `PermissionRequest` | (none) |
| User prompt submit | `UserPromptSubmit` | `UserPromptSubmit` | (none) |
| Pre-compact | `PreCompact` | `PreCompact` | `PreCompress` |
| Post-compact | `PostCompact` | `PostCompact` | (none) |

The `BeforeToolSelection`, `AfterModel`, `BeforeAgent`, and `AfterAgent` events are Gemini-only and have no Claude / Codex equivalent. A canonical hook policy that only represents the Claude/Codex superset cannot author records that fire on these events.

**Primary sources:**
- [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Codex hooks](https://developers.openai.com/codex/hooks)
- [Gemini writing-hooks docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/writing-hooks.md)

**Agent Forge alignment:** Track 4b extends the canonical event list with the four Gemini-only events. Aliases set to `None` for Claude and Codex; the PascalCase native name for Gemini. The factory already drops records with `None` aliases for a given host; this composes cleanly.

### 2.3 Native Auto-Memory

Only Claude documents a native cross-session auto-memory layer. Codex and Gemini docs do not describe an equivalent automatic memory.

- **Claude:** `~/.claude/projects/<encoded>/memory/MEMORY.md` is auto-loaded at session start (first 200 lines / ~25 KB). Topic files in the same directory load on demand.
- **Codex:** No native auto-memory documented. Project-local `AGENTS.md` (and `AGENTS.override.md`) provide instruction-level context but are not session-state.
- **Gemini:** No native auto-memory documented. `GEMINI.md` plays the boot-file role.

**Agent Forge alignment:** Already documented honestly in `docs/CONOPS.md` under "Native vs Sidecar Surfaces." The memory bridge writes outbound to all three hosts (native target for Claude, sidecar for Codex/Gemini at `.codex/memory/AGENTS_MEMORY.md` and `.gemini/memory/MEMORY.md`). Inbound sync from Codex/Gemini is best-effort; only Claude's bridge has a native two-way contract. No drift; the conservatism is already documented.

### 2.4 AGENTS.md — convention, not standard

`AGENTS.md` is a cross-vendor convention but not a formal standard. Each vendor reads it differently:

- **Claude Code:** Reads `AGENTS.md` as optional companion to `CLAUDE.md`; `/init` incorporates relevant parts into auto-generated `CLAUDE.md`. The recommendation in Claude docs: "If your repository already uses `AGENTS.md` for other coding agents, create a `CLAUDE.md` that imports it. A symlink also works."
- **OpenAI Codex:** Reads hierarchically (global `~/.codex/`, then project `.codex/`, then project root). Supports an `AGENTS.override.md` precedence file at project root that overrides the parent-tree `AGENTS.md` for that project's Codex session.
- **Gemini CLI:** Does not natively read `AGENTS.md`; uses `GEMINI.md`.

**Primary sources:**
- [Codex AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [Claude Code memory docs](https://code.claude.com/docs/en/memory)

**Agent Forge alignment:** Track 4c stubs `AGENTS.override.md` on bootstrap and instructs the renderer to leave it alone if it contains non-comment content.

---

## Section 3 — Verified Academic Citations (Load-Bearing for Architecture)

Use these citations as the warrant when proposing a design decision that invokes "industry research." Each was verified by the claim-verification agent (2026-05-22).

### 3.1 SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

- **Authors:** Yang, Jimenez, et al. (Princeton)
- **Venue:** NeurIPS 2024
- **Primary source:** [NeurIPS 2024 proceedings paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf) | [Project page](https://swe-agent.com/)
- **Finding:** Standard terminal environments are poorly suited for LLMs. Restricting agents to an Agent-Computer Interface (ACI) with rigid, single-purpose tools (file viewer capped at 100 lines, linter-guarded editing) improved GPT-4 performance on SWE-bench Lite by 10.7 percentage points.
- **What this justifies:** Consolidating overlapping tools and skills. The `efc74b8 great consolidation` commit was warranted by this finding.
- **What this does NOT justify:** Mandating any one specific tool set without verification that overlap actually exists.

### 3.2 Context Rot: How Increasing Input Tokens Impacts LLM Performance

- **Authors:** Chroma Research
- **Venue:** Technical report, July 2025
- **Primary source:** [Context Rot research page](https://research.trychroma.com/context-rot)
- **Finding:** Evaluated 18 LLMs (GPT-4.1, Claude 4, Gemini 2.5, Qwen3). Performance degrades with input length even on simple retrieval/replication tasks; placement of information matters more than presence.
- **What this justifies:** Tiered memory, bounded-decay distillation, progressive disclosure on skill bodies. Already present in Agent Forge via `policies/distillation.json` + `lesson-distiller` + `handoff-archiver`.
- **What this does NOT justify:** Aggressive context truncation that loses semantic anchors.

### 3.3 Lost in the Middle: How Language Models Use Long Contexts

- **Authors:** Liu et al. (Stanford / UC Berkeley / Samaya AI)
- **Venue:** TACL 2024
- **Primary source:** [arXiv 2307.03172](https://arxiv.org/abs/2307.03172) | [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/)
- **Finding:** Language models perform best when relevant information appears at the beginning or end of context; performance degrades when relevant information is in the middle, even for long-context models.
- **What this justifies:** Putting the most important canonical instructions at the top of `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`. Putting acceptance criteria near the top of long `SKILL.md` files.
- **What this does NOT justify:** Reordering existing skill bodies without operator review.

### 3.4 LLMs Get Lost in Multi-Turn Conversation

- **Authors:** Laban et al.
- **Venue:** ICLR 2026 (Best Paper Award)
- **Primary source:** [arXiv **2505.06120**](https://arxiv.org/abs/2505.06120)
- **CITATION ERROR FLAG:** The handover prompt circulating in earlier planning sessions cited arXiv `2505.09111` — **that is wrong**. `2505.09111` is a cosmic-ray neutrino-detector physics paper, unrelated. Use **2505.06120**.
- **Finding:** 39% average performance drop in multi-turn conversations vs. single-turn equivalents. Agents forget early architectural constraints as the conversation accumulates noise.
- **What this justifies:** Plan persistence to disk (already shipped via Track F). Subagent dispatch with fresh context (already shipped via `subagent-dispatcher`). Periodic re-grounding on canonical files.
- **What this does NOT justify:** Hard caps on conversation length without operator override.

### 3.5 LangGraph: Multi-Agent Workflows at Scale

- **Authors:** LangChain
- **Venue:** Production framework, 2024-2025
- **Primary source:** [LangChain blog](https://blog.langchain.com/langgraph-multi-agent-workflows/) | [GitHub repo](https://github.com/langchain-ai/langgraph)
- **Finding:** Complex multi-agent workflows benefit from being modeled as Directed Acyclic Graphs (DAGs) or State Machines with externalized state, rather than unstructured chat threads. Agents as Nodes, state passed via Edges as JSON. Supports persistence, streaming, human-in-the-loop.
- **What this justifies:** The state-machine dispatcher introduced in `efc74b8 great consolidation`. Checkpoint persistence as a follow-on enhancement.
- **What this does NOT justify:** Forcing every multi-step workflow through a DAG when sequential delegation suffices.

### 3.6 Code as Agent Harness (recent — caveat emptor)

- **Authors:** Ning, Tieu, Fu, et al.
- **Venue:** arXiv preprint, May 18 2026
- **Primary source:** [arXiv 2605.18747](https://arxiv.org/abs/2605.18747)
- **Caveat:** Posted 4 days before this audit was written. Not yet peer-reviewed. Treat findings as preliminary.
- **Finding:** Surveys code as foundational infrastructure for agents (harness interface, planning, memory, tool use). Argues for execution traces as a verification surface.
- **What this might justify (pending community review):** A semantic-trace requirement on `verification-gate` (agent must provide line-by-line justification of how implementation matches spec).
- **Action:** Track as watch-item. Do not mandate a new gate until the paper has community review (~1-2 months).

### 3.7 GenericAgent (GA) — Fudan

- **Authors:** Fudan / Shenzhen Aquaintelling
- **Venue:** arXiv preprint, April 21 2026
- **Primary source:** [arXiv 2604.17091](https://arxiv.org/abs/2604.17091)
- **Finding:** Token-efficient LLM agent with hierarchical memory, minimal tool sets, self-evolving SOPs. Core principle: contextual information density maximization.
- **What this justifies:** The factory's existing context-frugality discipline (`token-optimizer`, `context-engineer`). Append-first + bounded-decay already implements "self-evolving SOPs" via `lesson-distiller`. No new code needed; cite this as the warrant in `state-of-the-field`.

---

## Section 4 — Discarded Claims (NOT Load-Bearing)

The following appeared in a handover prompt circulating in earlier planning sessions. Each was investigated; each is excluded as a SOTA citation. They are listed here so future agents don't re-encounter them blind.

### 4.1 KAIROS and `/dream` memory distillation

- **Status:** **Unverifiable as peer-reviewed research.** Confirmed as **leaked unreleased Claude Code features** (March-April 2026 npm-package source leak).
- **Evidence:** Secondary-source coverage of the leak: [Alex Kim's blog](https://alex000kim.com/posts/2026-03-31-claude-code-source-leak/), [TechSy.io coverage](https://techsy.io/en/blog/claude-code-leaked-features-2026), [DEV.to reverse-engineering writeup](https://dev.to/mike_w_06c113a8d0bb14c793/we-reverse-engineered-kairos-from-the-claude-code-leak-heres-the-open-version-48dc).
- **Why excluded:** Leaked unreleased product roadmap is not an authoritative SOTA citation. If Anthropic ships KAIROS or `/dream` officially, the official docs become the citation; until then, the patterns can inspire but cannot warrant architectural mandates.
- **What was claimed but not justified:** "Implement Logic Traces" and "Memory Distillation" as KAIROS-driven. Both can be motivated by **Code as Agent Harness** (3.6) and **GenericAgent** (3.7) instead — those are real papers.

### 4.2 Stanford-Fudan KAIROS / Semantic Trace collaboration 2026

- **Status:** **No evidence found.** Likely fabricated conflation.
- **What might have caused the confusion:** There is a real KAIROS paper from Alibaba / Tsinghua on multi-agent scheduling ([arXiv 2508.06948](https://arxiv.org/abs/2508.06948)) — different KAIROS, different scope (latency optimization, not orchestration patterns). The handover prompt appears to have mashed together the Claude Code leak's "KAIROS" with this unrelated paper's title.
- **Why excluded:** A peer-reviewed Stanford-Fudan collaboration under those exact terms could not be located on arXiv, ACL, NeurIPS, ICLR, or via direct institutional search. The citation is unverifiable; treating it as authority would propagate misinformation.

### 4.3 "Fudan GA paper" cited generically without arXiv ID

- **Status:** Partially resolved — the real paper is GenericAgent (Section 3.7, arXiv 2604.17091). The handover prompt's generic reference was correct in spirit but lacked the citation.
- **Action:** Cite the specific arXiv ID going forward.

---

## Section 5 — Verified Agent Forge Drift Surfaces (Acted On In `feat/sota-2026-alignment`)

Each drift surface below is being addressed in the current sprint or explicitly documented as out-of-scope. Status updated as tracks land.

### 5.1 Codex subagent rendering — VERIFIED NON-DRIFT (2026-05-22)

- **2026 standard:** Codex 2026 requires TOML in `.codex/agents/`. The primary-source research agent inferred a `[agent]` section wrapper but did not read an actual rendered file.
- **Agent Forge state on verification:** `omni_factory.py` already renders `.codex/agents/<skill>.toml` files with flat top-level keys (`agent_forge_managed`, `name`, `description`, `sandbox_mode`, `developer_instructions`) plus `[[skills.config]]` for the SKILL.md reference. `tomllib.load()` succeeds on every rendered file across five different governed projects. The flat-top-level layout is valid TOML and matches Codex's documented expected schema; the `[agent]` wrapper was a stylistic inference, not a documented requirement.
- **Track:** 4a — verified non-drift. No code change. Lesson appended to `docs/LESSONS_LEARNED.md` (`2026-05-22 — Codex subagents already render as TOML`). Promotion target: `docs/HOST_INTEGRATIONS.md` § Codex subagent rendering, to document the actual schema so this verification doesn't have to be redone.

### 5.2 Gemini-only hook events — VERIFIED REPRESENTED + DOCUMENTED (2026-05-22)

- **2026 standard:** Gemini fires `BeforeAgent`, `AfterAgent`, `BeforeToolSelection`, `AfterModel`, `BeforeModel` — no Claude / Codex equivalents.
- **Agent Forge state on verification:** All five events are already present in `scripts/omni_factory.py:_EVENT_ALIASES` (`before_agent`, `after_agent`, `before_tool_selection`, `after_model`, `before_model`) with `None` aliases for Claude and Codex and the matching PascalCase native names for Gemini. This was wired in by an earlier SOTA pass; the canonical schema represents the events even though no current `policies/hooks.json` record uses them.
- **Track:** 4b — verified represented in code. The work is documentation only: `docs/CONOPS.md` § Hook Governance gains a fourth bullet explicitly allowing host-specific canonical events; `policies/hooks.json` description string gains a sentence naming the Gemini-only events and the None-alias drop behavior, so a future author reading the canonical file knows the asymmetry is intentional.

### 5.3 `AGENTS.override.md` precedence (Codex) — IMPLEMENTED (2026-05-22)

- **2026 standard:** Codex reads `AGENTS.override.md` (project root) with precedence over the parent-tree `AGENTS.md`.
- **Agent Forge state on close:** `scripts/bootstrap-project.sh` now stubs `AGENTS.override.md` with a comment-only header when scaffolding a new governed project. The stub creation is idempotent (`[[ ! -f ... ]]` guard), so re-running bootstrap on an existing project never clobbers an operator's project-local overrides. The omni-factory renderers were already silent on `AGENTS.override.md` — no code change needed there (verified via `grep`).
- **Track:** 4c — closed. `docs/CONOPS.md` § Codex AGENTS.md Override Precedence added under "Native vs Sidecar Surfaces" documenting the precedence model and the operator-authored / factory-skipped contract.

### 5.4 `targets:` field labeled as standard — LABELED AS LOCAL EXTENSION (2026-05-22)

- **2026 standard:** `agentskills.io` defines `name` and `description` as required; treats skills as host-portable by default. `targets:`, `capability_class:`, `delivery_projects:`, `claude_command_name:`, `gemini_command_name:`, `codex_sandbox_mode:`, and `requires_mcp_servers:` are **not** in the standard.
- **Agent Forge state on close:** All seven extensions are now explicitly labeled as Agent Forge local extensions in two places: `docs/CONOPS.md` § Standard vs Local Extensions (under "Capability Model") and `skills/global/skill-author/SKILL.md` § Frontmatter contract. The `state-of-the-field` explainer in `EXPLAINERS.md` already named the same distinction in Track 3. Contributors reading any of these surfaces now know the renderer is what parses these fields, not the host CLIs themselves.
- **Track:** 4d — closed. Documentation-only. No code change.

---

## Section 6 — Watch Items (Not Acted On This Sprint)

- **Semantic-trace requirement on verification-gate.** Warranted by **Code as Agent Harness** (3.6) but the paper is too recent (4 days old) to mandate a new architectural gate. Revisit next sprint after community review accumulates.
- **State-machine dispatcher checkpoint persistence.** Warranted by **LangGraph** (3.5). The `efc74b8 great consolidation` commit introduced a state-machine dispatcher; verify its checkpoint capabilities before adding new code. If checkpoint persistence is missing, add in a focused follow-on sprint.
- **Memory-distiller skill / `/dream` pattern.** Inspired by leaked Claude Code features (Section 4.1). Not warranted by peer-reviewed research alone. If implemented later, must be cited honestly as "inspired by leaked Claude Code roadmap, not academic SOTA."
- **Further skill / team consolidation per SWE-agent ACI principles.** The recent commits already executed "the great consolidation." Further consolidation risks churning settled work. Revisit after one sprint of operational use.

---

## Section 7 — 2026-05-23 Deep Audit Delta

This section amends the 2026-05-22 baseline without rewriting it. Treat the items below as the current correction layer for vendor-surface decisions until the next dated audit.

### 7.1 Claude hooks are broader than the baseline table

Claude Code's current hooks reference enumerates 27+ lifecycle events, including newer or under-modeled events such as `Setup`, `InstructionsLoaded`, `UserPromptExpansion`, `PostToolUseFailure`, `PostToolBatch`, `PermissionDenied`, `TaskCreated`, `TaskCompleted`, `StopFailure`, `TeammateIdle`, `ConfigChange`, `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `Elicitation`, and `ElicitationResult`, in addition to the events captured in the earlier cross-vendor table.

**Agent Forge implication:** `scripts/omni_factory.py:_EVENT_ALIASES` intentionally covers a broad canonical set, but `policies/hooks.json` exercises only a small live subset. A future hook-expansion sprint should distinguish "known to render" from "actively exercised by policy" and add fixtures before enabling new lifecycle controls.

**Primary source:** [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)

### 7.2 Gemini hook semantics are control-flow primitives, not just aliases

Gemini's hook docs demonstrate four lifecycle controls that require first-class modeling:

- `BeforeAgent` can inject additional context before the agent loop starts.
- `BeforeToolSelection` can set tool mode (`AUTO`, `ANY`, `NONE`) and whitelist candidate tools before the model chooses.
- `AfterModel` observes model request/response content and can support streaming-era logging or redaction patterns.
- `AfterAgent` can validate the final response and block it to trigger a retry.

**Agent Forge implication:** The canonical schema already declares these Gemini-only event names with `None` aliases for Claude and Codex. The missing piece is policy coverage: no active hook currently exercises those records, so runtime assurance is shallow for these semantics.

**Primary source:** [Gemini CLI writing hooks](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/writing-hooks.md)

### 7.3 Codex subagent and MCP config details need renderer follow-up

Codex subagent files are TOML and current docs name optional fields such as `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`. Codex MCP configuration uses `[mcp_servers.<name>]` tables in `config.toml`, including nested env/header/tool-policy tables.

**Agent Forge implication:** The previous "flat TOML" conclusion remains directionally correct, but Agent Forge's renderer/docs still need explicit coverage for `model_reasoning_effort` and per-agent `mcp_servers` inheritance so future authors do not assume Claude/Gemini frontmatter fields map directly.

**Primary sources:** [Codex subagents](https://developers.openai.com/codex/subagents), [Codex MCP](https://developers.openai.com/codex/mcp)

### 7.4 MCP convergence is protocol-level; host config files diverge

MCP 2025-11-25 standardizes JSON-RPC 2.0 communication, server features (Resources, Prompts, Tools), and client features (Sampling, Roots, Elicitation). That does not mean host configuration files share one schema. Claude Code project MCP uses `.mcp.json` with `mcpServers`, Codex uses TOML `[mcp_servers.<name>]` tables, and Gemini uses `mcpServers` in `.gemini/settings.json`.

**Agent Forge implication:** `global-mcp.json` remains the correct canonical inventory, but docs should say "rendered to host-native config shapes" rather than "field names are identical across hosts." The earlier 2026-05-22 claim was overbroad at the config-file layer.

**Primary sources:** [MCP specification 2025-11-25](https://modelcontextprotocol.io/specification/latest), [Claude Code MCP](https://code.claude.com/docs/en/mcp), [Codex MCP](https://developers.openai.com/codex/mcp), [Gemini CLI configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/configuration.md)

### 7.5 Prompt caching is a load-bearing cost doctrine

Anthropic's prompt caching docs make stable-prefix design operational. Cache prefixes are built over `tools`, then `system`, then `messages`; static content belongs before variable content, and the cache breakpoint should sit on the last reusable block. Timestamps, request IDs, session-unique labels, and other per-turn values before the breakpoint create new hashes and destroy cache reuse.

**Agent Forge implication:** Progressive disclosure, tiered memory, and bounded-decay docs already reduce context load. The new doctrine is economic: keep host boot prompts, tool definitions, and canonical skill summaries stable and push volatile cursor/task details later. This should inform future renderer changes and API-harness integrations.

**Primary source:** [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

---

## Section 8 — Revision History

| Date | Editor | Change |
|---|---|---|
| 2026-05-23 | Codex (under operator-approved deep-refactor plan) | Added deep audit delta: Claude hook breadth, Gemini hook control-flow semantics, Codex `model_reasoning_effort` / `mcp_servers` details, MCP config-file divergence, and Anthropic prompt-caching doctrine. |
| 2026-05-22 | Opus 4.7 (under operator approval) | Initial audit. Phase 1 research baseline captured; four drift surfaces identified; six watch-items recorded; KAIROS/dream/Stanford-Fudan-collab claims rejected with evidence. |

When updating this file, append a row above. Do not silently rewrite earlier claims — the audit history is itself a load-bearing artifact for future agents.
