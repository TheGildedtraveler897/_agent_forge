---
status: approved
branch: feat/great-consolidation
---
# Plan: The Great Consolidation & State-Machine Orchestration

## Objective
Consolidate overlapping skills and upgrade the `subagent-dispatcher` into a state-machine orchestrator. This plan is empirically backed by 2024-2026 SOTA research on Agent-Computer Interfaces (ACI), "Context Rot", and Cyclic Graph orchestration (LangGraph).

## Research Foundation & Rationale
1. **SWE-agent ACI Interfaces (Princeton, NeurIPS 2024):** Proved that LLMs suffer when given overlapping or "noisy" tools. Restricting an agent to rigid, single-purpose tools improved performance by 10.7%.
   *Rationale:* We must merge overlapping planning tools (`principal-architect` into `spec-architect`) and overlapping review tools (`code-review-doctrine`, `quality-gate`) into a single, unambiguous pipeline.
2. **Context Rot (Chroma Research, 2025):** Proved that coding agents fail primarily due to declining signal-to-noise ratios as context grows (the "Lost in the Middle" phenomenon applied to multi-turn agentic workflows).
   *Rationale:* We must enforce a hard limit of 4 atomic tasks per execution plan to force context flushing.
3. **LangGraph State Machines (LangChain, 2024-2025):** Established that complex multi-agent reasoning requires Directed Acyclic/Cyclic Graphs (DAGs) where state is externalized.
   *Rationale:* `subagent-dispatcher` must be upgraded to natively read `teams/*.json` files, treating the JSON as an executable state machine rather than a human-readable blueprint.

## Proposed Solution & Implementation Steps

### Phase 1: Skill Consolidation
1. **Merge Planners:** Move the architectural decision logic of `principal-architect` into `spec-architect`. Deprecate `principal-architect`.
2. **Merge Reviewers:** Move the static analysis rules of `code-review-doctrine` and `quality-gate` into the background `AGENTS.md` doctrine and the prompt of `@paranoid-reviewer`. Delete the redundant skills.

### Phase 2: State-Machine Upgrade
1. **Upgrade `subagent-dispatcher`:** Rewrite the skill to accept a `--team` argument (e.g., `/subagent-dispatcher --team gsd-delivery-team`). It must parse the JSON roles, inputs, and outputs as nodes and edges in a state machine.
2. **Upgrade `execution-planner`:** Enforce the "Context Rot Limit" (max 4 tasks per plan).

## Handover & Next Steps
*(This file serves as the context anchor for the next agent assigned to implementation).*