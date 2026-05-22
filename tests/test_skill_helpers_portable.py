"""Smoke tests for the Python implementations of cross-host hook helpers.

Ensures the ports of guardian.sh, auto-activator.sh, and prober.sh are
exercised under the same conditions as the bash originals. Running these
on Linux/macOS/Windows proves the helpers function natively on every
platform Agent Forge ships to.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent.parent / "skills" / "global"
GUARDIAN = SCRIPT_ROOT / "telemetry-guardian" / "guardian.py"
AUTO_ACTIVATOR = SCRIPT_ROOT / "prompt-auto-activator" / "auto-activator.py"
PROBER = SCRIPT_ROOT / "live-hook-prober" / "prober.py"


def _run(script: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=15,
    )


class GuardianPyTests(unittest.TestCase):
    def test_allow_benign_command(self) -> None:
        result = _run(GUARDIAN, stdin=json.dumps({"command": "git status"}))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["verdict"], "allow")

    def test_block_no_verify(self) -> None:
        result = _run(GUARDIAN, stdin=json.dumps({"command": "git commit --no-verify"}))
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["verdict"], "block")
        self.assertIn("--no-verify", payload["matched"])

    def test_block_force_push_to_main(self) -> None:
        result = _run(
            GUARDIAN,
            stdin=json.dumps({"command": "git push --force origin main"}),
        )
        self.assertEqual(result.returncode, 1)

    def test_block_wildcard_home_rm(self) -> None:
        result = _run(GUARDIAN, stdin=json.dumps({"command": "rm -rf $HOME"}))
        self.assertEqual(result.returncode, 1)

    def test_extracts_command_from_nested_tool_input(self) -> None:
        payload = {"tool_input": {"command": "git commit --no-verify"}}
        result = _run(GUARDIAN, stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 1)

    def test_extracts_command_from_raw_stdin_fallback(self) -> None:
        result = _run(GUARDIAN, stdin="not json but contains rm -rf $HOME oops")
        self.assertEqual(result.returncode, 1)


class AutoActivatorPyTests(unittest.TestCase):
    def test_caveman_triggers_token_optimizer(self) -> None:
        result = _run(AUTO_ACTIVATOR, stdin=json.dumps({"prompt": "/caveman please"}))
        self.assertEqual(result.returncode, 0)
        first_line = result.stdout.strip().splitlines()[0]
        payload = json.loads(first_line)
        self.assertEqual(payload["skill"], "token-optimizer")

    def test_terse_mode_triggers_token_optimizer(self) -> None:
        result = _run(AUTO_ACTIVATOR, stdin=json.dumps({"prompt": "use terse mode now"}))
        self.assertEqual(result.returncode, 0)
        self.assertIn("token-optimizer", result.stdout)

    def test_checkpoint_triggers_context_engineer(self) -> None:
        result = _run(AUTO_ACTIVATOR, stdin=json.dumps({"prompt": "/checkpoint please"}))
        self.assertEqual(result.returncode, 0)
        self.assertIn("context-engineer", result.stdout)

    def test_no_trigger_produces_silent_output(self) -> None:
        result = _run(AUTO_ACTIVATOR, stdin=json.dumps({"prompt": "ordinary request"}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_raw_text_input_is_tolerated(self) -> None:
        result = _run(AUTO_ACTIVATOR, stdin="bare /caveman text")
        self.assertEqual(result.returncode, 0)
        self.assertIn("token-optimizer", result.stdout)


class ProberPyTests(unittest.TestCase):
    def test_help_invocation_returns_usage(self) -> None:
        result = _run(PROBER, "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--host", result.stdout)

    def test_missing_required_args_returns_error(self) -> None:
        result = _run(PROBER)
        self.assertNotEqual(result.returncode, 0)

    def test_invalid_host_rejected(self) -> None:
        result = _run(
            PROBER,
            "--host",
            "invalid",
            "--project",
            "/tmp",
            "--command",
            "ls",
            "--expect",
            "allow",
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
