from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSTATION = ROOT / "scripts" / "bootstrap-workstation.sh"
DEPLOY = ROOT / "scripts" / "deploy-and-bootstrap.sh"


class AutoProvisionBashTests(unittest.TestCase):
    """Static/structural coverage for the opt-in --auto-provision bash path.

    Real package installs are host-gated; these assert the wiring and that the
    --base-deps-only short-circuit precedes the interactive service menu.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.ws = WORKSTATION.read_text(encoding="utf-8")
        cls.dep = DEPLOY.read_text(encoding="utf-8")

    def _parses(self, path: Path) -> None:
        r = subprocess.run(["bash", "-n", str(path)], check=False, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_scripts_parse(self) -> None:
        self._parses(WORKSTATION)
        self._parses(DEPLOY)

    def test_workstation_has_base_deps_only_flag(self) -> None:
        self.assertIn('BASE_DEPS_ONLY="0"', self.ws)
        self.assertIn("--base-deps-only)", self.ws)
        self.assertIn('BASE_DEPS_ONLY="1"', self.ws)

    def test_base_deps_only_short_circuits_before_service_menu(self) -> None:
        guard = self.ws.index('if [[ "${BASE_DEPS_ONLY}" == "1" ]]')
        menu = self.ws.index("choose_services\n")
        # The early-exit guard must come before the interactive choose_services call.
        self.assertLess(guard, menu)
        # And the guard block exits.
        block = self.ws[guard:menu]
        self.assertIn("exit 0", block)

    def test_python3_in_base_dep_lists(self) -> None:
        # apt and dnf base-dep installs must include python3 so --auto-provision
        # ensures Python on *nix too.
        apt = self.ws.index("ensure_base_dependencies_apt()")
        apt_line = self.ws[apt:self.ws.index("}", apt)]
        self.assertIn("python3", apt_line)
        dnf = self.ws.index("ensure_base_dependencies_dnf()")
        dnf_line = self.ws[dnf:self.ws.index("ensure_node_dnf", dnf)]
        self.assertIn("python3", dnf_line)
        # macOS only provisions python if none exists (don't disturb an existing one).
        self.assertIn("command -v python3", self.ws)
        self.assertIn("port install python312", self.ws)

    def test_deploy_has_auto_provision_flag(self) -> None:
        self.assertIn('AUTO_PROVISION="0"', self.dep)
        self.assertIn("--auto-provision)", self.dep)
        self.assertIn('AUTO_PROVISION="1"', self.dep)

    def test_auto_provision_runs_base_deps_only_before_deploy(self) -> None:
        prov = self.dep.index("--base-deps-only")
        deploy_call = self.dep.index("scripts/deploy-factory.sh")
        # Provisioning must run before the deploy-factory sync (which needs python3).
        self.assertLess(prov, deploy_call)
        self.assertIn("bootstrap-workstation.sh", self.dep[prov - 200:prov + 50])


if __name__ == "__main__":
    unittest.main()
