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

Expected additions later:

- `scripts/bootstrap-open-models.sh`
- runtime/provider config docs
- optional model pull helpers
- common environment variables for local vs remote providers
- provider selection guidance for different task classes

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
