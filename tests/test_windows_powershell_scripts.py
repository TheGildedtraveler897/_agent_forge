from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WindowsPowerShellScriptTests(unittest.TestCase):
    def script(self, name: str) -> str:
        path = ROOT / "scripts" / name
        self.assertTrue(path.is_file(), f"missing Windows script: {path}")
        return path.read_text(encoding="utf-8")

    def test_python_invocation_does_not_use_descending_empty_arg_range(self) -> None:
        for name in ("deploy-factory.ps1", "bootstrap-project.ps1"):
            with self.subTest(script=name):
                body = self.script(name)

                self.assertNotIn("$python[1..($python.Length - 1)]", body)
                self.assertIn("$pythonExe @pythonArgs", body)

    def test_deploy_factory_unblocks_copied_tree_and_supports_stock_powershell(self) -> None:
        body = self.script("deploy-factory.ps1")

        self.assertIn("Get-ChildItem -LiteralPath $targetFactoryRoot -Recurse", body)
        self.assertIn("Unblock-File", body)
        self.assertIn("powershell.exe -ExecutionPolicy Bypass -File", body)

    def test_deploy_and_bootstrap_unblocks_extracts_checks_and_deploys(self) -> None:
        body = self.script("deploy-and-bootstrap.ps1")

        self.assertIn("[Parameter(Mandatory=$true)][string]$BundleZip", body)
        self.assertIn("Unblock-File -LiteralPath $bundlePath", body)
        self.assertIn("Expand-Archive -LiteralPath $bundlePath", body)
        self.assertIn("Test-BundleIntegrity", body)
        self.assertIn("AGENTS.md", body)
        self.assertIn("docs", body)
        self.assertIn("policies", body)
        self.assertIn("Get-ChildItem -LiteralPath $factoryRoot -Recurse", body)
        self.assertIn("deploy-factory.ps1", body)
        self.assertIn("-ClaudeOnly", body)
        self.assertIn("-AllHosts", body)
        self.assertIn("MAX_PATH", body)
        self.assertIn("/onboarding-guide", body)

    def test_bootstrap_workstation_windows_has_detection_and_winget_fallbacks(self) -> None:
        body = self.script("bootstrap-workstation.ps1")

        self.assertIn("winget", body)
        self.assertIn("Python.Python.3", body)
        self.assertIn("Git.Git", body)
        self.assertIn("OpenJS.NodeJS.LTS", body)
        self.assertIn("WSL2", body)
        self.assertIn("python.org", body)
        self.assertIn("git-scm.com", body)
        self.assertIn("nodejs.org", body)


if __name__ == "__main__":
    unittest.main()
