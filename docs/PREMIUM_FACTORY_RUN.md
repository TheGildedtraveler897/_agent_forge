# Premium Factory Run

Use this runbook when you want Claude Opus to improve the Agent Forge framework itself instead of drifting into product work.

## Mission

Improve the shared factory layer so future normal-tier runs can execute from better teams, better briefs, better handoffs, and better context discipline.

## Target Surface

Focus on:

- `_agent_forge`
- root shared docs under `~/Projects` only when necessary

Avoid:

- repo-specific product implementation
- opportunistic feature work in governed projects

## What Claude Should Do

1. Audit the current framework artifacts.
2. Tighten the new team manifests.
3. Tighten context-engineering and evaluation docs.
4. Improve the new utility skills and command adapters.
5. Run scenario-based tests against the framework.
6. Update `_agent_forge/docs/HANDOFF.md` with what changed and what remains.

## Copy/Paste Prompt

```text
Continue from the current Agent Forge baseline and work only on the shared factory layer unless a shared-doc update requires touching another repo.

Primary mission:
Use the remaining premium context to optimize `_agent_forge` into a stronger portable multi-agent factory for future normal-tier runs.

Current baseline:
- Governance validation already passed.
- Three-layer Claude delivery model exists.
- `.claude/skills` is governed.
- `_agent_forge` is under git.
- The remaining leverage is framework quality, team design, context engineering, evals, and operator guidance.

Your job:
1. Audit the new framework artifacts added in this prep pass.
2. Improve the team system for research, planning, assessment, and improvement.
3. Improve context-engineering infrastructure: briefs, evidence packs, handoffs, compaction, model-escalation guidance.
4. Improve the new shared skills and command adapters.
5. Run scenario-based tests against the framework itself.
6. Update the relevant `_agent_forge` docs and handoff notes.
7. Leave behind a compact final operator layer optimized for future weaker models.

Constraints:
- Focus on `_agent_forge` and shared root docs.
- Do not drift into product feature work.
- Do not create agent bloat.
- Prefer a small number of sharp reusable primitives.
- Preserve `_agent_forge` as canonical source of truth.
- If you find schema or sync edge cases, fix them consistently across registry, scripts, docs, and verification.

Final output must separate:
- framework upgrades completed
- tests/scenarios run
- remaining weaknesses
- manual follow-up items
- final verdict on factory readiness for future lower-tier model runs
```
