# TECH_DEBT

This file records the most important shortcuts and restart hooks from the April 3, 2026 governance sprint.

## Open Debt

- The operator UX remediation pass (2026-04-06) closed the main gaps: one-shot wrapper, auto-sync in bootstrap-project, interactive CONOPS flow, clean/backup export modes, VM operator runbook, workstation ready-state check. Remaining UX gaps are noted below.
- `factory` is still a thin CLI repo. It has not yet absorbed the broader "agent factory" capability discussed during planning.
- Bootstrap coverage is only proven for the default new-project path. `bootstrap-project.sh --existing` and `--with-local-skills` still need deliberate exercise.
- The Governance Team is operationalized, but the Bootstrap Team and Delivery Team are still defined as canonical team manifests rather than full native role artifacts.
- `playlist-archive` has a working Spotify+YouTube downloader (`archive.py`, `install.sh`, 5 commits). Verify current feature gaps and whether further implementation slices are needed before treating it as pending work.
- `RoboNaaz` is still effectively pre-commit as a repo. It needs a deliberate first-commit hygiene pass rather than opportunistic commits.
- `jarvis`, `ZorroClaw`, and `factory` each have mixed local changes. They need repo-by-repo review before any commit decisions.
- `bootstrap-project.sh` intentionally emits starter `TODO` placeholders into new stub docs. That is acceptable, but the template text may need tightening once more projects are bootstrapped.

## Remaining UX Gaps

- No real Debian VM proof from a human operator perspective (only isolated temp-dir smoke tests)
- No real macOS proof
- `deploy-factory.sh` stdout still shows separate sync commands in its "Next steps" section — those are now redundant since `bootstrap-project.sh` auto-syncs, but they are not wrong
- `bootstrap-project.sh --existing` and `--with-local-skills` paths still need deliberate exercise

## First 3 Tasks For Founder Dhillon

1. Run `python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py` to confirm workspace health.
2. Do repo-by-repo commit hygiene for `_agent_forge`, `jarvis`, `ZorroForge/factory`.
3. Review `playlist-archive` current state — working downloader already exists; identify any actual remaining gaps before scoping further work.

## Notes For The Next Session

- Use the workspace `README.md` plus `_agent_forge/docs/AGENTS_AND_TEAMS.md` and `_agent_forge/docs/TEAM_RUNBOOKS.md` as the fastest re-entry path.
- For the next VM/operator polish pass, start with `_agent_forge/docs/FUTURE_WORK_VM_ONBOARDING.md`. That doc now includes: one-shot wrapper, ready checks, auto-sync project bootstrap, interactive first-pass CONOPS generation, and clean-vs-backup export mode separation.
- Do not initialize git at `/home/pheonixprotocol/Projects`.
- Treat `_agent_forge` as the only maintained source of truth for shared skills, teams, and adapters.
