---
name: jarvis-reviewer
description: Pre-commit code reviewer. Runs git diff and flags doctrine violations before any commit.
context_cost: medium
model_tier: any
---

# jarvis-reviewer

When invoked, run `git diff HEAD` (or `git diff --cached` for staged changes) and review all changes against the ZorroForge Doctrine.

## ZorroForge Doctrine

No API SDKs, strict portability (Suitcase Doctrine), usage guards, CLI silencers, intuition-first comments (The Ferda Standard).

## How to invoke

```
/jarvis-reviewer
```

## What to do

1. Run `git diff HEAD` to capture all unstaged changes.
2. Run `git diff --cached` to capture staged changes.
3. Review the combined diff output against the criteria below.
4. Output a concise bulleted terminal report.

## Review criteria

Flag the following as violations:

- **Hardcoded secrets** — API keys, tokens, passwords, or credentials embedded directly in code
- **Raw API SDK imports** — `import anthropic`, `import openai`, `from openai`, `from anthropic`, or equivalent in any language
- **Premature infrastructure** — Dockerfiles, docker-compose, VM configs, or cloud infra added without explicit Phase 2 sign-off
- **Over-engineered abstractions** — classes, modules, or utilities built for hypothetical future use with no current caller

## Output format

One bullet per finding. Lead with the file and line if relevant.

```
- [VIOLATION] <file>:<line> — <short reason>
- [VIOLATION] <file>:<line> — <short reason>
```

If no violations are found:

```
Doctrine aligned. Ready to commit.
```

No summaries. No explanations. No fluff.
