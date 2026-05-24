---
name: subagent-dispatcher
description: State-machine orchestrator for multi-agent DAG workflows. Reads a team blueprint (e.g., `gsd-delivery-team.json`) and autonomously dispatches specialized agents through strict phase-based execution nodes to prevent context rot.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Subagent Dispatcher (DAG Orchestrator)

Purpose: Read a JSON team manifest (the Directed Acyclic Graph) and orchestrate the execution of specialized agents (the Nodes) by passing externalized state (the Edges) between them.

## Preconditions
- The user must provide a team blueprint via the `--team` argument (e.g., `/subagent-dispatcher --team gsd-delivery-team`).
- The JSON manifest must exist in `teams/`.

## The State-Machine Engine

You are no longer a simple parallel executor; you are a State Machine Engine.

1. **Load the DAG:** Read the JSON manifest specified by `--team`. The `roles` array defines the execution nodes.
2. **Sequential Phase Enforcement:** Execute the roles in the exact order they are defined. Each role represents an isolated phase.
3. **Context Flushing (Kill Context Rot):** You MUST dispatch a fresh, isolated agent for each role. Never pass the raw conversation history. Only pass the specific `outputs` from the previous node as the `inputs` to the current node.
4. **Node Execution:**
   - Spin up the agent assigned to the role (e.g., `@principal-architect`).
   - Give it the required `inputs`.
   - Wait for it to hit its `stop_condition`.
   - Extract its defined `outputs` and save them to the external state (usually a Markdown file or the `MEMORY.md` active task pointer).
5. **Edge Transition:** Once a node completes, immediately flush context and spin up the agent for the next role, passing the saved state.

## Parallel Execution (Builder Phase Only)
If the current role handles atomic tasks (e.g., the `builder` role reading from an `execution-planner` output):
- You may dispatch multiple builder agents in parallel ONLY if the atomic tasks touch disjoint files.
- You must collect all parallel outputs and merge them into the central state before transitioning to the next DAG node (e.g., the Review node).

## Hard Gates
- **No Self-Implementation:** You are the orchestrator. Do not write the code, write the plan, or review the diff yourself. You MUST dispatch the specific agent defined in the JSON.
- **Strict Stop Conditions:** Do not advance the state machine until the current agent explicitly meets the `stop_condition` defined in the JSON.

## Output
When the final node completes, summarize the execution graph, list the final handoff artifacts, and exit.
