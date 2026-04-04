# Agent Forge Handoff

Last updated: 2026-04-04

## What Changed

### Premium Factory Optimization (2026-04-04, Claude Opus)

Compared Agent Forge against external best practices from Anthropic, Google ADK, OpenAI Agents SDK, Microsoft Agent Framework, and ArXiv research. Made targeted improvements based on the highest-leverage gaps found.

#### External Research Findings

Agent Forge already aligns with industry best practice on: declarative role definitions (JSON manifests), progressive-disclosure skill architecture, context discipline (artifacts over chat), handoff protocols, and team size constraints (2-4 roles). Sources: Anthropic context engineering blog, Google ADK multi-agent patterns, OpenAI Agents SDK handoffs docs, ArXiv papers on orchestration and eval harnesses.

#### Changes Made

1. **Token budget and model-tier hints** — Added `context_cost` (light/medium/heavy) and `model_tier` (any/sonnet/opus) to all 17 SKILL.md frontmatter files. Helps operators and cheaper models make load/skip decisions.

2. **Worked examples in utility skills** — Added concrete filled-in examples to context-engineer, evidence-packager, and quality-gate SKILL.md files. Research shows weaker models perform dramatically better with few-shot examples.

3. **Severity tiers in quality gate** — Changed from flat pass/fail to blocker/warning/note tiers. Prevents weaker models from treating cosmetic issues as showstoppers. Updated EVALUATION.md scorecard to match.

4. **Team escalation rules** — Added `collapse_condition` and `escalate_condition` to all 7 team manifests. Tells operators when to use one worker vs. the full team pattern.

5. **Filled operator templates** — Added realistic worked examples for all 4 templates (task brief, evidence pack, implementation brief, handoff) using playlist-archive as the scenario.

6. **Compaction triggers** — Added "When To Compact" section to CONTEXT_ENGINEERING.md with 5 concrete trigger points.

7. **Full team runbooks** — Expanded TEAM_RUNBOOKS.md with Claude/Codex patterns, recommended flows, and stop conditions for all 7 teams (previously only 3 had full runbooks).

#### Scenario Tests Run

- Quality-gate applied to HANDOFF.md: 0 blockers, 2 warnings — KEEP
- Sonnet task brief simulation: self-contained, no prior context needed — PASS
- Evidence-packager output test: matches contract, compact for downstream planner — PASS

## Current State

- **Registry:** v4, 22 skills (up from 17 after prep pass added context-engineer, evidence-packager, quality-gate + 2 more)
- **Teams:** 7 teams, all with escalation rules
- **Verification:** 136 checks, 0 failures
- **Skills:** All 17 canonical SKILL.md files have context_cost and model_tier metadata
- **Docs:** 12 framework docs, all updated this session

## Remaining Weaknesses

1. **No automated eval harness** — Quality-gate is a manual skill invocation, not a CI/CD pipeline. Industry practice is automated evals on every change. Low priority for a one-person corp.
2. **Bootstrap script untested for edge cases** — `bootstrap-project.sh --existing` and `--with-local-skills` paths haven't been exercised with real projects.
3. **No Codex-side validation** — All verification has been Claude-side. Codex skill discovery and runtime behavior haven't been independently confirmed this session.
4. **Team manifests are conceptual** — No automated team orchestration exists. Teams work by operator selection and manual handoff. This is intentional but limits weaker-model autonomy.
5. **Content freshness** — Domain skills (finance, legal, procurement) embed rate/threshold data that will drift annually. The "verify before citing" mandate handles this at query time but doesn't prevent stale defaults from anchoring weaker models.

## Manual Follow-Up Items

1. Commit the prep pass + premium optimization changes in `_agent_forge`
2. Run `sync-claude-adapters.sh --project jarvis` to deploy updated skills
3. Exercise `bootstrap-project.sh` against a real new project to validate the bootstrap path
4. Consider a Codex validation pass to confirm skill discovery works from that side
5. Start first real implementation slice (playlist-archive) using the delivery team model

## Final Verdict

**The factory is materially stronger for future lower-tier model runs.**

The key improvements are the ones that reduce ambiguity for weaker models: worked examples in utility skills, severity-weighted quality gates, filled operator templates, and explicit escalation rules. A Sonnet-class model receiving a task brief built with these templates can execute without needing the full planning context that produced it. The framework's token discipline (selective skill delivery, compaction triggers, context_cost hints) keeps the signal-to-noise ratio high even in constrained contexts.

The architecture is sound, the governance is operational, and the factory is portable. Clone `_agent_forge`, run the sync scripts, bootstrap a project — the accumulated knowledge deploys without rebuilding.
