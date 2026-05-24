from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omni_factory_current_host_tests", ROOT / "scripts" / "omni_factory.py")
assert SPEC and SPEC.loader
omni_factory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = omni_factory
SPEC.loader.exec_module(omni_factory)


class CurrentHostRendererTests(unittest.TestCase):
    def test_codex_config_uses_current_hooks_feature_flag(self) -> None:
        rendered = omni_factory.render_codex_config("_agent_forge", ROOT, [])

        self.assertIn("[features]\nhooks = true", rendered)
        self.assertNotIn("codex_hooks", rendered)

    def test_codex_hook_aliases_cover_current_lifecycle_events(self) -> None:
        self.assertEqual(omni_factory.native_hook_event("codex", "subagent_start"), "SubagentStart")
        self.assertEqual(omni_factory.native_hook_event("codex", "subagent_stop"), "SubagentStop")
        self.assertEqual(omni_factory.native_hook_event("codex", "pre_compact"), "PreCompact")
        self.assertEqual(omni_factory.native_hook_event("codex", "post_compact"), "PostCompact")

    def test_codex_mcp_env_passthrough_renders_env_vars(self) -> None:
        payload = {
            "version": 2,
            "servers": {
                "env-test": {
                    "prefix": "env.test",
                    "description": "Environment passthrough test server.",
                    "scope": "shared",
                    "projects": ["app"],
                    "targets": ["codex"],
                    "transport": {"type": "stdio", "command": "env-test"},
                    "auth": "none",
                    "trust": "local",
                    "env_passthrough": ["AGENT_FORGE_TOKEN"],
                    "env_literal": {"STATIC_FLAG": "1"},
                }
            },
        }
        projects = {
            "version": 1,
            "governed_projects": [
                {"name": "app", "root": "app", "trusted_workspace": True, "required_files": []}
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            mcp_path = tmp_root / "global-mcp.json"
            projects_path = tmp_root / "projects.json"
            mcp_path.write_text(json.dumps(payload) + "\n")
            projects_path.write_text(json.dumps(projects) + "\n")
            original_mcp_path = omni_factory.GLOBAL_MCP_PATH
            original_projects_path = omni_factory.PROJECTS_CATALOG_PATH
            original_projects_root = omni_factory.PROJECTS_ROOT
            omni_factory.GLOBAL_MCP_PATH = mcp_path
            omni_factory.PROJECTS_CATALOG_PATH = projects_path
            omni_factory.PROJECTS_ROOT = tmp_root
            try:
                rendered = omni_factory.render_codex_config("app", tmp_root / "app", [])
            finally:
                omni_factory.GLOBAL_MCP_PATH = original_mcp_path
                omni_factory.PROJECTS_CATALOG_PATH = original_projects_path
                omni_factory.PROJECTS_ROOT = original_projects_root

        self.assertIn("env_vars = [\"AGENT_FORGE_TOKEN\"]", rendered)
        self.assertIn("[mcp_servers.env-test.env]", rendered)
        self.assertIn("STATIC_FLAG = \"1\"", rendered)
        self.assertNotIn("AGENT_FORGE_TOKEN = \"$AGENT_FORGE_TOKEN\"", rendered)

    def test_claude_sync_delivers_global_skills_to_native_skill_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_home = Path(tmp) / "claude-home"
            omni_factory.sync_claude(None, ROOT.parent, claude_home)

            self.assertTrue((claude_home / "skills" / "onboarding-guide").is_symlink())
            self.assertTrue((claude_home / "skills" / "onboarding-guide.md").is_file())

    def test_project_gemini_context_deduplicates_imports(self) -> None:
        rendered = omni_factory.render_project_gemini_md(ROOT)
        imports = [line for line in rendered.splitlines() if line.startswith("@")]

        self.assertEqual(len(imports), len(set(imports)))


if __name__ == "__main__":
    unittest.main()
