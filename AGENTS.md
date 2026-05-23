# Agent Forge

This workspace is the canonical source of truth for portable multi-agent governance under `~/Projects`.

## Read Order

1. This file
2. `docs/CONOPS.md`
3. `docs/HANDOFF.md`
4. `docs/LESSONS_LEARNED.md` when the task touches prior failures, workarounds, portability traps, or host-integration drift
5. `<project>/MEMORY.md` when working under a governed project — it is the universal cross-host session-state layer (build commands, project quirks, active tasks, recent decisions, known failures). Append-only via the `memory-archivist` skill; never edit anchor lines by hand.
6. The relevant canonical `skills/**/SKILL.md` files and team manifests

## Purpose

- Store canonical capability content in `skills/`
- Keep teams, MCP servers, and hooks in one governed location each
- Generate host-native Claude/Codex/Gemini delivery surfaces from those canonical inputs
- Keep tool-home folders and project-local adapter folders as delivery targets only
- Keep a durable, append-first lesson ledger so validated workarounds survive past one session

## Layout

- `skills/global/`: portable cross-project capabilities
- `skills/projects/<project>/`: project-local capabilities
- `teams/`: canonical starter team definitions and role contracts
- `projects.json`: governed project catalog
- `global-mcp.json`: canonical MCP server inventory
- `policies/hooks.json`: canonical hook policy inventory
- `registry.json`: generated compatibility registry, not an authoring surface
- `CLAUDE.md`: Claude-native boot adapter for this repo
- `GEMINI.md`: Gemini-native boot adapter for this repo
- `scripts/`: sync/export/bootstrap/validation helpers
- `docs/`: governance, portability, and operating doctrine
- `docs/LESSONS_LEARNED.md`: append-first knowledge anchor for durable lessons and promotion candidates
- `runtime/validation-matrix.json`: tracked validation coverage target

## Rules

- Each skill lives in its own folder with `SKILL.md`
- Each team lives as a canonical manifest under `teams/`
- Each capability's metadata lives in its `SKILL.md` frontmatter
- Use `targets` as the canonical host list in capability frontmatter; treat `hosts` as a legacy compatibility alias during migration
- Each MCP server is defined exactly once in `global-mcp.json`
- Generated host surfaces are never hand-edited
- Promote a skill from project-local to global only after removing repo-specific assumptions
- Update canonical skills, teams, MCP, and hooks here first, then sync outward to host-native locations
- `docs/LESSONS_LEARNED.md` is append-first. Do not silently rewrite `AGENTS.md` or `docs/CONOPS.md` when harvesting lessons.
- Promote a lesson from the ledger into doctrine only when it is durable, broad, and worth loading by default.
- Append-first is paired with bounded decay. After a lesson's `Status:` becomes `promoted` and the named doctrine reference resolves, the entry is eligible for archival via `lesson-distiller` to `docs/archive/LESSONS_PROMOTED.md` (the archive file is created on first distillation). `docs/HANDOFF.md` follows the same pattern via `handoff-archiver` and `docs/archive/SPRINTS.md`. Distillation is reversible (the archive is the on-disk wisdom anchor) and operator-gated. The retention contract lives in `policies/distillation.json`.
- If Codex is the active host, treat `docs/LESSONS_LEARNED.md` as required supporting context when this file or a generated agent points to prior workarounds.
- After any canonical skill, team, MCP, or hook change, run `python3 scripts/validate-triad-runtime.py --project <name>` as the final runtime gate. The structural verifier confirms files on disk; only the triad validator confirms the three host CLIs can actually enumerate and reach those skills. Sandbox-blocked Codex passes only when paired with filesystem evidence per the 2026-04-23 escalation rule.
- Global skills default to delivery across every governed project listed in `projects.json`. Use `delivery_projects: ["*"]` to restate the default explicitly, a specific list (e.g. `["my-app"]`) to narrow, or `delivery_projects: []` as the explicit opt-out for global-only skills.
- Prefer narrow tool calls over heroic compound shell commands. One question per Bash invocation when inspecting state across many files or projects; reserve `&&` / `;` chains for short related steps where rolling back partial completion is fine. Compound commands with thick output (mixed stdout/stderr, large JSON, multi-section payloads) are more likely to hit harness-level tool-result delivery failures.
- Treat `[Tool result missing due to internal error]` as a re-grounding signal, not a retry signal. The next tool call after a delivery failure must be a small read-only re-ground (`git status`, one `ls`, one `Read`) before any heavier work — never a retry of the failed compound command.
- `master` and `main` are integration-only. Non-trivial implementation work must happen on a named task branch, and simultaneous agents must use separate branches unless they are deliberately pairing on the same work.
- Before any handoff, rate-limit stop, model swap, or end-of-day pause, commit the current branch state and push it upstream. The handoff must name the branch, latest commit, next task, the path to the active plan file (if `docs/plans/<branch-slug>.md` exists), and any dirty state that intentionally remains.
- Use `scripts/enforce-branch-discipline.sh` as the branch preflight for implementation work. It may be bypassed on `master`/`main` only for explicit integration or release actions.
- Plans authored by `execution-planner` persist to `docs/plans/<branch-slug>.md` with frontmatter status (`awaiting-approval`, `approved`, `in-progress`, `superseded`, `completed`). The plan is committed before the human approval gate so it survives session glitches, context overflow, and model swaps. Peer agents on other hosts discover it via the `MEMORY.md active_tasks` pointer and read the file directly when they need execution detail. On merge, `branch-finisher` archives the plan to `docs/archive/PLANS_COMPLETED.md` and removes the active file — one plan per active branch, no `docs/plans/` bloat.

## Operator Tips

- If the agent's progress indicator has been moving for >5 minutes with no token consumption visible, it is almost certainly waiting on a stuck tool-result delivery, not reasoning. A short interrupt + "are you stuck?" prompt re-grounds the agent on the next turn at near-zero cost. The working tree is preserved; nothing is lost.

## Workflow Discipline Chain

The default chain for any non-trivial code change under a governed project is:

1. `spec-architect` — adversarial spec discovery with one-question-at-a-time and section-by-section human approval.
2. `execution-planner` — decomposition into 2–5 minute micro-tasks with exact file paths, embedded RED tests, and explicit verification commands.
3. `tdd-engineer` — RED/GREEN/REFACTOR execution with a watched failing test gate and a three-fix architecture stop.
4. `subagent-dispatcher` — optional parallel or sequential delegation with fresh-context isolation and a two-stage review loop.
5. `verification-gate` — fresh-evidence completion gate; prior runs, code inspection, and agent reports are insufficient.
6. `branch-finisher` — tests-must-pass gate, typed confirmation on destructive actions, post-merge re-verification, no hook or signature bypass.

Escape hatches inside the chain:

- `root-cause-analyst` — invoked when `tdd-engineer` hits its three-fix stop or any time a bug must be understood before it is patched.
- `code-review-doctrine` — invoked for both giving and receiving code review; receiving discipline requires STOP-and-ASK on unclear feedback.
- `skill-author` — meta-skill used only when authoring or revising a skill under `skills/`.
