# Onboarding-Guide Explainers

Plain-English explanations of the agentic vocabulary used by Agent Forge. One section per topic; topics are alphabetical.

When the operator asks "what is X?" during the inline tour, or when the operator types `/onboarding-guide explain <topic>`, the assistant reads the matching `## <topic>` section below and serves it back in chat.

The terminal-mode helper `onboard.py explain <topic>` reads the same sections so there is one source of truth.

---

## agent

An agent is an autonomous something that can read, write, plan, call tools, and remember between turns. In this factory, an agent is one of the three host CLIs (Claude, Codex, or Gemini) running on your machine. A skill is what an agent reads to know how to behave for a specific job. A subagent is an agent dispatched by another agent to handle a focused task with its own fresh context — useful when you want to keep the main agent's working memory clean while a side task runs. All three host CLIs now use the same `SKILL.md` format (via the [agentskills.io](https://agentskills.io) open standard) for both workflow-class and expert-class capabilities. They differ on invocation and subagent schema: Claude invokes skills via `/name` and subagents via `@name` (YAML-frontmatter markdown in `.claude/agents/`); Codex invokes skills via the `/skills` menu or `$name` mention and subagents via delegation (TOML in `.codex/agents/`); Gemini auto-activates skills via tool call and invokes subagents via `@name` (YAML-frontmatter markdown in `.gemini/agents/`).

---

## agent-team

A team in this factory is a portable role contract. It lives at `teams/<name>.json` and says "a research team has these roles, escalates like this, collapses like this" — but it is a governance manifest, not a process the host runs. Teams describe how a group of skills and agents would work together on a complex job; the operator (you) decides whether to actually dispatch them. The seeded teams (assessment, bootstrap, delivery, governance, improvement, planning, research) carry `claude_mapping`, `codex_mapping`, and `gemini_mapping` blocks that name the host-native primitives each team prefers.

---

## bootstrap

Bootstrapping is the one-time setup. `scripts/bootstrap-workstation.sh` installs the three host CLIs (Claude / Codex / Gemini) on a fresh Linux or macOS machine; `scripts/bootstrap-workstation.ps1` performs the Windows prerequisite check and can install common tools through `winget` when available. `scripts/bootstrap-project.sh --name <foo>` creates a new governed project with the minimum required files and immediately syncs Claude / Codex / Gemini surfaces into it. `scripts/deploy-and-bootstrap.sh` is the one-shot Linux/macOS operator path from a freshly unpacked suitcase; `scripts/deploy-and-bootstrap.ps1` is the Windows path that unblocks and expands the ZIP before deployment.

---

## claude-cli

Claude Code is Anthropic's coding-agent CLI. It loads `CLAUDE.md` boot files hierarchically (current directory walking up), has a true machine-local auto-memory at `~/.claude/projects/<encoded>/memory/MEMORY.md`, and exposes two kinds of authored capabilities: skills invoked as `/name` (the [agentskills.io](https://agentskills.io) `SKILL.md` standard, stored at `.claude/skills/<name>/`) and subagents invoked as `@name` (stored at `.claude/agents/<name>.md`). The Claude docs explicitly state that "custom commands have been merged into skills" — a file at `.claude/commands/<name>.md` and a skill at `.claude/skills/<name>/SKILL.md` both create `/name` and work the same way. Settings live at `~/.claude/settings.json` (user-global) and `<project>/.claude/settings.json` (project-local, takes precedence). Permission modes range from `default` (ask) to `bypassPermissions` (don't ask). When to pick this host: when you want the deepest native primitive coverage and the most polished memory story.

---

## codex-cli

OpenAI Codex is a coding-agent CLI with a strong default sandbox. On Linux it uses bubblewrap (`bwrap`); on macOS it uses Seatbelt. Skills are invoked via the `/skills` menu, by `$name` mention, or autonomously when a task matches a skill's description; subagents are invoked via delegation (no `@name` convention like Claude / Gemini). Codex implements the [agentskills.io](https://agentskills.io) standard and reads skills from `.agents/skills/` (walking up to the repo root) and `~/.agents/skills/`. Subagents render as TOML in `.codex/agents/` — see `developers.openai.com/codex/subagents`. The boot file is `AGENTS.md` (walks up the directory tree like Claude's `CLAUDE.md`), with project-local `AGENTS.override.md` taking precedence. Codex has no native auto-memory, so Agent Forge bridges the canonical `MEMORY.md` to a sidecar at `<project>/.codex/memory/AGENTS_MEMORY.md` and points Codex at it. Settings live in `<project>/.codex/config.toml`. When to pick this host: when you want the strongest default sandbox or when you're on a network where Codex is the only allowed coding agent.

---

## factory

The "factory" is the `_agent_forge/` folder. It is a single source of truth that holds canonical definitions of skills, safety rules, shared memory sections, team manifests, and MCP server inventory, plus a Python engine (`scripts/omni_factory.py`) that translates those definitions into Claude Code, OpenAI Codex, and Gemini CLI configuration files. You only ever edit the canonical sources; the engine generates the host-specific files. After every change, a runtime validator asks each host's CLI "can you actually see what we just shipped?" — that's the gate.

---

## gemini-cli

Gemini CLI is Google's coding-agent CLI. It loads `GEMINI.md` boot files hierarchically and is vision-capable. Gemini implements the [agentskills.io](https://agentskills.io) `SKILL.md` standard; skills are read from `.gemini/skills/` or `.agents/skills/` (`.agents/skills/` precedes within tier), and the model auto-activates a matching skill via the `activate_skill` tool call with a UI confirmation prompt. The factory also delivers thin command and subagent surfaces under `<project>/.gemini/commands/` and `<project>/.gemini/agents/` for skills authored before the standard. Subagents are invoked as `@subagent-name`. Gemini supports a different subset of hook events than Claude / Codex — events like `BeforeAgent`, `BeforeToolSelection`, `AfterModel`, and `AfterAgent` are Gemini-only and don't have Claude / Codex equivalents; the factory's canonical event list includes them with `None` aliases for the other two hosts. Settings live in `<project>/.gemini/settings.json`. Like Codex, Gemini has no native auto-memory; a sidecar at `<project>/.gemini/memory/MEMORY.md` carries the bridge. When to pick this host: when you need a vision-capable agent or want the most cost-efficient non-trivial tier.

---

## governed-project

A governed project is one declared in `projects.json` and managed by the factory. On a fresh install, no projects are pre-wired — `projects.json` is an empty list. Adding your first one means: (1) add an entry to `projects.json` with `name`, `root`, and `required_files`; (2) run `./scripts/bootstrap-project.sh --name <name>`. The bootstrap creates the minimum required files, then immediately syncs the factory's skills, hooks, MEMORY.md, and forge_state into the project's host-native directories (`.claude/`, `.codex/`, `.agents/`, `.gemini/`). Generated surfaces are never hand-edited; re-run sync after any canonical change. The `required_files` declaration is what the verifier uses to confirm the project still has the minimum footprint.

---

## guardian

`telemetry-guardian` is the universal pre-tool seatbelt. Python-first (`skills/global/telemetry-guardian/guardian.py`) so it runs natively on Windows, macOS, and Linux without bash — important on no-WSL native Windows. A thin `guardian.sh` POSIX forwarder is kept for legacy hook records that still point at the bash entry point. Reads one tool invocation on stdin, matches the command against a fixed deny list, exits 0 to allow or 1 to block. Bypass via `AGENT_FORGE_GUARDIAN=off` env var; every bypass is logged. Intentionally dumb — predictability beats sophistication for safety gates. The deny list covers `--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777, `--no-gpg-sign`, explicit `git reset --hard <ref>`.

---

## hook

A hook is a script that runs at a specific moment in a host CLI's tool-call lifecycle. The most common hook in this factory is `pre-tool-execution-guardian` — it runs before every Bash tool call, reads the command, and either lets it through or refuses. Hook records live in `policies/hooks.json`. The factory translates one canonical record into each host's native event names (Claude `PreToolUse`, Codex `PreToolUse`, Gemini `BeforeTool`). Some events are host-specific — Gemini has `BeforeAgent` / `BeforeToolSelection` / `AfterModel` / `AfterAgent` events that don't exist on Claude / Codex; canonical records for those events alias to `None` on the other two hosts and the renderer drops them silently.

---

## host-dirs

The factory writes to four different config directory names depending on the host. Claude reads from `.claude/`. Codex reads from `.codex/` and also from `.agents/skills/`. Gemini reads from `.gemini/` and also from `.agents/skills/`. The `.agents/skills/` directory is the cross-vendor [agentskills.io](https://agentskills.io) standard alias; the host-specific directories (`.codex/`, `.gemini/`) take precedence within their own tier. The factory keeps all of these in sync from one canonical source, so if you ever see drift between them, that's a bug — not a feature. The triad runtime validator (`validate-triad-runtime.py`) is the gate that catches that drift before it ships.

---

## mcp

MCP (Model Context Protocol) is the open standard that lets an AI agent call external tools — GitHub, Slack, your internal services. The current spec is [MCP 2025-11-25](https://modelcontextprotocol.io/specification/latest) and all three host CLIs implement the same protocol concepts: JSON-RPC 2.0 transport, server features (Resources, Prompts, Tools), and client features (Sampling, Roots, Elicitation). Host config files are not identical: Claude reads project MCP from `<project>/.mcp.json`, Codex renders MCP as `[mcp_servers.<name>]` TOML tables in `<project>/.codex/config.toml`, and Gemini uses an `mcpServers` object in `<project>/.gemini/settings.json`. The factory declares shared MCP servers in `global-mcp.json` and translates that one canonical record into each native shape.

---

## memory

The shared memory layer is one Markdown file per project, at `<project>/MEMORY.md`. Five sections: build commands, project quirks, active tasks, recent decisions, known failures. The schema is defined in `policies/memory.json`. All three host CLIs read this file. The `memory-archivist` skill (`append`/`validate`/`summary`) writes to it; entries are timestamped and tagged by host. Append-first; secrets-deny at write time. Only Claude has documented native auto-memory; for Codex and Gemini the factory bridges to sidecar files (`.codex/memory/AGENTS_MEMORY.md`, `.gemini/memory/MEMORY.md`) — outbound from canonical works on all three, inbound has a true native target only on Claude.

---

## prompt-caching

Prompt caching is a Claude API feature that lets repeated prompt prefixes be reused instead of paid and processed as fresh input every time. Anthropic documents automatic caching and explicit cache breakpoints in its [prompt caching guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching). For long-running agents, this is a cost and latency lever because the stable parts of a request — tool definitions, system instructions, project context, and durable examples — can be cached while the new user message remains uncached.

The core design rule is stability before variability. Put the most stable material first and mark the end of the reusable prefix: tools, system instructions, then stable messages or examples, then per-request material. A small change before the cache breakpoint creates a different prefix hash, so cache-friendly harnesses keep doctrine, tools, and reusable context byte-stable across turns.

Avoid putting timestamps, request IDs, random session labels, or other per-turn data near the top of a request. Put variable content after the cached prefix. In Agent Forge terms, canonical doctrine and progressive-disclosure skill summaries are good cache-prefix candidates; live task notes, cursor snippets, and user-specific one-off details belong later.

---

## sandbox

Each host CLI runs your tool calls inside some kind of isolation. Codex CLI uses Linux bubblewrap (`bwrap`) on Debian/Ubuntu and macOS Seatbelt on macOS. Claude has permission modes (`default`, `plan`, `acceptEdits`, `auto`, `bypassPermissions`). Gemini gates on trusted-folder state. The factory is sandbox-aware: when the runtime validator can't inspect Codex via its shell tool because bwrap blocked the loopback interface, it escalates to filesystem evidence per documented doctrine.

---

## skill

A skill is a packaged, reusable workflow. It lives at `skills/global/<name>/SKILL.md` (for cross-project skills) or `skills/projects/<project>/<name>/SKILL.md` (for project-local). The frontmatter declares the metadata (which hosts, which projects, workflow vs. expert class). The body is the durable instruction text. The format follows the [agentskills.io](https://agentskills.io) open standard which all three hosts now implement: `name` and `description` are required, the body is loaded lazily when the skill is invoked (progressive disclosure). Agent Forge adds optional fields like `targets:`, `capability_class:`, and `delivery_projects:` as Agent Forge **local extensions** — they are not part of agentskills.io itself. The renderer honors them; an omitted `targets:` defaults to delivery on all three hosts.

---

## state-of-the-field

*Last reviewed against vendor docs: 2026-05-23. Re-verify before relying on specifics. The source-of-truth for what was actually checked is `docs/SOTA_2026_AUDIT.md`.*

**What has converged across Claude / Codex / Gemini (the cross-vendor SOTA):**

- **Skills** — all three vendors adopted the [agentskills.io](https://agentskills.io) open standard. `SKILL.md` with YAML frontmatter, progressive disclosure (`name` + `description` load eagerly, full body lazily). Optional siblings: `scripts/`, `references/`, `assets/`.
- **MCP** — all three implement the [Model Context Protocol 2025-11-25 spec](https://modelcontextprotocol.io/specification/latest). JSON-RPC 2.0 transport, Resources / Prompts / Tools server features, and Sampling / Roots / Elicitation client features are converged at the protocol level. Per-host config files still diverge: Claude project `.mcp.json`, Codex `[mcp_servers.<name>]` TOML tables in `.codex/config.toml`, and Gemini `mcpServers` objects in `.gemini/settings.json`.

**What has NOT converged:**

- **Hooks** — Gemini fires `BeforeAgent`, `BeforeToolSelection`, `AfterModel`, `AfterAgent` events that don't exist on Claude / Codex (they're semantically distinct, not just renamed). The factory's canonical hook schema includes them with `None` aliases for the other two hosts; the renderer drops them silently for hosts that lack the event.
- **Subagents** — Codex uses **TOML** in `.codex/agents/` (`[agent]` section, `developer_instructions`, `sandbox_mode`); Claude and Gemini use YAML-frontmatter markdown. Not interchangeable. The factory's renderer writes the right format per host.
- **Native auto-memory** — only Claude has documented native cross-session memory (`~/.claude/projects/<encoded>/memory/MEMORY.md`, auto-loaded). Codex and Gemini have no documented equivalent. The factory bridges outbound from canonical `MEMORY.md` to sidecar files (`.codex/memory/AGENTS_MEMORY.md`, `.gemini/memory/MEMORY.md`); inbound sync has a true native target only on Claude.
- **`AGENTS.md`** — a convention, not a formal standard. Codex specifically supports an `AGENTS.override.md` precedence file (project-local overrides parent-tree `AGENTS.md`); the factory honors this on bootstrap.

**Where the field is going (what the research says):**

- *Long-context degradation is real.* [Context Rot (Chroma, July 2025)](https://research.trychroma.com/context-rot) and [Lost in the Middle (Liu et al., TACL 2023, arXiv 2307.03172)](https://arxiv.org/abs/2307.03172) show that LLM performance drops as input grows, even on simple retrieval. The factory's response is tiered memory + bounded-decay distillation: append-first in `LESSONS_LEARNED.md` and `HANDOFF.md`, archive-on-promote via `lesson-distiller` and `handoff-archiver`. Keep the most important instructions at the top of canonical files; the middle of long contexts is where attention degrades.
- *Multi-turn agents forget.* [LLMs Get Lost in Multi-Turn Conversation (Laban et al., arXiv 2505.06120, submitted May 2025)](https://arxiv.org/abs/2505.06120) measured a 39% average performance drop across six generation tasks in multi-turn vs single-turn evaluation. The factory's response is plan persistence (`docs/plans/<branch-slug>.md`) and subagent dispatch with fresh context.
- *Tool overlap hurts agents.* [SWE-agent (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf) showed restricting agents to rigid, single-purpose tools improved GPT-4 on SWE-bench Lite by 10.7 percentage points. The factory's recent "great consolidation" (commit `efc74b8`) merged overlapping planner / reviewer skills with this finding as the warrant.
- *Cost lever available today: prompt caching.* Anthropic's [prompt caching guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) makes stable-prefix design operational: keep tools, system instructions, and reusable context stable before per-request content, then cache that prefix. See `prompt-caching` for the operator-level explanation.

**Why this matters to you, the operator:** the rate of change in this field is high. A vendor doc you read three months ago may no longer be accurate. `docs/SOTA_2026_AUDIT.md` is dated and re-verifiable; when in doubt, re-check primary sources before acting on a memory of how things used to work.

---

## suitcase

The "suitcase" is the portable export of the factory you can carry to a fresh machine or VM without copying secrets or per-machine residue. `scripts/factory-export.sh` produces `agent-forge-suitcase-<timestamp>.tar.gz` (and `.zip`) in `exports/`. The bundle includes `_agent_forge/` canonical sources, the sync/bootstrap/validation scripts, and the doctrine docs — no `.env`, no auth tokens, no machine-local caches. On Linux/macOS, run `./_agent_forge/scripts/deploy-and-bootstrap.sh`. On Windows, run the sidecar `agent-forge-suitcase-<timestamp>-deploy-and-bootstrap.ps1` against the ZIP so PowerShell unblocks the transferred file before extraction. The host-specific surfaces (`<project>/.claude/`, `.codex/`, `.gemini/`) and per-project `MEMORY.md` are re-rendered on first sync; they are NOT carried in the suitcase. This is the canonical-first doctrine in practice: ship the source of truth; let the engine generate the host views fresh on the target.

---

## triad-validator

`scripts/validate-triad-runtime.py` is the runtime gate. It does three things per host: asks the actual CLI to enumerate its visible skills (the surface check), confirms the seeded `telemetry-guardian` hook is registered with the right event name (the hook surface check), and confirms the `MEMORY.md` shared brain is reachable (the memory surface check). Run it after any canonical change. With `--probe-invocations`, it also fires a real test command and observes whether the hook actually intercepts it.

---

## validation-pyramid

The factory uses three nested gates of increasing depth and decreasing speed. Level 1 — `verify-agent-forge.py` — is the cheapest: it checks file presence, JSON parse, schema-shape, and that referenced scripts exist on disk. Run constantly. Level 2 — `validate-triad-runtime.py` (default mode) — asks each host's CLI to enumerate skills, then confirms the seeded telemetry-guardian hook is registered with the host's expected event key (PreToolUse / PreToolUse / BeforeTool) and that the MEMORY.md surface is reachable. Mandatory after every canonical change. Level 3 — `validate-triad-runtime.py --probe-invocations` — fires a real test command on each host CLI and observes whether the hook actually intercepts it. Slow, opt-in, and the only level that catches host-native semantic drift (the kind that broke the Gemini hook silently for two sprints in 2026-04). Each level is necessary; only the third is sufficient.
