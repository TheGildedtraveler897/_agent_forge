# Agent Forge Handoff

Last updated: 2026-04-04

## What Changed

### Workstation Bootstrap Planning + Execution (2026-04-05, Codex)

Extended the suitcase layer so a freshly unpacked machine can be brought to actual LLM-development readiness instead of only receiving the factory files.

#### Changes Made

1. **Machine bootstrap script** — Added `scripts/bootstrap-workstation.sh` to install base dependencies plus selected hosted coding CLIs (Claude Code, Codex, Gemini CLI) on Debian/Ubuntu or macOS.
2. **Interactive service selection** — The workstation bootstrap now presents an interactive menu for installing one, several, or all hosted CLIs.
3. **Security-conscious Node policy** — Debian/Ubuntu uses native `apt` first and only offers a vetted external Node LTS apt source with explicit operator approval if the distro Node is too old for Gemini CLI.
4. **macOS policy locked to MacPorts** — The first macOS path now assumes MacPorts instead of Homebrew and stops cleanly if MacPorts is missing.
5. **Auth guidance layer** — The bootstrap records and prints the real auth flow for Claude Code, Codex, and Gemini CLI instead of pretending subscription auth can be fully automated.
6. **Open-model phase documented** — Added `docs/OPEN_MODEL_ROADMAP.md` documenting phase 2: Ollama first, OpenRouter second, and the intended low-cost helper-model lane.
7. **Suitcase flow updated** — Deploy output and suitcase docs now point operators to workstation bootstrap before project bootstrap.

### Factory Suitcase Export + Deploy Batch (2026-04-05, Codex)

Added the first explicit portable snapshot workflow for Agent Forge so the factory can be moved to a clean machine or Debian VM without carrying project repos or secrets.

#### Changes Made

1. **Portable suitcase export script** — Added `scripts/factory-export.sh` to build an unpacked suitcase directory plus `.tar.gz` and `.zip` archives. The payload includes `_agent_forge`, shared root doctrine docs, a manifest, and bundle README.
2. **Target-machine deploy script** — Added `scripts/deploy-factory.sh` to install the exported factory snapshot into a target `Projects` root, copy shared doctrine docs, and sync Claude/Codex delivery surfaces.
3. **Target override support for Claude sync** — Extended `sync-claude-adapters.sh` with `--projects-root` and `--claude-home` so deployment can be tested in a VM-style temp root without touching the source machine's active setup.
4. **Suitcase runbook** — Added `docs/FACTORY_SUITCASE.md` covering build, deploy, Debian VM validation, and the next Reddit archive pilot flow.
5. **Portability docs updated** — Expanded `docs/PORTABILITY.md` with the suitcase snapshot model, what is safe to carry, and what must never travel.
6. **Verification coverage expanded** — `verify-agent-forge.py` now checks that the suitcase export/deploy scripts and runbook exist, and that the factory shell scripts are executable.
7. **Isolated smoke test completed** — Exported a suitcase to `/tmp/agent-forge-export`, deployed it into `/tmp/agent-forge-suitcase-smoke`, confirmed root doctrine docs and delivery surfaces, and re-ran deploy successfully with `--replace-factory`.

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
- **Verification:** includes suitcase export/deploy surfaces in addition to the existing skill and governance checks
- **Bootstrap:** workstation bootstrap now covers Debian/Ubuntu and macOS (MacPorts) for hosted CLI setup
- **Skills:** All 17 canonical SKILL.md files have context_cost and model_tier metadata
- **Docs:** factory now includes a dedicated suitcase/export/deploy runbook
- **Suitcase status:** export and isolated deploy smoke test passed; Debian VM proof still pending

## Remaining Weaknesses

1. **No automated eval harness** — Quality-gate is a manual skill invocation, not a CI/CD pipeline. Industry practice is automated evals on every change. Low priority for a one-person corp.
2. **Bootstrap script untested for edge cases** — `bootstrap-project.sh --existing` and `--with-local-skills` paths haven't been exercised with real projects.
3. **No suitcase VM proof yet** — Export and deploy flows are smoke-tested in temp roots, but they still need a real Debian VM validation pass.
4. **No real workstation proof yet** — The bootstrap logic is implemented, but it still needs validation on a fresh Debian VM and a real macOS workstation.
5. **No Codex-side validation** — All verification has been Claude-side. Codex skill discovery and runtime behavior haven't been independently confirmed this session.
6. **Team manifests are conceptual** — No automated team orchestration exists. Teams work by operator selection and manual handoff. This is intentional but limits weaker-model autonomy.
7. **Content freshness** — Domain skills (finance, legal, procurement) embed rate/threshold data that will drift annually. The "verify before citing" mandate handles this at query time but doesn't prevent stale defaults from anchoring weaker models.

## Manual Follow-Up Items

1. Run the first real Debian VM deployment using the validated suitcase flow
2. Run `bootstrap-workstation.sh` on the Debian VM and complete authentication for the selected hosted CLIs
3. Bootstrap `reddit-archive` from the deployed suitcase instead of assembling it manually
4. Exercise `bootstrap-project.sh` against that new project to validate the bootstrap path
5. Consider a Codex validation pass to confirm skill discovery works from that side
6. Use the artifact chain strictly during the Reddit pilot: evidence pack -> implementation brief -> scorecard -> handoff

## Final Verdict

**The factory is materially stronger for future lower-tier model runs.**

The key improvements are the ones that reduce ambiguity for weaker models: worked examples in utility skills, severity-weighted quality gates, filled operator templates, and explicit escalation rules. A Sonnet-class model receiving a task brief built with these templates can execute without needing the full planning context that produced it. The framework's token discipline (selective skill delivery, compaction triggers, context_cost hints) keeps the signal-to-noise ratio high even in constrained contexts.

The architecture is sound, the governance is operational, and the factory is portable. Clone `_agent_forge`, run the sync scripts, bootstrap a project — the accumulated knowledge deploys without rebuilding.
