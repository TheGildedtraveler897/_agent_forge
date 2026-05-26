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

    def test_psutil_shared_helper_enforces_python_floor_and_link_fallback(self) -> None:
        body = self.script("_psutil.ps1")

        self.assertIn("function Resolve-Python", body)
        self.assertIn("MinMinor = 10", body)
        self.assertIn(r"Python\s+(\d+)\.(\d+)", body)
        self.assertIn("not found on PATH", body)
        self.assertIn("function Get-RelativePath", body)
        self.assertIn("MakeRelativeUri", body)
        self.assertIn("function New-ManagedLink", body)
        self.assertIn("New-Item -ItemType SymbolicLink", body)
        self.assertIn("Developer Mode", body)
        self.assertIn("Managed by Agent Forge", body)
        self.assertIn("function Test-Command", body)

    def test_entry_scripts_dot_source_shared_helper_not_local_resolver(self) -> None:
        for name in ("bootstrap-project.ps1", "deploy-factory.ps1"):
            with self.subTest(script=name):
                body = self.script(name)
                self.assertIn("_psutil.ps1", body)
                self.assertIn("Resolve-Python", body)
                self.assertNotIn("function Resolve-PythonCommand", body)
                self.assertIn("$pythonExe @pythonArgs", body)

    def test_bootstrap_project_has_full_parity_constructs(self) -> None:
        body = self.script("bootstrap-project.ps1")

        # interactive CONOPS
        self.assertIn("Invoke-ProjectDefinition", body)
        self.assertIn('Read-Host "Project mission', body)
        self.assertIn("[switch]$Define", body)
        self.assertIn("[switch]$NoDefine", body)
        self.assertIn("IsInputRedirected", body)
        # existing mode
        self.assertIn("[switch]$Existing", body)
        self.assertIn("Existing mode requested but target does not exist", body)
        # local skills
        self.assertIn("[switch]$WithLocalSkills", body)
        self.assertIn(r"skills\projects", body)
        # relpath fix + managed link (the wrong hardcoded import must be gone)
        self.assertIn("New-ManagedLink", body)
        self.assertNotIn("@../CLAUDE.md", body)
        # Codex override stub parity
        self.assertIn("AGENTS.override.md", body)

    def test_deploy_and_bootstrap_forwards_all_home_flags(self) -> None:
        body = self.script("deploy-and-bootstrap.ps1")

        self.assertIn("$ClaudeHome", body)
        self.assertIn("$CodexHome", body)
        self.assertIn("$GeminiHome", body)
        self.assertIn("-GeminiHome", body)

    def test_bootstrap_workstation_installs_clis_and_enforces_floors(self) -> None:
        body = self.script("bootstrap-workstation.ps1")

        self.assertIn("@anthropic-ai/claude-code", body)
        self.assertIn("@openai/codex", body)
        self.assertIn("@google/gemini-cli", body)
        self.assertIn("npm install -g", body)
        self.assertIn("Read-ServiceSelection", body)
        self.assertIn("Install-NpmGlobal", body)
        self.assertIn("Resolve-Python", body)
        self.assertIn("NODE_USE_SYSTEM_CA", body)
        self.assertIn("GOOGLE_CLOUD_PROJECT", body)
        self.assertIn(r"runtime\machine-setup", body)

    def test_projects_json_registration_parity_between_sh_and_ps1(self) -> None:
        ps1 = self.script("bootstrap-project.ps1")
        sh = (ROOT / "scripts" / "bootstrap-project.sh").read_text(encoding="utf-8")
        for body in (ps1, sh):
            self.assertIn("governed_projects", body)
            self.assertIn("required_files", body)
            self.assertIn("docs/CONOPS.md", body)
            self.assertIn(".claude/CLAUDE.md", body)


if __name__ == "__main__":
    unittest.main()
