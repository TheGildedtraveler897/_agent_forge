# Bundle Check

- Date: 2026-05-23
- Export command: `scripts/factory-export.sh --mode onboarding --name agent-forge-suitcase-20260523-validation`
- Export directory: `exports/agent-forge-suitcase-20260523-validation`
- ZIP: `exports/agent-forge-suitcase-20260523-validation.zip`
- Windows sidecar: `exports/agent-forge-suitcase-20260523-validation-deploy-and-bootstrap.ps1`
- Required files present in ZIP:
  - `_agent_forge/AGENTS.md`
  - `_agent_forge/docs/CONOPS.md`
  - `_agent_forge/policies/hooks.json`
  - `_agent_forge/scripts/deploy-and-bootstrap.ps1`
  - `_agent_forge/scripts/bootstrap-workstation.ps1`
  - `_agent_forge/docs/HOOK_EXAMPLES.md`
- COI grep: exit 1 with empty stdout/stderr means zero matches.
- Cache scrub: no `__pycache__` directories or `*.pyc` files were found in the regenerated export directory.
