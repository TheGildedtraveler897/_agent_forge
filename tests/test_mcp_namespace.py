from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


omni_factory = load_module("omni_factory_for_mcp_namespace_tests", ROOT / "scripts" / "omni_factory.py")


class MCPNamespaceTests(unittest.TestCase):
    def with_catalog(self, tmp: str, mcp_payload: dict, projects_payload: dict) -> None:
        self.tmp_root = Path(tmp)
        self.mcp_path = self.tmp_root / "global-mcp.json"
        self.projects_path = self.tmp_root / "projects.json"
        self.mcp_path.write_text(json.dumps(mcp_payload, indent=2) + "\n")
        self.projects_path.write_text(json.dumps(projects_payload, indent=2) + "\n")

        self.original_mcp_path = omni_factory.GLOBAL_MCP_PATH
        self.original_projects_path = omni_factory.PROJECTS_CATALOG_PATH
        self.original_projects_root = omni_factory.PROJECTS_ROOT
        omni_factory.GLOBAL_MCP_PATH = self.mcp_path
        omni_factory.PROJECTS_CATALOG_PATH = self.projects_path
        omni_factory.PROJECTS_ROOT = self.tmp_root

    def restore_catalog(self) -> None:
        omni_factory.GLOBAL_MCP_PATH = self.original_mcp_path
        omni_factory.PROJECTS_CATALOG_PATH = self.original_projects_path
        omni_factory.PROJECTS_ROOT = self.original_projects_root

    def base_projects(self) -> dict:
        return {
            "version": 1,
            "governed_projects": [
                {"name": "trusted-app", "root": "trusted-app", "trusted_workspace": True, "required_files": []},
                {"name": "unsafe", "root": "unsafe", "trusted_workspace": False, "required_files": []},
            ],
        }

    def forge_factory_payload(self) -> dict:
        return {
            "version": 2,
            "defaults": {
                "startup_timeout_ms": 20000,
                "tool_timeout_ms": 60000,
                "required": False,
                "trust_server": False,
                "parallel_safe": False,
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
                        "args": ["-c", "exec python3 \"$HOME/Projects/_agent_forge/scripts/mcp/forge_factory_server.py\""],
                    },
                    "auth": "none",
                    "trust": "local",
                    "tool_filter": ["read_handoff"],
                    "env_passthrough": [],
                    "env_literal": {},
                    "headers": {},
                }
            },
        }

    def test_mcp_v2_normalizes_prefix_to_host_safe_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.with_catalog(tmp, self.forge_factory_payload(), self.base_projects())
            try:
                server = omni_factory.load_mcp_servers()[0]
            finally:
                self.restore_catalog()

        self.assertEqual(server["prefix"], "forge.factory")
        self.assertEqual(server["server_alias"], "forge-factory")
        self.assertEqual(server["tool_filter"], ["read_handoff"])

    def test_mcp_renderers_use_alias_and_tool_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.with_catalog(tmp, self.forge_factory_payload(), self.base_projects())
            try:
                claude = json.loads(omni_factory.render_claude_project_mcp("trusted-app"))
                gemini = json.loads(omni_factory.render_gemini_settings("trusted-app"))
                codex = omni_factory.render_codex_config("trusted-app", Path(tmp) / "trusted-app", [])
            finally:
                self.restore_catalog()

        self.assertIn("forge-factory", claude["mcpServers"])
        self.assertNotIn("forge.factory", claude["mcpServers"])
        self.assertEqual(gemini["mcpServers"]["forge-factory"]["includeTools"], ["read_handoff"])
        self.assertIn("[mcp_servers.forge-factory]", codex)
        self.assertIn('enabled_tools = ["read_handoff"]', codex)

    def test_remote_project_server_requires_trusted_workspace(self) -> None:
        payload = self.forge_factory_payload()
        payload["servers"] = {
            "remote-audit": {
                "prefix": "forge.audit",
                "scope": "project",
                "projects": ["unsafe", "trusted-app"],
                "targets": ["claude", "codex", "gemini"],
                "transport": {"type": "streamable_http", "url": "https://example.invalid/mcp"},
                "auth": "bearer",
                "trust": "remote-trusted",
                "tool_filter": ["read_report"],
                "env_passthrough": ["AUDIT_TOKEN"],
                "env_optional": ["AUDIT_TOKEN"],
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            self.with_catalog(tmp, payload, self.base_projects())
            try:
                unsafe = omni_factory.project_mcp_servers("unsafe")
                trusted = omni_factory.project_mcp_servers("trusted-app")
            finally:
                self.restore_catalog()

        self.assertEqual(unsafe, [])
        self.assertEqual(len(trusted), 1)
        self.assertEqual(trusted[0]["server_alias"], "forge-audit")

    def test_duplicate_mcp_prefix_is_a_verifier_error(self) -> None:
        payload = self.forge_factory_payload()
        payload["servers"]["forge-factory-copy"] = dict(payload["servers"]["forge-factory"])
        with tempfile.TemporaryDirectory() as tmp:
            self.with_catalog(tmp, payload, self.base_projects())
            try:
                errors, _warnings = omni_factory.validate_mcp_inventory()
            finally:
                self.restore_catalog()

        self.assertTrue(any("duplicate prefix 'forge.factory'" in error for error in errors))

    def test_forge_factory_server_lists_read_handoff(self) -> None:
        server = load_module("forge_factory_server_for_tests", ROOT / "scripts" / "mcp" / "forge_factory_server.py")

        response = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

        self.assertEqual(response["id"], 1)
        tools = response["result"]["tools"]
        self.assertEqual(tools[0]["name"], "read_handoff")
        self.assertIn("HANDOFF.md", tools[0]["description"])

    def test_forge_factory_server_handles_ping_and_client_protocol_version(self) -> None:
        server = load_module("forge_factory_server_for_tests_ping", ROOT / "scripts" / "mcp" / "forge_factory_server.py")

        init = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-03-26"},
            }
        )
        ping = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "ping"})

        self.assertEqual(init["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual(ping["result"], {})

    def test_validator_mcp_surface_passes_for_seeded_claude_config(self) -> None:
        validator = load_module("triad_validator_for_mcp_tests", ROOT / "scripts" / "validate-triad-runtime.py")
        with tempfile.TemporaryDirectory() as tmp:
            self.with_catalog(tmp, self.forge_factory_payload(), self.base_projects())
            try:
                validator.PROJECTS_CATALOG_PATH = self.projects_path
                validator.PROJECTS_ROOT = self.tmp_root
                validator.omni_factory.GLOBAL_MCP_PATH = self.mcp_path
                validator.omni_factory.PROJECTS_CATALOG_PATH = self.projects_path
                validator.omni_factory.PROJECTS_ROOT = self.tmp_root
                project = Path(tmp) / "trusted-app"
                (project / ".claude").mkdir(parents=True)
                payload = omni_factory.render_claude_project_mcp("trusted-app")
                assert payload is not None
                (project / ".mcp.json").write_text(payload)
                result = validator.mcp_surface_for("claude", project)
            finally:
                self.restore_catalog()

        self.assertTrue(result["pass"])
        self.assertEqual(result["server_alias"], "forge-factory")
        self.assertIn("read_handoff", result["listed_tools"])


if __name__ == "__main__":
    unittest.main()
