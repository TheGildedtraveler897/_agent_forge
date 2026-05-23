# SOTA Agent Governance Evidence Pack

- `Question:` Which current public standards should Agent Forge align to for agent instructions, skills, subagents, hooks, MCP, memory/context, and generated host surfaces?
- `Retrieved:` 2026-05-23
- `Status:` source-backed implementation evidence for the 2026 drift repair pass.

## Sources

| Source | Type | Practical claim used |
|---|---|---|
| https://agents.md/ | Vendor-neutral standard | `AGENTS.md` is the portable project instruction file that agents can discover without vendor-specific file names. |
| https://agentskills.io/ | Vendor-neutral standard | Agent Skills are portable capability folders centered on `SKILL.md`; `.agents/skills` is the cross-tool installation surface. |
| https://code.claude.com/docs/en/skills | Official Claude docs | Claude Code has first-class skills and supports personal/project skill directories. |
| https://code.claude.com/docs/en/sub-agents | Official Claude docs | Claude subagents are file-backed specialized agents under `.claude/agents`-style surfaces. |
| https://docs.anthropic.com/en/docs/claude-code/hooks | Official Claude docs | Claude hooks use named lifecycle events and can call command, HTTP, MCP tool, prompt, or agent handlers. |
| https://developers.openai.com/codex/guides/agents-md | Official Codex docs | Codex uses `AGENTS.md` as its native project guidance file. |
| https://developers.openai.com/codex/skills | Official Codex docs | Codex supports Agent Skills and the `.agents/skills` discovery surface. |
| https://developers.openai.com/codex/subagents | Official Codex docs | Codex custom agents are configured separately from skills and can attach skills. |
| https://developers.openai.com/codex/hooks | Official Codex docs | Codex hooks require `[features].hooks = true`; legacy `codex_hooks` is deprecated, and the event table includes compact and subagent lifecycle events. |
| https://developers.openai.com/codex/mcp | Official Codex docs | Codex MCP server config supports `enabled_tools`, `disabled_tools`, `env_vars`, literal env tables, and HTTP header/env-header fields. |
| https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills.md | Official Gemini CLI repo docs | Gemini CLI discovers Agent Skills from `.agents/skills` and Gemini-specific skill paths. |
| https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/configuration.md | Official Gemini CLI repo docs | Gemini settings support context file configuration and host settings in `settings.json`. |
| https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md | Official Gemini CLI repo docs | Gemini subagents are file-backed role definitions under Gemini agent surfaces. |
| https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/writing-hooks.md | Official Gemini CLI repo docs | Gemini hook event names are PascalCase names such as `BeforeTool`, `AfterTool`, `SessionStart`, and `SessionEnd`. |
| https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md | Official Gemini CLI repo docs | Gemini MCP servers render through `settings.json` with command/args or URL-style transports. |
| https://modelcontextprotocol.io/specification/latest | Official MCP spec | MCP remains the cross-host protocol boundary for tool/resource/prompt exposure and versioned client-server behavior. |

## Confirmed Findings

- Agent Forge's canonical-first model remains aligned: one `SKILL.md`, one hook policy, one MCP inventory, and generated host surfaces are still the correct architecture.
- `AGENTS.md` should stay the portable repo instruction contract; `CLAUDE.md` and `GEMINI.md` should remain thin native adapters where those hosts expect native context files.
- Agent Skills are now the strongest shared abstraction. The factory should expose them through `.agents/skills` for open-standard discovery and through host-native skill directories where a host has one.
- Claude has a native `~/.claude/skills` / project `.claude/skills` skill surface. Continuing to generate slash commands is useful for command ergonomics, but skills should also be present natively.
- Codex current hook config uses `[features].hooks = true`. `codex_hooks` is documented only as a deprecated compatibility alias.
- Codex current hook event coverage includes subagent and compact lifecycle events that Agent Forge's previous alias table did not expose.
- Codex MCP env passthrough should render as `env_vars = [...]`; literal environment assignments belong in the server `.env` table.
- Gemini uses PascalCase hook names and supports Agent Skills discovery. The factory's project `.gemini/skills` side remains valid, while global open-standard skills should be documented as `~/.agents/skills` to match the renderer.
- MCP latest remains protocol-centric; no source requires Agent Forge to replace its canonical `global-mcp.json` inventory with host-native authoring.

## Conflicts Or Uncertainty

- Host vendors increasingly support both native skill folders and the open `.agents/skills` location. The safest factory posture is additive: render native skill surfaces where supported, keep `.agents/skills` as the vendor-neutral baseline, and avoid duplicate host-specific skill copies where the generator intentionally centralizes global skills.
- Some host docs evolve faster than local CLIs. Runtime validation must continue checking real rendered event keys and skill visibility rather than accepting syntactic config only.

## Practical Implications

- Fix renderer drift for Codex hook feature naming, Codex hook aliases, Codex MCP env passthrough, Claude global skill delivery, and duplicated Gemini root imports.
- Update operator docs to distinguish global open-standard skills from host-specific project skill folders.
- Preserve current canonical schema names (`targets`, `delivery_projects`, `capability_class`) because they model host delivery decisions without binding to one vendor's nomenclature.

## Recommended Next Step

Apply the confirmed drift fixes, add regression tests around the changed renderers, regenerate generated root surfaces through the factory path, and verify with the structural verifier plus targeted unit tests.
