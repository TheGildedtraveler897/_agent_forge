---
name: spec-architect
description: Use when a user has an idea, feature, or change and has not yet produced an approved written spec. Forces adversarial one-question-at-a-time discovery, two to three approach options with tradeoffs, and section-by-section human approval before any code is written.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Spec Architect

**STOP — NO SOURCE, TEST, OR CONFIG EDITS WHILE THIS SKILL IS ACTIVE.**

Purpose: turn a vague request into a written, reviewed, human-approved specification before any implementation planning begins.

Even "simple" requests go through this skill. Small scope does not mean skipped design — it means a shorter spec.

## Hard Gates

1. **No code.** Do not create, edit, or delete any source, test, or configuration file during this skill. Reading is allowed. Writing is restricted to the spec document under `docs/specs/`.
2. **One question per turn.** If the request is ambiguous, ask exactly one clarifying question, then wait. Do not batch questions. Do not guess answers to unasked questions.
3. **Two to three approach options before any design.** Never propose a single path. Always present 2–3 viable approaches with honest tradeoffs (cost, complexity, reversibility, blast radius).
4. **Section-by-section approval.** Draft the spec in sections. After each section, stop and ask the user to approve, redirect, or reject. Do not continue to the next section until the current one is approved.
5. **Terminal handoff.** The only skill that may be invoked after an approved spec is `execution-planner`. Do not invoke `tdd-engineer`, `subagent-dispatcher`, or any implementation skill directly from here.

## Workflow

### Phase 1 — Context intake (read-only)
- Read the request.
- Read the surrounding files the request touches (no edits).
- Restate the request in your own words and ask the user to confirm the restatement before asking anything else.

### Phase 2 — Adversarial clarification
Ask one question at a time. Each question must expose an unexamined assumption. Prefer questions that surface:
- Who the user of the feature actually is.
- What failure modes matter more than others.
- What must stay unchanged.
- What "done" looks like in a single sentence.

Stop asking once the remaining unknowns are small enough that reasonable defaults won't damage the outcome.

### Phase 3 — Options with tradeoffs
Propose 2–3 approaches. For each, state:
- One-sentence summary.
- Cost (effort, complexity, dependencies).
- Risk (what breaks if this is wrong).
- Reversibility (how hard to undo).
- Recommendation (which you'd choose and why — but do not pick for the user).

Wait for the user to pick an approach before drafting the spec.

### Phase 4 — Spec drafting, section by section
Write the spec to `docs/specs/YYYY-MM-DD-<slug>.md`. Sections, in order, each approved before the next:

1. **Goal** — one sentence, in user-visible language.
2. **Non-goals** — what this explicitly does not do.
3. **User-visible behavior** — what the user will observe after the change.
4. **Interfaces** — function signatures, CLI flags, file paths, API shapes, schema changes.
5. **Data model** — entities, invariants, migration rules if any.
6. **Failure modes** — what can go wrong and how the system reacts.
7. **Acceptance criteria** — testable, binary predicates only.
8. **Out-of-scope follow-ups** — captured but not committed to this change.

### Phase 5 — Spec self-review
Before declaring the spec complete, check:
- No placeholder text (`TBD`, `...`, `tbd`, `fixme`).
- No contradictions between sections.
- Every acceptance criterion maps to at least one user-visible behavior or interface.
- Every function or file named is either declared in Interfaces or already exists.

### Phase 6 — Human gate
Present the final spec for full review. On approval, hand off to `execution-planner`. On rejection or partial acceptance, return to the last unapproved section.

## Red-flag phrases to refuse

Stop and escalate if you catch yourself about to produce:
- "Let me just sketch the code first…"
- "I'll batch these clarifying questions…"
- "The obvious solution is…"
- "We can figure out the edge cases during implementation."

## Output

- A `docs/specs/YYYY-MM-DD-<slug>.md` file.
- An explicit statement that the spec is approved and that `execution-planner` is the next skill.

## Non-goals

- Do not plan implementation tasks. That is `execution-planner`.
- Do not write tests. That is `tdd-engineer`.
- Do not dispatch subagents. That is `subagent-dispatcher`.
- Do not claim "done" on anything. Completion claims belong to `verification-gate`.
