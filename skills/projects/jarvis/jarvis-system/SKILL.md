---
name: jarvis-system
description: Jarvis Phase 1 operating doctrine. Enforces subscription-first, local-first, CLI-native principles. Load this when working in the Jarvis repo.
context_cost: medium
model_tier: any
---

# Jarvis System Skill

You are operating inside the Jarvis repo. This skill governs your behavior for every task here.

---

## What Jarvis Is

A terminal-first, subscription-first AI workflow engine. Built to reduce mental load, preserve portability, and avoid unnecessary cost or complexity. Phase 1 is about building manual, repeatable, modular workflows — not a polished application.

## What Jarvis Is Not

- Not a centralized API application
- Not a Python app backed by Anthropic/OpenAI SDKs
- Not a Docker-heavy or framework-heavy project
- Not a feature-complete product yet

---

## Phase 1 Priorities

1. **Subscription tools first** — Claude Code, Gemini CLI, ChatGPT Plus, Perplexity Pro
2. **Local machine second** — scripts, bash, local files, terminal workflows
3. **Skills and modular scripts** — over monolithic app patterns
4. **API SDKs last** — deferred to Phase 2; code lives in `archive/`

---

## Hard Rules for Phase 1

- Enforce Phase 1 rules as defined in CLAUDE.md.
  **Local API Exception (Phase 2+):** API SDKs (`openai`, `langchain`, etc.) are permitted ONLY when configured with `base_url='http://localhost:11434/v1'`. Cloud API billing remains strictly forbidden.
- No Docker, VM setup, or local model configuration unless explicitly requested
- No API billing — if a task seems to require it, stop and ask first
- If a subscription tool can do the job, use that instead
- Always warn before adding cost, lock-in, or avoidable complexity
- **Maximum Portability** — NEVER hardcode absolute paths. Scripts must be dynamically portable to any machine. Use `$(dirname "$0")` for script-relative paths or relative paths from the repo root.
- **Dependency Management** — NEVER assume external Python packages are installed. If a script requires a new package, explicitly ask the user for permission to install it via the isolated environment (e.g., `./.venv/bin/pip install <pkg>`) and provide the exact command in your plan.

---

## How to Behave in This Repo

- **One small step at a time.** Do not batch large changes without checking in.
- **Be concise.** No long explanations unless asked. Prefer editing files over narrating them.
- **Recommend clearly.** When multiple options exist, pick one and state why briefly.
- **Explain the intuition** when implementing anything non-trivial — one sentence is enough.
- **Prefer scripts over code** for Phase 1 automation. `scripts/` is the center of gravity.
- **Prefer skills over monoliths.** New capabilities should be small, composable, and isolated.
- **Read `docs/CONOPS.md` ONLY before adding a new script, skill, or top-level capability.** It defines current state, active objective, and tool stack.
- **Update `docs/CHANGELOG.md` after completing any meaningful milestone.** One bullet per change is enough.
- **Decision Documentation** — When a significant architectural choice is made (e.g., "no SDKs", "use git for review"), log it in the "Architecture Decision Log" section of `docs/CONOPS.md` with a one-line rationale.
- **Gotcha Documentation** — When a weird bug is bypassed, a surprising behavior is discovered, or a workaround is implemented, log it in the "Gotchas" section of `docs/CONOPS.md` with enough context to reproduce or avoid the issue.
- **Future State Documentation** — When a tool, pattern, or capability is deliberately deferred to a later phase, log it in the "Future State (The Horizon)" section of `docs/CONOPS.md` with the phase it targets and why it is deferred now.

---

## Sanity Check Mindset

After any change, ask:
- Does this require an API key or SDK? → If yes, flag it.
- Does this add a new dependency or service? → If yes, warn.
- Can this be done simpler? → If yes, do the simpler thing.
- Does this match the Phase 1 priority order? → If not, realign before proceeding.
