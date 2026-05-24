# SOTA Agent Governance Drift Audit

- `Date:` 2026-05-23
- `Branch:` `sota-agent-governance-audit`
- `Evidence pack:` `docs/research/sota-agent-governance-evidence.md`
- `Baseline:` `python3 scripts/verify-agent-forge.py` was green before edits; `projects.json` has no governed projects, so project triad validation has no target.

## Findings Fixed

| Severity | Finding | Evidence | Fix |
|---|---|---|---|
| High | Codex project config rendered deprecated `[features].codex_hooks = true`. | Codex hooks docs now document `[features].hooks = true`. | `render_codex_config` now emits `hooks = true`; regression test added. |
| High | Codex hook alias table rejected supported lifecycle events. | Codex hooks docs list subagent and compact lifecycle events. | Added `SubagentStart`, `SubagentStop`, `PreCompact`, and `PostCompact` aliases; regression test added. |
| High | Codex MCP env passthrough rendered `TOKEN = "$TOKEN"` in an env table, conflating passthrough and literal env. | Codex MCP docs distinguish `env_vars` passthrough from literal env assignments. | Codex MCP renderers now use `env_vars = [...]` for passthrough and `.env` only for literals; regression test added. |
| Medium | Claude global sync only generated commands/agents, not native global skill symlinks. | Claude skills docs make skills a first-class native surface. | `sync_claude` now symlinks global skills into `~/.claude/skills` while preserving commands and agents. |
| Medium | Root `GEMINI.md` could duplicate `@AGENTS.md` when the factory repo is treated as the project root. | Local rendered file contained duplicate `@AGENTS.md`. | Gemini project context renderer now deduplicates imports; regression test added. |
| Medium | Docs listed Gemini global skills under `~/.gemini/skills` even though the renderer intentionally uses open-standard `~/.agents/skills` for global skill delivery. | Local docs disagreed with `sync_gemini`. | Updated host-surface docs and the governor checklist to distinguish `~/.agents/skills` global delivery from project `.gemini/skills`. |

## Findings Not Changed

- The canonical `SKILL.md` frontmatter model is retained. The public Agent Skills format does not require abandoning host-routing metadata; Agent Forge needs that metadata to render three hosts from one source.
- `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` remain native boot files. Renaming them to a single neutral name would reduce host-native loading reliability.
- Team manifests remain conceptual orchestration contracts. No primary source requires adding a persistent swarm runtime.

## Verification Targets

- `python3 -m unittest tests.test_current_host_renderers tests.test_hooks_v3 tests.test_mcp_namespace`
- `python3 scripts/omni_factory.py render-registry > registry.json`
- `python3 scripts/verify-agent-forge.py`
- `python3 scripts/validate-triad-runtime.py --project <name>` only when `projects.json` contains at least one governed project.

## Residual Risk

- Vendor docs and installed CLI versions can diverge. The strengthened alias and config tests protect the renderer, but live hook dispatch still requires `validate-triad-runtime.py --probe-invocations` on a governed project.
