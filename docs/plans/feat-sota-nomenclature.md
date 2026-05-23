---
status: approved
branch: feat/sota-nomenclature
---
# Plan: SOTA 2026 Nomenclature Audit & Reconciliation

## Objective
Reconcile Agent Forge's internal terminology and generated directory structures with the actual 2026 SOTA nomenclature used by Claude Code, OpenAI Codex, and Gemini CLI. The goal is 100% factual accuracy for the user's upcoming demo.

## Findings from Discovery
1. **Industry Standard (2026):**
   - **Skills:** Reusable instruction bundles (`SKILL.md`). Invoked via Slash Commands (`/name`).
   - **Agents:** Specialized, isolated context workers (what Agent Forge previously called "Subagents"). Invoked via delegation (`@name` or via planner).
2. **Agent Forge Current State:**
   - Uses `workflow` vs `expert` in `SKILL.md` frontmatter.
   - `omni_factory.py` translates these into legacy directories: `.claude/commands`, `.gemini/commands` (instead of unifying under `/skills` and `/agents`).
   - `onboarding-guide/onboard.py` translation table explicitly misidentifies "Agents" as "Subagents" and "Skills" as "Commands" for Claude/Gemini.

## Proposed Solution & Implementation Steps

### 0. Persist Plan & Update Memory
- Save to `docs/plans/feat-sota-nomenclature.md` (status: approved).
- Add pointer to `MEMORY.md`.

### 1. Update the Onboarding Translation Table
- Modify `skills/global/onboarding-guide/onboard.py` to reflect the factual 2026 reality:
  - **Concept:** Workflow skill -> **Claude:** skill -> **Codex:** skill -> **Gemini:** skill
  - **Concept:** Expert agent -> **Claude:** agent -> **Codex:** (none native) -> **Gemini:** agent
- Update the ASCII diagram labels from `Subagents` to `Agents (Isolated Specialists)`.

### 2. Update `omni_factory.py` Delivery Surfaces
- *Constraint Check:* While renaming the translation table is safe, altering `omni_factory.py` to stop generating `.claude/commands` in favor of `.claude/skills` might break the underlying host CLI if the CLI still expects the legacy path for backwards compatibility, or it might break `validate-triad-runtime.py`.
- **Action:** Update the mapping arrays in `omni_factory.py` so that `workflow` capabilities are explicitly categorized as `skills` (not commands) in the generated user/project manifests. (If host CLIs still require the legacy folder name for execution, we document this quirk in `LESSONS_LEARNED.md` rather than breaking execution).

### 3. Update Canonical Doctrine (`AGENTS.md` & `CONOPS.md`)
- Replace lingering references of "subagents" with "specialist agents" or simply "agents".
- Ensure the terminology aligns: The Main CLI is the "Host CLI", and dispatched workers are "Agents".

## Verification & Testing
1. Run `python3 onboard.py tour --quick` to verify the table output.
2. Run `python3 scripts/verify-agent-forge.py` to ensure structural changes to doctrine didn't break validation.