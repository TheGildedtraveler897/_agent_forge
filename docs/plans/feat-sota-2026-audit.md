---
status: approved
branch: feat/sota-2026-audit
---
# Plan: SOTA 2026 Deep Audit & Remediation

## Objective
Execute a comprehensive upgrade of `_agent_forge` to align perfectly with the May 2026 State of the Art (SOTA) standards for Claude Code, OpenAI Codex, Gemini CLI, and Model Context Protocol (MCP).

## Findings from Discovery
1. **Agent Instructions:** The industry has standardized on `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` for context-efficient instructions.
2. **The Unified Skill System:** The legacy `.claude/skills/` and `.gemini/skills/` formats have been superseded by a universal `SKILL.md` format located in `.claude/skills/` and `.gemini/skills/`. OpenAI Codex *also* fully adopted this standard (using `.codex/skills/` and the vendor-neutral `.agents/skills/`), meaning all three CLIs are now unified on the exact same format.
3. **Tiered Memory:** SOTA 2026 mandates that `MEMORY.md` is a *Private Project Memory* that should NOT be committed to the repository, to prevent context rot and security leaks.
4. **Agent Definitions:** Subagents/Agents are formally separated from the "Host CLI".
5. **Event Hooks:** SOTA hook mappings need alignment in the synchronization engine (`omni_factory.py`).

## Proposed Solution & Implementation Steps

### 0. Persist Plan & Update Memory
- Save this plan directly to `docs/plans/feat-sota-2026-audit.md` with `status: approved`.
- Add an active task pointer to `MEMORY.md`.

### 1. Refactor Delivery Surfaces to `skills`
- Modify `omni_factory.py`, `bootstrap-project.sh`, `docs/CONOPS.md`, and other governance documents.
- Replace all legacy references of `.claude/skills` with `.claude/skills`.
- Replace all legacy references of `.gemini/skills` with `.gemini/skills`.
- Ensure Codex surfaces are accurately mapped to `.codex/skills` alongside the vendor-neutral `.agents/skills` to guarantee cross-compatibility across all three tools.

### 2. Implement Tiered Memory Security
- Add `MEMORY.md` to `.gitignore` to enforce the local-only tiered memory architecture dictated by SOTA 2026.
- Update `memory-archivist` and `memory-bridge` to handle the un-tracked nature of `MEMORY.md` safely.

### 3. Align Event Hooks in `omni_factory.py`
- Review and update `_EVENT_ALIASES` in `omni_factory.py` to match the exact 2026 lifecycle hook names:
  - **Claude:** `InstructionsLoaded`, `SessionStart`, `SessionEnd`
  - **Gemini:** `BeforeTool`, `AfterTool`, `BeforeAgent`, `AfterAgent`
  - **Codex:** `SessionStart`, `Stop`, `PreToolUse`, `PostToolUse`

### 4. Final Validation
- Run `verify-agent-forge.py` to ensure the new structural alignments pass validation.
- Commit all changes to the `feat/sota-2026-audit` branch.

## Verification & Testing
1. Ensure the structural verifier passes with zero errors.
2. Verify `.gitignore` actively blocks `MEMORY.md`.