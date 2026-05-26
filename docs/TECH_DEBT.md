# Agent Forge Tech Debt

Framework-level debt items are tracked here. Add an entry when you discover a gap that has a clear closure path; promote items into `docs/HANDOFF.md` § Next Evolution when scheduled.

## Open

### Codex subagent TOML: render `model_reasoning_effort` and per-agent `mcp_servers`

- `Discovered:` 2026-05-26 (enterprise-readiness audit; confirmed in `scripts/omni_factory.py:render_codex_agent` ~641-663)
- `Impact:` Rendered `.codex/agents/*.toml` files emit only `name`, `description`, `sandbox_mode`, `developer_instructions`, and a `[[skills.config]]` table. Codex 2026 documents `model_reasoning_effort` and per-agent `mcp_servers` as supported fields; not rendering them means the factory can't express per-agent reasoning effort or MCP inheritance. Currently MCP is project-scoped via `render_codex_config`, which is acceptable but not full parity.
- `Closure plan:` Extend `render_codex_agent` to optionally emit `model_reasoning_effort` (from a new frontmatter field) and per-agent `mcp_servers` (derived from `requires_mcp_servers`). Gate on primary-source re-verification of the Codex TOML schema. Document in `docs/HOST_INTEGRATIONS.md` § Codex subagent rendering. Add renderer + verifier coverage.
- `Owner:` operator (scheduled follow-on sprint)
- `Status:` open

### Migrate SKILL.md local extensions under `metadata.agent_forge.*`

- `Discovered:` 2026-05-26 (standards re-verification against https://agentskills.io/specification)
- `Impact:` Agent Forge carries `targets`, `capability_class`, `delivery_projects`, `context_cost`, `model_tier`, command-name overrides, sandbox, and MCP-requirement fields as TOP-LEVEL `SKILL.md` frontmatter. The spec sanctions `metadata` (a string→string map) as the home for client-specific properties, recommending unique keys to avoid conflicts. Top-level extra keys are not forbidden, but `metadata.agent_forge.*` is the spec-aligned pattern.
- `Closure plan:` Add backward-compatible parsing in `scripts/omni_factory.py` (accept both top-level and `metadata.agent_forge.*`), update `scripts/verify-agent-forge.py`, migrate all 30 `SKILL.md` files, then document in `docs/CONOPS.md` § Standard vs Local Extensions. Backward-compatible renderer+verifier first; no flag-day churn.
- `Owner:` operator (scheduled follow-on; not worth churning mid-audit)
- `Status:` open

### RHEL-family runtime proof on a real host

- `Discovered:` 2026-05-26 (enterprise-readiness audit, Phase 2)
- `Impact:` `bootstrap-workstation.sh` now has a dnf/yum path, but it is only structurally verified on Linux (bash -n + static tests). The EPEL-provides-ripgrep/jq path (and any CRB/PowerTools dependency), the `nodejs:20` AppStream module availability per RHEL minor, NodeSource RPM behind a proxy, and whether `npm install -g` hits EACCES on the dnf global prefix are unproven without a real RHEL/Rocky/Alma/Fedora host.
- `Closure plan:` Run `bootstrap-workstation.sh` end-to-end on a Rocky/Alma or RHEL VM; capture evidence under `runtime/validation/`. If npm EACCES occurs on the dnf prefix, add `dnf` to the `npm_global_install` sudo branch (mirrors the MacPorts fix).
- `Owner:` operator (needs RHEL host)
- `Status:` open

### Windows native runtime proof on a real host

- `Discovered:` 2026-05-26 (enterprise-readiness audit, Phases 3-4)
- `Impact:` Full PowerShell parity + the `omni_factory.py` symlink→copy fallback are statically verified on Linux only. The symlink-denial path (WinError 1314 without Developer Mode), `Resolve-Python` parsing `py -3 --version`, winget/npm install placing the three CLIs on PATH, `MakeRelativeUri` path output, and `projects.json` round-trip + `verify` on a Windows-registered project remain VM-gated.
- `Closure plan:` Run the Windows VM checklist (`runtime/validation/windows-<date>.md`) end to end; capture evidence; set `validation-matrix.json` `windows.pass` against captured output only.
- `Owner:` operator (needs Windows VM)
- `Status:` open

### macOS Beat 0 inline render proof

- `Discovered:` 2026-05-25 (NRC ship handoff)
- `Impact:` macOS CLIs and `bootstrap-project.sh` are confirmed on a real Mac, but the `/onboarding-guide` Beat 0 inline-render acceptance gate has not been observed on macOS. `mac.pass` in `validation-matrix.json` stays unset until it is.
- `Closure plan:` Run `/onboarding-guide` in Claude Code on the Mac; confirm Beat 0 greeting + experience prompt render inline; set `mac.pass = true`.
- `Owner:` operator (needs macOS host)
- `Status:` open

## Recently Resolved

_Resolved items land here for one milestone before being removed._

---

## Entry Template

### <short title>

- `Discovered:` YYYY-MM-DD
- `Impact:` what breaks or is harder than it should be
- `Closure plan:` how this gets fixed
- `Owner:` agent or operator responsible
- `Status:` `open`, `in-progress`, `resolved`
