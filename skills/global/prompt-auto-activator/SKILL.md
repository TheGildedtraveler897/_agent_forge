---
name: prompt-auto-activator
description: Use when a user-prompt-submit hook should advise the agent to load a specific skill based on keyword triggers in the user's prompt. Routes opt-in phrases like /caveman or /terse to token-optimizer without making the agent guess.
capability_class: workflow
targets: ["claude", "codex"]
context_cost: light
model_tier: any
---

# Prompt Auto-Activator

Owns the `user_prompt_submit` advisory hook. Reads the user prompt, regex-matches a small keyword table, and emits one-line advisories recommending the skill that should be loaded for the current turn.

## Hook-driven, advisory-only

- Ships `auto-activator.py` (with a thin `auto-activator.sh` POSIX forwarder), registered as a `user_prompt_submit` hook for Claude and Codex via `policies/hooks.json`. The Python implementation runs natively on Windows Claude Code without bash.
- Gemini has no equivalent event. The canonical alias `_EVENT_ALIASES["gemini"]["user_prompt_submit"]` resolves to `None`, so the renderer drops Gemini automatically. The skill's `targets` list reflects this.
- The script reads stdin, regex-matches a keyword set, and prints one advisory line per match.
- The agent decides whether to load the recommended skill. The hook never blocks, never modifies the prompt, and never invokes a tool.

## Keyword Set and Routing Table

| Trigger phrase (case-insensitive) | Recommended skill |
|-----------------------------------|-------------------|
| `/caveman`, `caveman mode`, `/terse`, `terse mode` | `token-optimizer` |
| `/checkpoint`, `/handoff` | `context-engineer` |

New rows are added by editing the `ADVISORIES` list in `auto-activator.py`. No schema change is required to add a new trigger.

## Non-goals

- Does not load skills itself. The agent reads the advisory and decides.
- Does not modify the user's prompt.
- Does not run any tool.
- Does not duplicate `telemetry-guardian`. That skill owns `pre_tool_use`; this one owns `user_prompt_submit`.
- Does not target Gemini. Re-add only after a Gemini equivalent event ships and is verified against current Gemini CLI release notes.

## Live probe

Use `live-hook-prober` to confirm the hook fires end to end:

1. Sync the project (`python3 scripts/omni_factory.py --project <name>`).
2. Send a Claude prompt containing `/caveman`.
3. Confirm the hook trace contains `{"advice":"...","skill":"token-optimizer"}`.

If the trace is empty, re-check `_EVENT_ALIASES`, the rendered Claude `.claude/settings.json`, and the script's executable bit.
