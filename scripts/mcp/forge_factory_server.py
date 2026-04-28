#!/usr/bin/env python3
"""Minimal Agent Forge MCP server.

This local stdio server is intentionally small. It exists to prove the
omni-factory MCP rendering path without introducing external credentials,
network auth, or third-party server drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDOFF_PATH = ROOT / "docs" / "HANDOFF.md"
PROTOCOL_VERSION = "2025-06-18"


def _result(request_id: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def read_handoff(max_chars: int = 12000) -> str:
    if not HANDOFF_PATH.exists():
        return "HANDOFF.md is not present."
    body = HANDOFF_PATH.read_text()
    if max_chars <= 0:
        return body
    return body[:max_chars]


def tools_list() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "read_handoff",
                "description": "Read Agent Forge docs/HANDOFF.md for current sprint state.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_chars": {
                            "type": "integer",
                            "description": "Maximum characters to return. Defaults to 12000.",
                            "minimum": 1,
                        }
                    },
                    "additionalProperties": False,
                },
            }
        ]
    }


def tools_call(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name != "read_handoff":
        raise ValueError(f"Unknown tool: {name}")
    max_chars = arguments.get("max_chars", 12000)
    if not isinstance(max_chars, int):
        raise ValueError("max_chars must be an integer")
    return {
        "content": [
            {
                "type": "text",
                "text": read_handoff(max_chars=max_chars),
            }
        ],
        "isError": False,
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        client_protocol = (params or {}).get("protocolVersion") or PROTOCOL_VERSION
        return _result(
            request_id,
            {
                "protocolVersion": client_protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "forge-factory", "version": "1.0.0"},
            },
        )
    if method == "ping":
        return _result(request_id, {})
    if method == "logging/setLevel":
        return None
    if method == "roots/list":
        return _result(request_id, {"roots": []})
    if method == "prompts/list":
        return _result(request_id, {"prompts": []})
    if method == "prompts/get":
        return _error(request_id, -32602, "Unknown prompt")
    if method == "resources/list":
        return _result(request_id, {"resources": []})
    if method == "resources/templates/list":
        return _result(request_id, {"resourceTemplates": []})
    if method == "resources/read":
        return _error(request_id, -32602, "Unknown resource")
    if method == "completion/complete":
        return _result(request_id, {"completion": {"values": [], "total": 0, "hasMore": False}})
    if method == "tools/list":
        return _result(request_id, tools_list())
    if method == "tools/call":
        try:
            return _result(request_id, tools_call(params))
        except ValueError as exc:
            return _error(request_id, -32602, str(exc))
    return _error(request_id, -32601, f"Method not found: {method}")


def _read_message(stream) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        decoded = line.decode("utf-8").strip()
        if ":" not in decoded:
            continue
        key, value = decoded.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    payload = stream.read(length)
    if not payload:
        return None
    return json.loads(payload.decode("utf-8"))


def _write_message(stream, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
    stream.write(body)
    stream.flush()


def main() -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        try:
            request = _read_message(stdin)
            if request is None:
                break
            response = handle_request(request)
        except Exception as exc:
            response = _error(None, -32700, f"Parse error: {exc}")
        if response is None:
            continue
        _write_message(stdout, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
