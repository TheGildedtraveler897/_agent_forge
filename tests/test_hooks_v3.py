from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omni_factory", ROOT / "scripts" / "omni_factory.py")
assert SPEC and SPEC.loader
omni_factory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = omni_factory
SPEC.loader.exec_module(omni_factory)


class HookV3RenderingTests(unittest.TestCase):
    def test_codex_pre_tool_use_renders_pascal_case(self) -> None:
        payload = omni_factory.codex_hook_payload()

        self.assertIn("PreToolUse", payload["hooks"])
        self.assertNotIn("pre_tool_use", payload["hooks"])

    def test_legacy_v2_command_record_normalizes_to_v3_handler(self) -> None:
        record = {
            "id": "legacy-command",
            "event": "pre_tool_use",
            "command": "bash ~/Projects/_agent_forge/skills/global/telemetry-guardian/guardian.sh",
            "targets": ["claude"],
        }

        normalized = omni_factory.normalize_hook_record(record, "shared")

        self.assertEqual(normalized["handler"]["type"], "command")
        self.assertEqual(normalized["handler"]["command"], record["command"])
        self.assertTrue(normalized["enabled"])

    def test_high_risk_event_aliases_are_curated(self) -> None:
        self.assertEqual(omni_factory.native_hook_event("claude", "pre_tool_use"), "PreToolUse")
        self.assertEqual(omni_factory.native_hook_event("codex", "pre_tool_use"), "PreToolUse")
        self.assertEqual(omni_factory.native_hook_event("gemini", "pre_tool_use"), "BeforeTool")
        self.assertEqual(omni_factory.native_hook_event("gemini", "stop"), "SessionEnd")

    def test_user_prompt_submit_renders_for_claude_and_codex(self) -> None:
        claude_payload = omni_factory.claude_hook_payload()
        codex_payload = omni_factory.codex_hook_payload()

        self.assertIn("UserPromptSubmit", claude_payload)
        self.assertIn("UserPromptSubmit", codex_payload["hooks"])

        def _has_auto_activator(entries: list) -> bool:
            for entry in entries:
                serialized = repr(entry)
                if "prompt-auto-activator" in serialized or "auto-activator.sh" in serialized:
                    return True
            return False

        self.assertTrue(_has_auto_activator(claude_payload["UserPromptSubmit"]))
        self.assertTrue(_has_auto_activator(codex_payload["hooks"]["UserPromptSubmit"]))

    def test_user_prompt_submit_filtered_from_gemini(self) -> None:
        gemini_payload = omni_factory.gemini_hook_payload()
        serialized = repr(gemini_payload)

        self.assertNotIn("prompt-auto-activator", serialized)
        self.assertNotIn("auto-activator.sh", serialized)
        self.assertNotIn("UserPromptSubmit", serialized)


if __name__ == "__main__":
    unittest.main()
