# Onboarding-Guide Explainers

Plain-English explanations of the agentic vocabulary used by Agent Forge. One section per topic; topics are alphabetical.

When the operator asks "what is X?" during the inline tour, or when the operator types `/onboarding-guide explain <topic>`, the assistant reads the matching `## <topic>` section below and serves it back in chat.

The terminal-mode helper `onboard.py explain <topic>` reads the same sections so there is one source of truth.

---

## agent

An agent is an autonomous something that can read, write, plan, call tools, and remember between turns. In this factory, an agent is one of the three host CLIs (Claude, Codex, or Gemini) running on your machine. A skill is what an agent reads to know how to behave for a specific job. A subagent is an agent dispatched by another agent to handle a focused task with its own fresh context — useful when you want to keep the main agent's working memory clean while a side task runs. The factory calls workflow-class skills 'commands' on Claude/Gemini and 'skills' on Codex; it calls expert-class skills 'subagents' on Claude/Gemini (Codex has no native expert-agent primitive).

---

## agent-team

A team in this factory is a portable role contract. It lives at `teams/<name>.json` and says "a research team has these roles, escalates like this, collapses like this" — but it is a governance manifest, not a process the host runs. Teams describe how a group of skills and agents would work together on a complex job; the operator (you) decides whether to actually dispatch them. The seeded teams (assessment, bootstrap, delivery, governance, improvement, planning, research) carry `claude_mapping`, `codex_mapping`, and `gemini_mapping` blocks that name the host-native primitives each team prefers.

---

## bootstrap

Bootstrapping is the one-time setup. `scripts/bootstrap-workstation.sh` installs the three host CLIs (Claude / Codex / Gemini) on a fresh machine. `scripts/bootstrap-project.sh --name <foo>` creates a new governed project with the minimum required files and immediately syncs Claude / Codex / Gemini surfaces into it. `scripts/deploy-and-bootstrap.sh` is the one-shot operator path from a freshly unpacked suitcase: deploys the factory, then offers to run the workstation bootstrap.

---

## claude-cli

Claude Code is Anthropic's coding-agent CLI. It loads `CLAUDE.md` boot files hierarchically (current directory walking up), has a true machine-local auto-memory at `~/.claude/projects/<encoded>/memory/MEMORY.md`, and exposes two kinds of authored capabilities: slash commands invoked as `/name` and subagents invoked as `@name`. Settings live at `~/.claude/settings.json` (user-global) and `<project>/.claude/settings.json` (project-local, takes precedence). Permission modes range from `default` (ask) to `bypassPermissions` (don't ask). When to pick this host: when you want the deepest native primitive coverage and the most polished memory story.

---

## codex-cli

OpenAI Codex is a coding-agent CLI with a strong default sandbox. On Linux it uses bubblewrap (`bwrap`); on macOS it uses Seatbelt. There is no slash-command convention — skills are invoked by name through delegation. The boot file is `AGENTS.md` (walks up the directory tree like Claude's `CLAUDE.md`). Codex has no native auto-memory, so Agent Forge bridges the canonical `MEMORY.md` to a sidecar at `<project>/.codex/memory/AGENTS_MEMORY.md` and points Codex at it. Settings live in `<project>/.codex/config.toml`. When to pick this host: when you want the strongest default sandbox or when you're on a network where Codex is the only allowed coding agent.

---

## factory

The "factory" is the `_agent_forge/` folder. It is a single source of truth that holds canonical definitions of skills, safety rules, shared memory sections, team manifests, and MCP server inventory, plus a Python engine (`scripts/omni_factory.py`) that translates those definitions into Claude Code, OpenAI Codex, and Gemini CLI configuration files. You only ever edit the canonical sources; the engine generates the host-specific files. After every change, a runtime validator asks each host's CLI "can you actually see what we just shipped?" — that's the gate.

---

## gemini-cli

Gemini CLI is Google's coding-agent CLI. It loads `GEMINI.md` boot files hierarchically and is vision-capable. Skills are delivered as TOML or Markdown into `<project>/.gemini/commands/` and `<project>/.gemini/agents/`. Gemini supports a different subset of hook events than Claude / Codex — events like `BeforeAgent`, `BeforeToolSelection`, `AfterModel`, and `AfterAgent` are Gemini-only and don't have Claude / Codex equivalents; the factory's canonical event list includes them with `None` aliases for the other two hosts. Settings live in `<project>/.gemini/settings.json`. Like Codex, Gemini has no native auto-memory; a sidecar at `<project>/.gemini/memory/MEMORY.md` carries the bridge. When to pick this host: when you need a vision-capable agent or want the most cost-efficient non-trivial tier.

---

## governed-project

A governed project is one declared in `projects.json` and managed by the factory. On a fresh install, no projects are pre-wired — `projects.json` is an empty list. Adding your first one means: (1) add an entry to `projects.json` with `name`, `root`, and `required_files`; (2) run `./scripts/bootstrap-project.sh --name <name>`. The bootstrap creates the minimum required files, then immediately syncs the factory's skills, hooks, MEMORY.md, and forge_state into the project's host-native directories (`.claude/`, `.codex/`, `.agents/`, `.gemini/`). Generated surfaces are never hand-edited; re-run sync after any canonical change. The `required_files` declaration is what the verifier uses to confirm the project still has the minimum footprint.

---

## guardian

`telemetry-guardian` is the universal pre-tool seatbelt. POSIX shell script at `skills/global/telemetry-guardian/guardian.sh`. Reads one tool invocation on stdin, matches the command against a fixed deny list, exits 0 to allow or 1 to block. Bypass via `AGENT_FORGE_GUARDIAN=off` env var; every bypass is logged. Intentionally dumb — predictability beats sophistication for safety gates. The deny list covers `--no-verify`, force-push to protected branches, wildcard home deletion, unscoped `terraform destroy`, whole-disk `dd`, recursive 777, `--no-gpg-sign`, explicit `git reset --hard <ref>`.

---

## hook

A hook is a script that runs at a specific moment in a host CLI's tool-call lifecycle. The most common hook in this factory is `pre-tool-execution-guardian` — it runs before every Bash tool call, reads the command, and either lets it through or refuses. Hook records live in `policies/hooks.json`. The factory translates one canonical record into each host's native event names (Claude `PreToolUse`, Codex `PreToolUse`, Gemini `BeforeTool`). Some events are host-specific — Gemini has `BeforeAgent` / `BeforeToolSelection` / `AfterModel` / `AfterAgent` events that don't exist on Claude / Codex; canonical records for those events alias to `None` on the other two hosts and the renderer drops them silently.

---

## host-dirs

The factory writes to four different config directory names depending on the host. Claude reads from `.claude/`. Codex reads from `.codex/` and also from `.agents/` (a legacy Codex convention for skills, kept for back-compat). Gemini reads from `.gemini/`. The factory keeps these in sync from one canonical source, so if you ever see drift between them, that's a bug — not a feature. The triad runtime validator (`validate-triad-runtime.py`) is the gate that catches that drift before it ships.

---

## mcp

MCP (Model Context Protocol) is the open standard that lets an AI agent call external tools — GitHub, Slack, your internal services. The current spec is [MCP 2025-11-25](https://modelcontextprotocol.io/specification/latest) and all three host CLIs implement it: JSON-RPC 2.0 transport, three server feature types (Resources, Prompts, Tools), identical field names across hosts. The factory declares shared MCP servers in `global-mcp.json`. When the factory syncs, it writes each host's native MCP config: Claude `<project>/.mcp.json`, Codex `<project>/.codex/config.toml`, Gemini `<project>/.gemini/settings.json`. The seeded `forge-factory` stdio server exposes `read_handoff`; other shared MCP servers can be added to the canonical file and will render outward to all three hosts.

---

## memory

The shared memory layer is one Markdown file per project, at `<project>/MEMORY.md`. Five sections: build commands, project quirks, active tasks, recent decisions, known failures. The schema is defined in `policies/memory.json`. All three host CLIs read this file. The `memory-archivist` skill (`append`/`validate`/`summary`) writes to it; entries are timestamped and tagged by host. Append-first; secrets-deny at write time. Only Claude has documented native auto-memory; for Codex and Gemini the factory bridges to sidecar files (`.codex/memory/AGENTS_MEMORY.md`, `.gemini/memory/MEMORY.md`) — outbound from canonical works on all three, inbound has a true native target only on Claude.

---

## sandbox

Each host CLI runs your tool calls inside some kind of isolation. Codex CLI uses Linux bubblewrap (`bwrap`) on Debian/Ubuntu and macOS Seatbelt on macOS. Claude has permission modes (`default`, `plan`, `acceptEdits`, `auto`, `bypassPermissions`). Gemini gates on trusted-folder state. The factory is sandbox-aware: when the runtime validator can't inspect Codex via its shell tool because bwrap blocked the loopback interface, it escalates to filesystem evidence per documented doctrine.

---

## skill

A skill is a packaged, reusable workflow. It lives at `skills/global/<name>/SKILL.md` (for cross-project skills) or `skills/projects/<project>/<name>/SKILL.md` (for project-local). The frontmatter declares the metadata (which hosts, which projects, workflow vs. expert class). The body is the durable instruction text. The format follows the [agentskills.io](https://agentskills.io) open standard which all three hosts now implement: `name` and `description` are required, the body is loaded lazily when the skill is invoked (progressive disclosure). Agent Forge adds optional fields like `targets:`, `capability_class:`, and `delivery_projects:` as local extensions; these control which hosts and which governed projects receive the rendered skill.

---

## suitcase

The "suitcase" is the portable export of the factory you can carry to a fresh machine or VM without copying secrets or per-machine residue. `scripts/factory-export.sh` produces `agent-forge-suitcase-<timestamp>.tar.gz` (and `.zip`) in `exports/`. The bundle includes `_agent_forge/` canonical sources, the sync/bootstrap/validation scripts, and the doctrine docs — no `.env`, no auth tokens, no machine-local caches. On the target machine, `./_agent_forge/scripts/deploy-and-bootstrap.sh` is the one-shot path: deploys the factory into `~/Projects`, syncs the global host surfaces, and offers to run the workstation bootstrap (which installs the three host CLIs). The host-specific surfaces (`<project>/.claude/`, `.codex/`, `.gemini/`) and per-project `MEMORY.md` are re-rendered on first sync; they are NOT carried in the suitcase. This is the canonical-first doctrine in practice: ship the source of truth; let the engine generate the host views fresh on the target.

---

## triad-validator

`scripts/validate-triad-runtime.py` is the runtime gate. It does three things per host: asks the actual CLI to enumerate its visible skills (the surface check), confirms the seeded `telemetry-guardian` hook is registered with the right event name (the hook surface check), and confirms the `MEMORY.md` shared brain is reachable (the memory surface check). Run it after any canonical change. With `--probe-invocations`, it also fires a real test command and observes whether the hook actually intercepts it.

---

## validation-pyramid

The factory uses three nested gates of increasing depth and decreasing speed. Level 1 — `verify-agent-forge.py` — is the cheapest: it checks file presence, JSON parse, schema-shape, and that referenced scripts exist on disk. Run constantly. Level 2 — `validate-triad-runtime.py` (default mode) — asks each host's CLI to enumerate skills, then confirms the seeded telemetry-guardian hook is registered with the host's expected event key (PreToolUse / PreToolUse / BeforeTool) and that the MEMORY.md surface is reachable. Mandatory after every canonical change. Level 3 — `validate-triad-runtime.py --probe-invocations` — fires a real test command on each host CLI and observes whether the hook actually intercepts it. Slow, opt-in, and the only level that catches host-native semantic drift (the kind that broke the Gemini hook silently for two sprints in 2026-04). Each level is necessary; only the third is sufficient.
