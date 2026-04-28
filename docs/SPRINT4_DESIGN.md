# Sprint 4 Design: MCP Namespace Prefixing & Routing

Date: 2026-04-27

## Objective

Ship the first real shared MCP server through the omni-factory and make MCP namespace collisions structurally visible before additional servers land.

Sprint 4 extends the same canonical-first pattern proven by hooks and memory:

1. Author MCP servers once in `global-mcp.json`.
2. Render host-native Claude, Codex, and Gemini MCP surfaces.
3. Validate rendered surfaces through `verify-agent-forge.py` and `validate-triad-runtime.py`.

## Web Verification Findings

- MCP itself still leaves namespace policy to clients. Discussion #128 confirms the collision problem and recommends client-side/server-name prefixing rather than a protocol-native namespace field.
- MCP architecture currently centers `stdio` and `streamable_http`; SSE remains host-supported but is not the proof target for this sprint.
- Codex CLI 0.124.0 supports project-scoped `.codex/config.toml` only in trusted projects, and streamable HTTP bearer auth uses `bearer_token_env_var`.
- Gemini CLI 0.39.1 unconditionally renders discovered MCP tools as `mcp_{serverName}_{toolName}` and warns that underscores in server names break policy parsing.
- Claude Code project MCP is stored in `.mcp.json`; project-scoped MCP use prompts for approval before the server is used.

## Schema

`global-mcp.json` moves to version 2 while keeping the existing map-shaped `servers` object:

```json
{
  "version": 2,
  "defaults": {
    "startup_timeout_ms": 20000,
    "tool_timeout_ms": 60000,
    "required": false,
    "trust_server": false,
    "parallel_safe": false
  },
  "servers": {
    "forge-factory": {
      "prefix": "forge.factory",
      "description": "Local Agent Forge factory MCP server.",
      "scope": "shared",
      "projects": "*",
      "targets": ["claude", "codex", "gemini"],
      "transport": {
             "type": "stdio",
             "command": "sh",
             "args": ["-c", "exec python3 \"$HOME/Projects/_agent_forge/scripts/mcp/forge_factory_server.py\""]
           },
      "auth": "none",
      "trust": "local",
      "tool_filter": ["read_handoff"],
      "env_passthrough": [],
      "env_literal": {},
      "headers": {}
    }
  }
}
```

Important distinction: `prefix` is the canonical semantic namespace. Host configs use the derived server alias `forge-factory`, because Gemini mandates `mcp_{serverName}_{toolName}` and Claude uses the `mcp__server__tool` convention. We do not render undocumented `prefix` keys into host configs.

## Renderer Rules

- Claude `.mcp.json`: key the server as `forge-factory`, render `stdio` as `type`, `command`, `args`, `env`, and `headers` where present.
- Codex `.codex/config.toml`: key `[mcp_servers.forge-factory]`, render `command`/`args` for stdio, `url` plus `bearer_token_env_var` for streamable HTTP, and `enabled_tools` from `tool_filter`.
- Gemini `.gemini/settings.json`: key `mcpServers.forge-factory`, render `includeTools` from `tool_filter`, and rely on Gemini's native `mcp_forge-factory_read_handoff` FQN.

## Trust Model

- The Sprint 4 proof server is local stdio only and carries no secrets.
- Remote or privileged project-scoped servers must emit only to projects with `trusted_workspace: true` in `projects.json`.
- Credentials never live in `global-mcp.json`; they flow through `env_passthrough`, `headers` with environment interpolation, or Codex `bearer_token_env_var` for streamable HTTP.

## Validation

`verify-agent-forge.py` must reject:

- unsupported `global-mcp.json` versions;
- missing or duplicate `prefix` values;
- invalid targets, scopes, auth modes, trust modes, or transport types;
- Gemini-targeted server aliases containing underscores;
- non-string `tool_filter` entries;
- remote/project-scoped servers selected for untrusted projects.

`validate-triad-runtime.py` gains `mcp_surface_for(host, root)` and records `mcp_pass` per host. The first gate checks host config surfaces plus direct stdio JSON-RPC smoke evidence for `forge-factory.read_handoff`; deeper native CLI enumeration remains a manual spot check because host MCP UIs are interactive.
