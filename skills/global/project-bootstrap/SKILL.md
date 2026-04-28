---
name: project-bootstrap
description: Bootstrap a new project under ~/Projects with Agent Forge governance files, portable adapters, and sync-friendly multi-agent structure. Use when creating a new governed repo or standardizing an early-stage project to the shared contract.
context_cost: light
model_tier: any
capability_class: workflow
targets: ["claude", "codex", "gemini"]
delivery_projects: ["jarvis"]
---

# Project Bootstrap

Create or standardize a project so it starts with Agent Forge governance from day one.

## Responsibilities

1. Create the required governance files and docs stubs
2. Create the Claude compatibility layer
3. Create project `.claude` adapter directories
4. Add project-local registry expectations when applicable
5. Provide sync and verification steps

## Rules

- Deterministic filesystem work belongs in the bootstrap script
- This skill should explain, plan, and audit the bootstrap process
- New projects should default to the thinnest complete governance footprint:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/CONOPS.md`
  - `docs/HANDOFF.md`
  - `.claude/CLAUDE.md` symlink

## Modes

- bootstrap new project
- standardize existing project
- audit bootstrap compliance without mutating
