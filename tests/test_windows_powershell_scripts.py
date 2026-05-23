from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_SCRIPTS = [
    ROOT / "scripts" / "deploy-factory.ps1",
    ROOT / "scripts" / "bootstrap-project.ps1",
]


class WindowsPowerShellScriptTests(unittest.TestCase):
    def test_python_invocation_does_not_use_descending_empty_arg_range(self) -> None:
        for script in WINDOWS_SCRIPTS:
            with self.subTest(script=script.name):
                body = script.read_text(encoding="utf-8")

                self.assertNotIn("$python[1..($python.Length - 1)]", body)
                self.assertIn("$pythonArgs", body)

    def test_deploy_next_step_supports_stock_windows_powershell(self) -> None:
        body = (ROOT / "scripts" / "deploy-factory.ps1").read_text(encoding="utf-8")

        self.assertIn("powershell.exe -ExecutionPolicy Bypass -File", body)


if __name__ == "__main__":
    unittest.main()
