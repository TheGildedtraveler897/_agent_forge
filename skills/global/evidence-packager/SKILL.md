---
name: evidence-packager
description: Convert research or repo exploration into a compact evidence pack with sources, confirmed findings, conflicts, and practical implications. Use before planning when the source surface is broad.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
---

# Evidence Packager

Package research so a planner or executor does not need the whole source hunt.

## Output Contract

- question
- source table
- confirmed findings
- conflicts or uncertainty
- practical implications
- recommended next step

## Rules

- prefer primary sources when available
- separate what is proven from what is inferred
- strip commentary that does not change the next decision
- include only the facts the next worker actually needs

## Example Evidence Pack

```
# Evidence Pack: Agent orchestration patterns for _agent_forge

## Question
Which orchestration pattern best fits a portable, team-based multi-agent factory?

## Sources
| Source | Type | Key Claim |
|---|---|---|
| Google ADK blog (2025) | Official | 8 patterns; start simple, add complexity when needed |
| Anthropic context eng. (2025) | Official | Smallest high-signal token set wins |
| ArXiv 2511.08475 | Academic | Modular interface design prevents role overlap |

## Confirmed Findings
- Supervisor/coordinator is the default enterprise pattern (Google, Microsoft, OpenAI)
- Optimal team size: 3-7 agents; beyond 7, use hierarchical sub-teams
- Declarative manifests (JSON/YAML) are industry standard for role definitions

## Conflicts
- Swarm vs. supervisor: swarm advocates cite emergent behavior, but no production evidence for portable factories

## Practical Implications
- Agent Forge's 2-4 role teams with JSON manifests align with best practice
- No need for swarm infrastructure — supervisor pattern covers all current use cases

## Next Step
Proceed with current team model; add escalation/collapse conditions to manifests
```
