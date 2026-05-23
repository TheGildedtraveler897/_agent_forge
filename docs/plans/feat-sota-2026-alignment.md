---
plan_id: feat-sota-2026-alignment
branch: feat/sota-2026-alignment
status: completed
created: 2026-05-22
last_updated: 2026-05-22
spec_ref: ~/.claude/plans/yeah-do-the-final-dapper-creek.md
task_count: 10
execution_mode: sequential
approved_at: 2026-05-22
approved_by: operator
completed_at: 2026-05-22
completed_by: opus-4.7
title: SOTA 2026 Drift Audit, Repair, and Onboarding-Guide Inline-Delivery Fix
---

# Plan: SOTA 2026 Drift Audit, Repair, and Onboarding-Guide Fix

This file is the canonical project-side plan artifact (durable across host/agent swaps). The full plan text is in `~/.claude/plans/yeah-do-the-final-dapper-creek.md` (operator-side). Summary below.

## Context

The operator's concern: Agent Forge may have drifted from 2026 vendor standards, and the `/onboarding-guide` slash command in Claude Code produces nothing visible (it attempts to spawn a Python subprocess with no terminal pipeline back to chat). Phase 1 research (three parallel Explore agents, including primary-source WebFetch on vendor docs and academic citation verification) ran before this plan was written.

**Phase 1 findings (load-bearing):**

What HAS converged (2026 cross-vendor SOTA):
- Skills: agentskills.io open standard. All three vendors honor `SKILL.md` with YAML frontmatter and progressive disclosure.
- MCP: Model Context Protocol 2025-11-25 spec. Identical field names across hosts.

What HAS NOT converged:
- Subagents: Codex uses **TOML** in `.codex/agents/`; Claude/Gemini use YAML-frontmatter markdown.
- Hooks: Gemini fires semantically distinct events (`BeforeAgent`, `BeforeToolSelection`, `AfterAgent`, `AfterModel`) that don't map 1:1 to Claude/Codex.
- Memory: only Claude has native auto-memory; Codex/Gemini have no documented equivalent. Factory's bridge already handles this honestly via sidecars.
- AGENTS.md: not a formal standard — a convention. Codex supports `AGENTS.override.md` precedence; not implemented in Agent Forge.

Current state: 30 global skills, 8 teams, hooks policy v3, MCP v2 schema, recent commits already landed "great consolidation" and "sota 2026 audit" passes. Onboarding-guide explainer content is **current** (audit confirmed). The user's perception of "outdated" likely stems from the inline-delivery bug making the tour invisible, not stale content.

Verified academic citations (for state-of-the-field explainer):
- SWE-agent (NeurIPS 2024) — ACI principles
- Context Rot (Chroma 2025) — long-context degradation
- Lost in the Middle (Liu et al., TACL 2024, arXiv 2307.03172)
- LLMs Get Lost in Multi-Turn (Laban et al., ICLR 2026, arXiv **2505.06120** — handover prompt's `2505.09111` is WRONG)
- LangGraph (LangChain 2024-2025)
- Code as Agent Harness (arXiv 2605.18747, May 2026)
- GenericAgent (Fudan, arXiv 2604.17091)

Discarded claims (NOT load-bearing):
- KAIROS, `/dream`: leaked Claude Code product features, not peer-reviewed research
- Stanford-Fudan KAIROS collab: no evidence found, likely fabricated

## Tracks

1. **Research artifact:** `docs/SOTA_2026_AUDIT.md` — durable, dated, verifiable.
2. **Inline-delivery fix:** Rewrite `skills/global/onboarding-guide/SKILL.md` as inline-delivery contract with 7 beats embedded. Extract 18 explainers to `EXPLAINERS.md`. Trim `onboard.py` to `check` + `explain` only.
3. **Onboarding currency:** Dated header + `state-of-the-field` explainer + role-tuned best practices in Beat 7.
4. **Verified-drift repairs:**
   - 4a. Codex subagent rendering (verify TOML vs YAML; fix if drift)
   - 4b. Gemini-only hook events in canonical schema + `_EVENT_ALIASES`
   - 4c. `AGENTS.override.md` precedence (Codex)
   - 4d. Document `targets:` field as Agent Forge local extension
5. **Citation hygiene:** Fix arXiv 2505.09111 → 2505.06120. Annotate any KAIROS/dream/Fudan-GA references. Audit `LESSONS_LEARNED.md` for fabricated citations. Fix PLANS_COMPLETED.md duplicate `## Entries` headers.
6. **Verification:** `verify-agent-forge.py` exit 0; `validate-triad-runtime.py --project <governed>` exit 0; smoke-test `/onboarding-guide` in fresh Claude Code session.
7. **Handoff:** Update frontmatter status `in-progress` → `completed` at each track close; final merge via `branch-finisher` archives to `docs/archive/PLANS_COMPLETED.md`.

## Out of Scope

- Interactive quizzing onboarding redesign (operator/role/install version detection) — deferred to next sprint per operator's voice note.
- `memory-distiller` skill / `/dream` pattern — KAIROS-inspired, not peer-reviewed; deferred.
- Semantic-trace gate on verification-gate — Code as Agent Harness paper too recent (4 days old) to mandate; documented as watch-item.
- State-machine dispatcher checkpoint persistence — verify `efc74b8 great consolidation` work first; revisit if missing.
- Further skill/team consolidation per SWE-agent ACI — recent commits already did "the great consolidation"; deferred to avoid churn.

## Verification

1. `/onboarding-guide` in fresh Claude Code session produces visible chat output and walks all 7 beats inline.
2. `docs/SOTA_2026_AUDIT.md` is the durable answer to "what 2026 SOTA looks like for this project" — peer agents on any host can re-ground from it.
3. Each of the four verified-drift surfaces is either fixed or proven non-drift, with evidence.
4. arXiv ID error and KAIROS/dream/Fudan-GA claims do not appear unannotated.
5. `verify-agent-forge.py` exits 0 with no new `[WARN]` / `[FAIL]`.
6. `validate-triad-runtime.py --project <first-governed>` exits 0 (or documented sandbox fallback).
7. Bundle (`factory-export.sh --mode onboarding`) still passes COI scrub at zero matches.
