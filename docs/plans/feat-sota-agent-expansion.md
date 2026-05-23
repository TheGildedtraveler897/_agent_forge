---
status: approved
branch: feat/sota-agent-expansion
---
# Plan: SOTA 2026 Agent & Team Expansion (GStack / GSD Integration)

## Objective
Enhance the Agent Forge capability catalog by incorporating the highly specialized, role-based "Cognitive Mode Switching" patterns popularized by the 2026 GStack and GSD frameworks. This involves creating new expert agents and restructuring team blueprints to enforce strict phase-based execution and eliminate context rot.

## Findings from SOTA Research (GStack & GSD)
1. **Cognitive Mode Switching:** SOTA frameworks rely on hyper-specialized roles rather than generalists. An agent shouldn't build *and* review its own code.
2. **Key SOTA Roles to Steal:**
   - **The Paranoid Reviewer:** A dedicated agent that *only* looks for bugs and architectural violations, ignoring style.
   - **The QA/E2E Tester:** An agent equipped with MCP tools to launch browsers (like Playwright) for end-to-end validation.
   - **The Architect/Partner:** A high-level decision-maker (like GStack's `/office-hours`) used *before* planning begins to lock in technical direction.
3. **Phase-Based Execution (GSD):** The "Get Shit Done" framework externalizes state into XML/Markdown files and uses fresh context windows for each phase (Discuss -> Plan -> Execute) to kill context rot.
4. **Nyquist Validation:** A strict SOTA quality gate ensuring a test feedback loop exists *before* production code is written.

## Proposed Expansion

### 1. New Specialized Agents (Expert Skills)
I propose authoring the following new `expert` class skills under `skills/global/`:
- **`paranoid-reviewer`:**
  - *Role:* Code Reviewer.
  - *Instruction:* "You are a hostile, paranoid reviewer. Do not comment on style or formatting. Find memory leaks, race conditions, unhandled exceptions, and architectural violations in the provided diff."
- **`e2e-qa-tester`:**
  - *Role:* End-to-End Validation.
  - *Instruction:* "You are a QA automation engineer. Use available MCP tools to execute Playwright/Cypress tests against the local build. Report failures with reproducible steps."
- **`principal-architect`:**
  - *Role:* Technical Decision Support (replacing vague planning).
  - *Instruction:* "Act as a Principal Engineer. Review the product requirements and propose three technical architectures with trade-offs. We will not write code until an approach is selected."

### 2. New Team Blueprint: `gsd-delivery-team`
I propose adding a new JSON blueprint to `teams/` that implements the strict GSD "Phase-Based" flow:
- **Phase 1 (Discuss):** `principal-architect` + `spec-architect` lock in the design.
- **Phase 2 (Plan):** `execution-planner` breaks the design into atomic tasks.
- **Phase 3 (Execute):** `subagent-dispatcher` orchestrates `tdd-engineer` across fresh context windows.
- **Phase 4 (Review & Gate):** `paranoid-reviewer` audits the output, followed by `e2e-qa-tester` validating the build.

### 3. Implementation Steps
1. Use the `skill-author` capability to scaffold `paranoid-reviewer`, `e2e-qa-tester`, and `principal-architect` into `skills/global/`.
2. Create `teams/gsd-delivery-team.json` with the new roles and escalation paths.
3. Run `python3 scripts/omni_factory.py render-registry` to update the canonical capability list.
4. Run the structural verifier to ensure the new assets align with Agent Forge doctrine.