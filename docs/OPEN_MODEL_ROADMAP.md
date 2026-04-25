# Open-Model Roadmap

This document defines the next expansion after hosted CLI bootstrap is complete.

## Phase 2 Goal

Add an open-model execution lane that fits the same `~/Projects` factory and governance model.

The first supported open-model runtime should be:

- **Ollama first**

The first remote fallback should be:

- **OpenRouter second**

## Why Ollama First

- straightforward local runtime for Debian/Ubuntu and macOS
- good fit for privacy-sensitive or offline-friendly workflows
- simple local endpoint conventions
- easiest first path for Gemma, Qwen, and related open models

## Why OpenRouter Second

- good remote fallback when local hardware is insufficient
- simple API-key auth model
- wide model inventory
- useful when the operator wants non-local open models without running their own infrastructure

## Planned Capability Split

### Hosted lane

- Claude Code
- Codex
- Gemini CLI

Best for:

- strongest coding assistance
- subscription-driven auth
- interactive multi-agent terminal work

### Open-model lane

- Ollama local runtime
- later provider wrappers for specific coding helper models
- OpenRouter as remote fallback

Best for:

- cheaper drafting and summarization
- lightweight helper agents
- environments where hosted usage should be minimized

## Phase 2 Implementation Shape

These are **planned, not yet implemented**. None of the paths below currently exist in the repo; they are the expected shape of Phase 2 once it begins:

- `scripts/bootstrap-open-models.sh` (planned)
- runtime/provider config docs (planned)
- optional model pull helpers (planned)
- common environment variables for local vs remote providers (planned)
- provider selection guidance for different task classes (planned)

## Known Research Findings

- local coding-helper models are realistic for bounded tasks, but they should not replace hosted frontier tools for complex planning or repo-wide reasoning
- Ollama is the cleanest first local runtime
- OpenRouter fits naturally as the remote open-model lane
- this phase should come after hosted workstation bootstrap is stable and validated on real machines

## Likely Future Roles For Open Models

- evidence cleanup
- summarization
- formatting
- classification
- low-risk drafting
- first-pass review

Not first-wave targets:

- canonical governance edits
- architecture decisions
- source-of-truth planning
- high-stakes legal or tax reasoning

---

## OSS Ecosystem Assessments

Assessed 2026-04-06. Re-research before acting — capability and trust signals change.

### obra/superpowers

**Repo:** https://github.com/obra/superpowers
**Stars:** ~137K | **License:** MIT | **Last active:** April 2026

**What it is:** A collection of 14 SKILL.md prompt files + a SessionStart shell hook + a local-only Node.js WebSocket server for a brainstorming UI. Zero npm runtime dependencies.

**Security verdict: LOW RISK.** No phone-home, no credential handling, no outbound network calls. The brainstorming server binds to 127.0.0.1 only. Maintainer (Jesse Vincent) is a known open-source figure with a long public track record.

**Conflict with ZorroForge architecture:** The SessionStart hook injects into every Claude Code session globally. This overrides per-project AGENTS.md doctrine. Installing it globally would undermine the _agent_forge registry model.

**Do NOT:**
- Install the plugin globally (`claude plugin add ...`)
- Add the SessionStart hook to `~/.claude/settings.json`

**Cherry-pick targets** (read + adapt into _agent_forge registry, MIT license allows this):
- `systematic-debugging` — well-tuned multi-step diagnostic workflow
- `subagent-driven-development` — two-stage review loop (spec compliance then quality) more sophisticated than a bare subagent dispatch
- Brainstorming design workflow — if local browser design-review UI has value

**If you ever install:** pin to a specific commit SHA (`git checkout <sha>`) rather than tracking main to prevent silent update risk.

---

### affaan-m/everything-claude-code (ECC)

**Repo:** https://github.com/affaan-m/everything-claude-code
**Stars:** ~142K in <3 months (anomalous — not a reliable trust signal) | **License:** MIT | **Last active:** April 2026

**What it is:** 156 prompt skills, 47 agent role definitions, 79 slash command shims, hook system (Node.js, runs on every agent operation), language-specific coding rules (12 ecosystems), Rust TUI control plane (alpha), SQLite-backed continuous learning session store. Install via `npm install ecc-universal` or `./install.sh --profile full`.

**Security verdict: MEDIUM — do not install wholesale.**
- Installing hooks gives third-party Node.js code exec rights on every Claude Code tool invocation
- Continuous learning SQLite store accumulates all tool-use events locally — large data footprint, conflicts with Suitcase Doctrine (non-portable side effect)
- `.mcp.json` includes `https://mcp.exa.ai/mcp` — an external remote HTTP MCP endpoint. This is the one outbound connection in the default install
- Star count is anomalous; do not treat community vetting as meaningful here
- Code appears real and non-malicious, but trust surface is high for a hooks-heavy install

**Do NOT:**
- Run `npm install ecc-universal` or `./install.sh --profile full`
- Add their `.mcp.json` to your settings (it enables Exa's remote MCP server)
- Install the Rust TUI (`ecc2/`) — it duplicates the forge CLI direction and is alpha

**Cherry-pick patterns** (read + adapt, never copy-paste-execute, MIT allows):
- `block-no-verify` PreToolUse hook concept — implement natively in 2 lines of bash in `settings.json` without any npm dependency: block `Bash(git ... --no-verify)` patterns
- Commit-quality hook secret-detection regex patterns — adapt into existing _agent_forge pre-commit hooks if that gap becomes relevant
- Language-specific Markdown rules for Rust/Swift/Kotlin/etc. — if those stacks become relevant, their rules are a useful starting point
- Selective install manifest architecture (`install-plan.js`) — study as reference for how to build a more sophisticated `_agent_forge` bootstrap/deploy installer if that direction is pursued
