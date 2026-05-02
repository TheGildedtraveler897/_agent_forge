---
name: codebase-cartographer
description: Use when a repo must be mapped before planning, when brownfield codebase intelligence is needed, or when structural drift is suspected.
capability_class: workflow
targets: ["claude", "codex", "gemini"]
context_cost: light
model_tier: any
---

# Codebase Cartographer

Purpose: map a repository into compact, planning-ready codebase intelligence. Use this before `spec-architect` or `execution-planner` when the repo shape is unknown, when a brownfield system needs orientation, or when structural drift is suspected.

## Hard Gates

1. **Facts before patterns.** Separate confirmed facts from inferred patterns. Do not present guesses, naming conventions, or likely architecture as proven.
2. **No competing state root.** Do not create `.planning/` or another hidden planning system. Output to an evidence pack or an accepted project-local codebase map.
3. **Smallest useful map.** Use `fast` when a focused orientation is enough. Use `full` only when planning risk justifies a broader scan.
4. **Freshness required.** Every output includes a freshness timestamp, the git reference or working-tree state inspected, and any scan limits.
5. **Read-only by default.** This skill maps and reports. Do not edit code, regenerate docs, or repair drift unless the user explicitly asks for a follow-up implementation task.

## Modes

- `fast`: map the minimum surfaces needed for near-term planning. Use for small changes, quick orientation, or a bounded subsystem.
- `full`: map the repo broadly enough for a new agent to understand stack, architecture, conventions, risks, tests, integrations, entrypoints, generated surfaces, and freshness timestamp.
- `focus quality`: emphasize maintainability, test strategy, dependency risk, generated output risk, and areas that need review before implementation.
- `focus concerns`: emphasize suspected failure modes, architectural seams, ownership ambiguity, portability risk, security-sensitive surfaces, and structural drift.
- `diff since <ref>`: map structural changes since the named git reference. Use this after a branch, sprint, migration, or large refactor.

## Workflow

### Step 1 - Scope the map

Identify the target repository, mode, and planning question. If no mode is named:
- Use `fast` for one subsystem or a small change.
- Use `full` for a new repo, brownfield onboarding, major planning, or unclear architecture.
- Use `diff since <ref>` when the user names a base commit, branch, tag, or previous release.

### Step 2 - Gather confirmed facts

Inspect only what is needed for the chosen mode:
- Top-level files and directories.
- Build, test, package, and runtime manifests.
- Entrypoints and command surfaces.
- Test directories and verification commands.
- Integration surfaces such as APIs, CLIs, queues, databases, external services, hooks, MCP servers, generated adapters, and deployment files.
- Generated surfaces and canonical source files that produce them.
- Recent commits or diffs when running `diff since <ref>`.

Record sources as file paths, manifest names, commands inspected, or git refs. If a fact cannot be tied to evidence, move it to inferred patterns.

### Step 3 - Identify inferred patterns

Infer patterns only after the confirmed facts are listed. Mark them explicitly as inferred:
- Architecture style.
- Ownership boundaries.
- Naming and layout conventions.
- Testing discipline.
- Coupling and risk hotspots.
- Drift between docs, generated surfaces, and source-of-truth files.

### Step 4 - Produce the map

Default output location:
- For planning evidence: `docs/research/YYYY-MM-DD-<slug>-codebase-map.md`.
- For an accepted project-local map: `docs/codebase-map/<slug>.md`.
- For transient local evidence: mention the inspected paths in the response and do not create files unless the user asked for an artifact.

Do not write `.planning/`.

### Step 5 - Hand off

Route the output based on what the map found:
- To `evidence-packager` when broad research needs compacting.
- To `spec-architect` when product or architecture decisions remain.
- To `execution-planner` when scope is clear and implementation can be decomposed.
- To `portability-auditor` for suitcase or host-specific portability findings.
- To `multi-agent-governor` for Agent Forge governance drift.

## Output Contract

Every codebase map includes:

```text
Mode: <full|fast|focus quality|focus concerns|diff since <ref>>
Target: <repo or subsystem>
Freshness timestamp: <ISO-8601 timestamp and timezone>
Git state: <branch/ref/commit and dirty state if known>
Scan limits: <what was intentionally skipped>

Confirmed facts:
- Stack: <languages, frameworks, runtimes, package managers>
- Architecture: <observed modules, layers, data flow, boundaries>
- Conventions: <naming, layout, config, docs, generated-source rules>
- Tests: <test frameworks, commands, coverage gaps, required gates>
- Integrations: <external services, CLIs, databases, queues, hooks, MCP, adapters>
- Entrypoints: <apps, scripts, commands, services, jobs>
- Generated surfaces: <generated files and their canonical sources>
- Risks: <confirmed risks tied to evidence>

Inferred patterns:
- <pattern and why it is inferred, not proven>

Structural drift:
- <docs/code/generated/source drift, or "none observed within scan limits">

Next planning implications:
- <what spec-architect, execution-planner, or another skill should do next>
```

## Red-flag Patterns To Refuse

- Treating an inferred architecture as confirmed because directory names look familiar.
- Producing a map without a freshness timestamp.
- Creating `.planning/` or hiding map state outside Agent Forge primitives.
- Updating docs or generated surfaces while claiming to only map the codebase.
- Ignoring generated surfaces when the project has canonical source files.
- Claiming "no drift" without naming scan limits.

## Non-goals

- Do not package broad external research; that is `evidence-packager`.
- Do not perform suitcase portability remediation; that is `portability-auditor`.
- Do not audit Agent Forge host delivery alignment; that is `multi-agent-governor`.
- Do not write implementation plans; that is `execution-planner`.
- Do not edit code or docs unless the user explicitly asks for a follow-up implementation task.
