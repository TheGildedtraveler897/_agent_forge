---
name: token-optimizer
description: Use when the operator requests caveman mode, terse mode, or any token-frugal output discipline. Suppresses preamble, summary, and conversational filler; preserves load-bearing facts, file paths, and exact commands.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Token Optimizer

Graceful degradation under context or rate-limit pressure. Output shrinks; truth does not.

## Hard Contract

- No preamble. No "Sure, I'll…", "Let me…", "I'll start by…".
- No postamble. No "Let me know if…", "Hope this helps", "Anything else?".
- No restatement of the user's request.
- No chain-of-thought narration ("First I'll…, then I'll…").
- No section headers, bullet padding, or table formatting unless the artifact actually needs structure.

The output is the answer or the artifact, nothing else.

## What Survives

These are load-bearing and must not be cut:

- Exact file paths.
- Exact shell commands and arguments.
- Exit codes, error strings, log lines that prove or refute a claim.
- Decisions, each with one short rationale clause.
- Any claim the next agent must verify (flag with the verification command).
- Verification evidence required by `verification-gate`.

Truncating these is a violation of terse mode, not an instance of it.

## Activation and Exit

Activated by:

- Explicit operator request: "go terse", "caveman mode", "/caveman", "/terse".
- The `prompt-auto-activator` advisory firing on those keywords (see `skills/global/prompt-auto-activator/`).
- An operator instruction that the session is approaching a context or rate limit.

Deactivated by:

- Explicit operator request: "verbose", "explain", "walk me through", "long form".
- The end of the session, unless re-confirmed.

Stays orthogonal to `verification-gate`: terse mode never suppresses verification evidence. Stays orthogonal to `context-engineer`: terse mode shrinks prose; the engineer extracts and persists state.

## Non-goals

- Does not change tool-call behavior. Tool calls remain whatever the task requires.
- Does not skip safety steps. A blocked destructive command in terse mode is still blocked, with the matched pattern reported.
- Does not summarize away the durable artifact. If the user wants a plan, the plan is written; only the surrounding chat shrinks.
