# SOTA 2026 Multi-Agent Research

*Citation hygiene last reviewed: 2026-05-23. Cross-referenced against `docs/SOTA_2026_AUDIT.md` which is the load-bearing primary-source anchor for SOTA decisions; any new citation added here should also land there.*

This document serves as the foundational academic and industry research driving "The Great Consolidation" of Agent Forge. It anchors the architectural decisions to empirical data regarding LLM performance, tool design, and context management.

## 1. Tool Overlap & Agent-Computer Interfaces (ACI)
**Concept:** LLMs suffer from "decision paralysis" and degraded performance when provided with overlapping, noisy, or excessively broad tools.
**Primary Source:** *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering* (Princeton University / NeurIPS 2024).
**Key Findings:**
*   Researchers demonstrated that standard terminal environments are poorly suited for LLMs.
*   By restricting agents to an "Agent-Computer Interface" (ACI) with rigid, single-purpose tools (e.g., a file viewer strictly capped at 100 lines, linter-guarded editing), they improved GPT-4 performance on SWE-bench Lite by **10.7 percentage points**.
*   **Architectural Mandate:** Consolidate overlapping tools. Do not provide three different review skills (`quality-gate`, `code-review-doctrine`, `paranoid-reviewer`). Merge them into a single, unambiguous pipeline.
**Links:**
*   [SWE-agent Project Page](https://swe-agent.com/)
*   [Princeton SWE-agent Release](https://www.cs.princeton.edu/news/2024/swe-agent)

## 2. Context Rot & "Lost in the Middle"
**Concept:** Coding agents fail on complex tasks primarily due to declining signal-to-noise ratios as context grows, rather than a fundamental lack of reasoning ability.
**Primary Source 1:** *Context Rot: How Increasing Input Tokens Impacts LLM Performance* (Chroma Research, 2025).
**Primary Source 2:** *Lost in the Middle: How Language Models Use Long Contexts* (Liu et al., 2023/2024).
**Primary Source 3:** *LLMs Get Lost in Multi-Turn Conversation* (Laban et al., ICLR 2026, arXiv 2505.06120).
**Key Findings:**
*   While modern LLMs have massive context windows (1M+ tokens), their ability to retrieve specific constraints from the *middle* of that context degrades heavily.
*   In multi-turn coding sessions, as agents explore files and execute tools, the "noise" accumulates. The agent forgets early architectural constraints (the "Lost in Conversation" phenomenon).
*   **Architectural Mandate:** Strict phase-based execution and context flushing. Task plans must be capped at a maximum of 4 atomic tasks. If a feature requires more, the orchestrator must flush the context, consolidate the state, and spawn a new subagent.
**Links:**
*   [Lost in the Middle (Liu et al., TACL 2024)](https://arxiv.org/abs/2307.03172)
*   [LLMs Get Lost in Multi-Turn Conversation (Laban et al., ICLR 2026)](https://arxiv.org/abs/2505.06120) *(note: an earlier circulated handover prompt cited arXiv 2505.09111 — that ID is wrong; it points to an unrelated cosmic-ray-physics paper. Correct ID is 2505.06120.)*

## 3. State-Machine Orchestration
**Concept:** Complex multi-agent workflows should be modeled as Directed Acyclic Graphs (DAGs) or State Machines, where state is externalized, rather than relying on unstructured chat threads.
**Primary Source:** *LangGraph: Multi-Agent Workflows at Scale* (LangChain, 2024-2025).
**Key Findings:**
*   Linear chain architectures fail at complex reasoning because agents cannot easily loop, retry, or self-correct without losing state.
*   By treating agents as "Nodes" and passing an externalized "State" (e.g., a JSON blueprint) between them via "Edges," systems become deterministic and resilient.
*   **Architectural Mandate:** Upgrading the `subagent-dispatcher` from a simple parallel executor to a DAG parser. It must read `teams/*.json` blueprints and autonomously transition between the defined roles (e.g., Discuss -> Plan -> Execute -> Review).
**Links:**
*   [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 4. Prompt Caching & Stable Prefix Design
**Concept:** Long-running agents repeatedly send large stable prefixes: tool definitions, system/developer instructions, durable doctrine, memory summaries, and examples. Prompt caching makes those stable prefixes cheaper to reuse, but only when they remain byte-stable before the cache breakpoint.
**Primary Source:** Anthropic, *Prompt caching* (reviewed 2026-05-23).
**Key Findings:**
*   Cache prefixes are created in the order `tools`, `system`, then `messages`, so request structure matters.
*   Static content should appear before variable per-request content; the cache breakpoint belongs at the end of the reusable prefix.
*   Timestamps, request IDs, and other turn-specific material before the breakpoint invalidate cache reuse because the prefix hash changes.
*   **Architectural Mandate:** Keep Agent Forge doctrine and generated host boot content stable at the top of prompts where possible. Put volatile cursor state, rate-limit handoff notes, and per-turn user detail after reusable instructions.
**Links:**
*   [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
