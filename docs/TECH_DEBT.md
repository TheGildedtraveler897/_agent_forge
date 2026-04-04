# TECH_DEBT

This file records the most important shortcuts and restart hooks from the April 3, 2026 governance sprint.

## Open Debt

- `factory` is still a thin CLI repo. It has not yet absorbed the broader "agent factory" capability discussed during planning.
- Bootstrap coverage is only proven for the default new-project path. `bootstrap-project.sh --existing` and `--with-local-skills` still need deliberate exercise.
- The Governance Team is operationalized, but the Bootstrap Team and Delivery Team are still defined as canonical team manifests rather than full native role artifacts.
- `playlist-archive` is governed and bootstrapped, but no downloader implementation exists yet.
- `RoboNaaz` is still effectively pre-commit as a repo. It needs a deliberate first-commit hygiene pass rather than opportunistic commits.
- `jarvis`, `ZorroClaw`, and `factory` each have mixed local changes. They need repo-by-repo review before any commit decisions.
- `bootstrap-project.sh` intentionally emits starter `TODO` placeholders into new stub docs. That is acceptable, but the template text may need tightening once more projects are bootstrapped.

## First 3 Tasks For Founder Dhillon

1. Run `/home/pheonixprotocol/Projects/_agent_forge/scripts/verify-agent-forge.py` and inspect repo git status to confirm the workspace still matches tonight's handoff.
2. Do repo-by-repo commit hygiene starting with `jarvis`, then decide whether `RoboNaaz`, `ZorroClaw`, `factory`, and `playlist-archive` should receive commits or stay as working state.
3. Start the first real implementation slice for `playlist-archive`, using the Delivery Team model to choose planning, build, and review boundaries up front.

## Notes For The Next Session

- Use the workspace `README.md` plus `_agent_forge/docs/AGENTS_AND_TEAMS.md` and `_agent_forge/docs/TEAM_RUNBOOKS.md` as the fastest re-entry path.
- Do not initialize git at `/home/pheonixprotocol/Projects`.
- Treat `_agent_forge` as the only maintained source of truth for shared skills, teams, and adapters.
