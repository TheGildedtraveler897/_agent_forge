from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cursor = load_module("continuity_cursor_for_tests", ROOT / "scripts" / "continuity_cursor.py")


def run_silently(func, *args) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return func(*args)


class ContinuityCursorTests(unittest.TestCase):
    def test_cursor_lifecycle_records_tiny_resume_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = project / "docs" / "plans" / "demo.md"
            artifact = project / "runtime" / "validation" / "triad" / "demo" / "summary.json"
            plan.parent.mkdir(parents=True)
            artifact.parent.mkdir(parents=True)
            plan.write_text("# Demo Plan\n")
            artifact.write_text('{"pass": true}\n')

            run_silently(
                cursor.cmd_start,
                Namespace(root=str(project), slug="demo", plan=str(plan), task="T-01", next_action="write RED test"),
            )
            run_silently(
                cursor.cmd_advance,
                Namespace(
                    root=str(project),
                    slug="demo",
                    task="T-01",
                    status="done",
                    note="RED/GREEN complete",
                    next_action="run verifier",
                )
            )
            run_silently(
                cursor.cmd_verify,
                Namespace(
                    root=str(project),
                    slug="demo",
                    cmd="python3 scripts/verify-agent-forge.py",
                    exit_code=0,
                    artifact=str(artifact),
                )
            )

            state = json.loads((project / "dev" / "active" / "demo" / "cursor.json").read_text())
            self.assertEqual(state["slug"], "demo")
            self.assertEqual(state["plan"], "docs/plans/demo.md")
            self.assertEqual(state["current_task"], "T-01")
            self.assertEqual(state["last_completed_task"], "T-01")
            self.assertEqual(state["task_status"]["T-01"], "done")
            self.assertEqual(state["last_verification"]["exit_code"], 0)
            self.assertEqual(state["last_verification"]["artifact"], "runtime/validation/triad/demo/summary.json")
            self.assertEqual(state["next_action"], "run verifier")
            self.assertLess(len(json.dumps(state, separators=(",", ":"))), 2048)

    def test_host_local_plan_without_cursor_is_not_a_resume_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            host_plan = project / ".claude" / "plans" / "saved.md"
            host_plan.parent.mkdir(parents=True)
            host_plan.write_text("# Host-local plan\n")

            with self.assertRaises(FileNotFoundError):
                cursor.load_cursor(project, "saved")

    def test_checkpoint_records_precise_resume_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            plan = project / "docs" / "plans" / "demo.md"
            target = project / "scripts" / "thing.py"
            plan.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            plan.write_text("# Demo Plan\n")
            target.write_text("print('demo')\n")

            run_silently(
                cursor.cmd_start,
                Namespace(root=str(project), slug="demo", plan=str(plan), task="T-03", next_action="resume work"),
            )
            run_silently(
                cursor.cmd_checkpoint,
                Namespace(
                    root=str(project),
                    slug="demo",
                    file=str(target),
                    line_range="1,4",
                    test_name="test_demo",
                    exit_code=1,
                ),
            )

            state = json.loads((project / "dev" / "active" / "demo" / "cursor.json").read_text())
            self.assertEqual(state["task_checkpoint"]["task"], "T-03")
            self.assertEqual(state["task_checkpoint"]["file"], "scripts/thing.py")
            self.assertEqual(state["task_checkpoint"]["line_range"], {"start": 1, "end": 4})
            self.assertEqual(state["task_checkpoint"]["test_name"], "test_demo")
            self.assertEqual(state["task_checkpoint"]["exit_code"], 1)

    def test_task_complete_records_short_commit_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            subprocess.run(["git", "init"], cwd=project, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=project, check=True)
            (project / "README.md").write_text("demo\n")
            subprocess.run(["git", "add", "README.md"], cwd=project, check=True)
            subprocess.run(["git", "commit", "-m", "demo"], cwd=project, check=True, stdout=subprocess.DEVNULL)

            plan = project / "docs" / "plans" / "demo.md"
            plan.parent.mkdir(parents=True)
            plan.write_text("# Demo Plan\n")
            run_silently(
                cursor.cmd_start,
                Namespace(root=str(project), slug="demo", plan=str(plan), task="T-01", next_action="finish"),
            )
            run_silently(cursor.cmd_task_complete, Namespace(root=str(project), slug="demo", task="T-01"))

            state = json.loads((project / "dev" / "active" / "demo" / "cursor.json").read_text())
            expected = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=project, text=True).strip()
            self.assertEqual(state["T-01_commit"], expected)
            self.assertEqual(state["task_status"]["T-01"], "done")
            self.assertEqual(state["last_completed_task"], "T-01")


if __name__ == "__main__":
    unittest.main()
