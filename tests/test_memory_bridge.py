from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


omni_factory = load_module("omni_factory_for_memory_bridge_tests", ROOT / "scripts" / "omni_factory.py")
bridge = load_module("memory_bridge_for_tests", ROOT / "skills" / "global" / "memory-bridge" / "bridge.py")
archivist = load_module("memory_archivist_for_bridge_tests", ROOT / "skills" / "global" / "memory-archivist" / "archivist.py")


def run_silently(func, *args) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return func(*args)


class MemoryBridgeTests(unittest.TestCase):
    def make_project(self, tmp: str) -> Path:
        project = Path(tmp) / "example-project"
        project.mkdir()
        forge_state = project / ".forge_state"
        forge_state.mkdir()
        (project / "MEMORY.md").write_text(omni_factory.render_memory_md(project))
        (forge_state / "manifest.json").write_text(omni_factory.render_forge_state_manifest(project))
        return project

    def test_outbound_is_idempotent_when_canonical_hash_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(tmp)
            target = bridge.native_target(project, "codex")
            original_utc_now = bridge.utc_now
            try:
                bridge.utc_now = lambda: "2026-04-27T10:00:00Z"
                run_silently(bridge.cmd_outbound, Namespace(project=str(project), host="codex"))
                first_body = target.read_text()

                bridge.utc_now = lambda: "2026-04-27T10:00:05Z"
                run_silently(bridge.cmd_outbound, Namespace(project=str(project), host="codex"))
                second_body = target.read_text()
            finally:
                bridge.utc_now = original_utc_now

            self.assertEqual(first_body, second_body)
            state = json.loads((project / ".forge_state" / "bridge.json").read_text())
            self.assertEqual(state["last_outbound_hash"]["codex"], bridge.sha256_text((project / "MEMORY.md").read_text()))

    def test_inbound_imports_new_host_note_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(tmp)
            target = bridge.native_target(project, "codex")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("- Run python3 -m unittest tests.test_memory_bridge for bridge coverage.\n")

            run_silently(bridge.cmd_inbound, Namespace(project=str(project), host="codex"))
            run_silently(bridge.cmd_inbound, Namespace(project=str(project), host="codex"))

            body = (project / "MEMORY.md").read_text()
            self.assertEqual(body.count("Run python3 -m unittest tests.test_memory_bridge for bridge coverage."), 1)
            self.assertIn("[codex]", body)
            self.assertIn("<!-- section:build_commands -->", body)

    def test_inbound_rejects_credential_shaped_content_and_logs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(tmp)
            target = bridge.native_target(project, "gemini")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("- API_KEY=abc123 should not enter canonical memory.\n")

            run_silently(bridge.cmd_inbound, Namespace(project=str(project), host="gemini"))

            body = (project / "MEMORY.md").read_text()
            self.assertNotIn("API_KEY=abc123", body)
            log_body = (project / ".forge_state" / "bridge.log").read_text()
            self.assertIn("inbound_reject", log_body)
            self.assertIn("gemini", log_body)

    def test_archivist_append_is_source_tagged_and_leaves_no_tmp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(tmp)

            run_silently(
                archivist.cmd_append,
                Namespace(
                    project=str(project),
                    section="project_quirks",
                    entry="Bridge imports are serialized through the archivist writer.",
                    source="claude",
                    replace=False,
                ),
            )

            body = (project / "MEMORY.md").read_text()
            self.assertIn("[claude]", body)
            self.assertIn("Bridge imports are serialized through the archivist writer.", body)
            self.assertEqual(list(project.rglob("*.tmp")), [])

    def test_factory_sync_memory_initializes_bridge_state_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example-project"
            project.mkdir()
            state: dict[str, object] = {}

            omni_factory.sync_memory(project, state)

            bridge_state = json.loads((project / ".forge_state" / "bridge.json").read_text())
            self.assertEqual(bridge_state["version"], 1)
            self.assertEqual(set(bridge_state["native_targets"]), {"claude", "codex", "gemini"})
            self.assertTrue((project / ".forge_state" / "bridge.log").exists())

    def test_validate_confirms_canonical_memory_and_bridge_state_are_accessible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "example-project"
            project.mkdir()
            state: dict[str, object] = {}
            omni_factory.sync_memory(project, state)

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                result = bridge.cmd_validate(Namespace(project=str(project), host="codex"))

            self.assertEqual(result, 0)
            payload = json.loads(buffer.getvalue())
            self.assertTrue(payload["pass"])
            self.assertTrue(payload["canonical_memory_readable"])
            self.assertTrue(payload["bridge_state_accessible"])
            self.assertTrue(payload["bridge_log_accessible"])
            self.assertTrue(payload["target_writable"])

    def test_outbound_appends_active_cursor_state_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.make_project(tmp)
            cursor_dir = project / "dev" / "active" / "demo"
            cursor_dir.mkdir(parents=True)
            (cursor_dir / "cursor.json").write_text(
                json.dumps(
                    {
                        "slug": "demo",
                        "current_task": "T-04",
                        "last_completed_task": "T-03",
                        "next_action": "validate bridge",
                        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )
                + "\n"
            )

            run_silently(bridge.cmd_outbound, Namespace(project=str(project), host="codex"))

            target = bridge.native_target(project, "codex")
            body = target.read_text()
            self.assertIn("Active Cursor State", body)
            self.assertIn("demo", body)
            self.assertIn("T-04", body)


if __name__ == "__main__":
    unittest.main()
