# Hook Schema Examples

These examples document non-command hook handler shapes for future authors.
They are intentionally outside `policies/hooks.json`; the policy file is only
for live canonical hooks that render into host settings.

## HTTP Handler

```json
{
  "id": "example-http-audit",
  "enabled": false,
  "description": "Dormant v3 schema example for Claude HTTP hook rendering.",
  "event": "post_tool_use",
  "matcher": "Write|Edit",
  "handler": {
    "type": "http",
    "url": "http://127.0.0.1:9/agent-forge/example-hook",
    "headers": {},
    "allowed_env_vars": []
  },
  "targets": ["claude"],
  "timeout_ms": 30000
}
```

## MCP Tool Handler

```json
{
  "id": "example-mcp-tool-audit",
  "enabled": false,
  "description": "Dormant v3 schema example for Claude MCP tool hook rendering.",
  "event": "post_tool_use",
  "matcher": "Write|Edit",
  "handler": {
    "type": "mcp_tool",
    "server": "example",
    "tool": "audit_file",
    "input": {
      "file_path": "${tool_input.file_path}"
    }
  },
  "targets": ["claude"],
  "timeout_ms": 30000
}
```

## Prompt Handler

```json
{
  "id": "example-prompt-review",
  "enabled": false,
  "description": "Dormant v3 schema example for Claude prompt hook rendering.",
  "event": "stop",
  "matcher": "",
  "handler": {
    "type": "prompt",
    "prompt": "Review the hook input JSON and return a yes/no JSON decision.",
    "model": "fast"
  },
  "targets": ["claude"],
  "timeout_ms": 30000
}
```

## Agent Handler

```json
{
  "id": "example-agent-review",
  "enabled": false,
  "description": "Dormant v3 schema example for Claude agent hook rendering.",
  "event": "stop",
  "matcher": "",
  "handler": {
    "type": "agent",
    "prompt": "Inspect the changed files and report whether a policy issue exists."
  },
  "targets": ["claude"],
  "timeout_ms": 60000
}
```
