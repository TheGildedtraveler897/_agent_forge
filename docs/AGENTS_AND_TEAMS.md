# Agents, Skills, And Teams

This document defines the canonical Agent Forge model for reusable skills, specialized agents, and starter agent teams.

## 1. Skills

Skills are reusable knowledge and workflow packs.

Properties:
- low-cost and composable
- durable and portable
- often tool-agnostic
- live canonically under `skills/`

Use a skill when:
- the work is mostly procedural
- the same audit or build logic repeats across repos
- you want the knowledge portable across Claude, Codex, and future tools

Examples:
- `multi-agent-governor`
- `project-bootstrap`
- `portability-auditor`

## 2. Agents

Agents are specialized workers with bounded scope, separate context, and tool access.

Properties:
- narrower than a general assistant
- often role-based rather than workflow-based
- good for work that benefits from separation of concerns or distinct context windows

Agent Forge mapping:
- Claude native: subagents
- Codex native: delegated runtime agents, often guided by skills

Use an agent when:
- the job benefits from distinct responsibility and context
- the role needs a clear stopping condition and handoff artifact
- you do not want one worker doing planning, implementation, and review all at once

## 3. Agent Teams

Agent teams are named multi-agent patterns with explicit role boundaries and handoff rules.

Properties:
- usually 2-4 roles
- role ownership is explicit
- handoff artifacts are defined
- stop conditions are defined
- portable concept first, tool-specific implementation second

Use a team when:
- one skill is not enough
- one agent would become a “god agent”
- you need explicit planning, execution, and verification phases

## 4. Design Rules

All teams in Agent Forge follow these rules:

- specialists stay narrow
- use handoff artifacts over hidden memory
- keep governance audit-first
- separate planning from implementation when risk is material
- keep canonical truth in repo docs and `_agent_forge`, not tool-home folders
- do not automate swarms before the roles are understandable by a human

## 5. Claude And Codex Mapping

### Claude

- skills are represented indirectly through canonical `SKILL.md` plus native adapters
- agents are subagents in `.claude/agents/` or `~/.claude/agents/`
- utility workflows are slash commands in `.claude/commands/` or `~/.claude/commands/`
- hooks enforce session or tool rules, but are not the team model

### Codex

- skills are native entries under `~/.codex/skills/`
- agents are delegated runtime workers
- teams are orchestrated patterns that combine delegated workers with skill-guided behavior

## 6. The First Three Teams

### Governance Team

Purpose:
- keep projects aligned with Agent Forge contracts and portability rules

Roles:
- governor-auditor
- portability-reviewer
- remediation-planner

Handoff artifacts:
- findings report
- remediation checklist

### Bootstrap Team

Purpose:
- create or standardize governed projects correctly

Roles:
- scaffold-planner
- bootstrap-executor
- post-bootstrap-verifier

Handoff artifacts:
- project scaffold summary
- verification result
- follow-up checklist

### Delivery Team

Purpose:
- do actual product work in a repo without collapsing planning, building, and review into one role

Roles:
- architect-planner
- builder-implementer
- reviewer-tester

Handoff artifacts:
- implementation plan
- code/result summary
- findings or test result report

## 7. What We Are Not Doing Yet

Not yet in scope:
- fully automated swarms
- persistent autonomous teams running unsupervised
- deep orchestration engines
- tool-specific team runtimes beyond the current starter model

The current goal is a portable conceptual and governance-safe system first.
