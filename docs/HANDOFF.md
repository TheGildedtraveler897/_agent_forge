# Agent Forge Handoff

Last updated: 2026-04-06

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

### Operator UX Remediation (2026-04-06, Claude Sonnet)

Implemented all 8 items from `docs/FUTURE_WORK_VM_ONBOARDING.md`.

#### Changes Made

1. **`scripts/deploy-and-bootstrap.sh`** (new) — one-shot machine setup wrapper. Runs deploy then prompts whether to run workstation bootstrap. Interactive by default; `--bootstrap`/`--no-bootstrap` for scripted use. Nothing installed silently.

2. **`bootstrap-workstation.sh` ready-state check** — added `check_ready_state` function that runs after install/auth guidance, checks `--version` for each selected CLI, prints a clear installed/not-found summary, and writes the result to the machine setup log.

3. **`bootstrap-project.sh` auto-sync** — now automatically runs `sync-claude-adapters.sh --project` and `sync-codex-skills.sh` (global only for fresh projects; project-scoped when `--with-local-skills` used) immediately after scaffold creation. No separate manual sync commands needed.

4. **`bootstrap-project.sh` interactive CONOPS** — after scaffold creation, prompts "Would you like to fill in the project definition now?" with 4 guided questions (mission, audience, deliverable, constraints). Writes a richer first-pass CONOPS.md. `--define`/`--no-define` flags for advanced use. Falls back to non-interactive if stdin is not a tty.

5. **`factory-export.sh --mode clean|backup`** — interactive mode selection by default. `clean` (default) strips HANDOFF.md and TECH_DEBT.md with stubs and excludes `runtime/`; all skills, teams, adapters, scripts, and workflow docs preserved. `backup` keeps everything. MANIFEST.json records `export_mode`.

6. **`docs/VM_OPERATOR_RUNBOOK.md`** (new) — dedicated Debian VM walkthrough: archive choice, unpack, one-shot wrapper, manual fallback, auth pitfalls, verify commands, ready-state checklist, refresh rule.

7. **`scripts/verify-agent-forge.py`** — updated to require `deploy-and-bootstrap.sh` (executable) and `VM_OPERATOR_RUNBOOK.md` in coverage.

8. **Docs updated** — FACTORY_SUITCASE.md, WORKSTATION_BOOTSTRAP.md, PORTABILITY.md, TECH_DEBT.md all revised to reflect the new human-first flow.

#### Tests Run

- All 4 modified shell scripts: `bash -n` syntax check — PASS
- `factory-export.sh --mode clean` to isolated `/tmp` — PASS (stubs correct, runtime/ absent, skills preserved, MANIFEST includes export_mode)
- `factory-export.sh --mode backup` — PASS (full HANDOFF.md preserved)
- `deploy-and-bootstrap.sh --no-bootstrap` against isolated temp root — PASS
- `bootstrap-project.sh --no-define` against live source — PASS (Claude sync OK, Codex global sync OK, no spurious warnings)
- `verify-agent-forge.py` — 155 OK, 0 FAIL

## Current State

- **Registry:** v4, 22 skills
- **Teams:** 7 teams, all with escalation rules
- **Verification:** 155 checks, 0 failures
- **Skills:** All SKILL.md files have context_cost and model_tier metadata
- **Operator UX:** one-shot wrapper, auto-sync bootstrap, interactive CONOPS, clean/backup export, VM runbook — all implemented
- **Suitcase status:** smoke-tested in isolated temp roots; real Debian VM proof still pending

## Remaining Weaknesses

1. **No automated eval harness** — Quality-gate is a manual skill invocation. Low priority for a one-person corp.
2. **No real Debian VM proof** — Export/deploy/bootstrap flows are smoke-tested in temp roots but have not been run from a real human operator perspective on a fresh VM.
3. **No real macOS proof** — MacPorts bootstrap path exists but is untested.
4. **`bootstrap-project.sh --existing` and `--with-local-skills`** — paths have not been exercised with real projects.
5. **No Codex-side validation** — All verification is Claude-side. Codex skill discovery and runtime behavior haven't been independently confirmed.
6. **Team manifests are conceptual** — No automated team orchestration. Teams work by operator selection and manual handoff.
7. **Content freshness** — Domain skills embed rate/threshold data that will drift annually.
8. **`deploy-factory.sh` "Next steps" still lists manual sync commands** — now redundant since `bootstrap-project.sh` auto-syncs, but not harmful.

## Manual Follow-Up Items

1. Run a real Debian VM proof: unpack suitcase, run `deploy-and-bootstrap.sh`, authenticate, bootstrap a project, verify
2. Exercise `bootstrap-project.sh --existing` against a real existing repo
3. Commit the UX remediation changes in `_agent_forge`
4. Start the first real implementation slice for `playlist-archive` using the Delivery Team model

## Final Verdict

**The factory is materially stronger for both LLM agents and human operators.**

LLM improvements (from previous pass): worked examples in utility skills, severity-weighted quality gates, filled operator templates, explicit escalation rules.

Human operator improvements (this pass): the system now guides a founder/operator through machine setup with one obvious entry point, asks before installing anything, auto-wires adapters after project bootstrap, and offers to capture the project definition immediately. A non-technical operator can set up a new machine by running one script and answering a few prompts.
