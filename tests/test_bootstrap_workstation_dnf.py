from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


BASH = shutil.which("bash") or "/bin/bash"


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap-workstation.sh"


class BootstrapWorkstationDnfTests(unittest.TestCase):
    """Static/structural coverage for the Red Hat family (dnf/yum) bootstrap path.

    No real RHEL host is available, so these assert on the script body plus one
    live subshell test of the os-release-independent DNF_BIN resolution logic.
    Runtime proof (EPEL providing ripgrep/jq, nodejs:20 AppStream, NodeSource
    rpm behind a proxy, npm -g on the dnf prefix) is host-gated; see
    docs/TECH_DEBT.md "RHEL-family runtime proof on a real host".
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.body = SCRIPT.read_text(encoding="utf-8")

    def test_script_parses(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_detect_platform_recognizes_redhat_ids(self) -> None:
        for token in ("rhel", "fedora", "centos", "rocky", "almalinux"):
            self.assertIn(token, self.body, f"detect_platform missing RH id: {token}")
        self.assertIn("*rhel*", self.body)
        self.assertIn("*fedora*", self.body)

    def test_sets_dnf_package_mode(self) -> None:
        self.assertIn('PACKAGE_MODE="dnf"', self.body)

    def test_dnf_bin_resolution_prefers_dnf_over_yum(self) -> None:
        self.assertIn('DNF_BIN="dnf"', self.body)
        self.assertIn('DNF_BIN="yum"', self.body)
        self.assertLess(
            self.body.index('DNF_BIN="dnf"'),
            self.body.index('DNF_BIN="yum"'),
            "dnf must be preferred over yum",
        )

    def test_defines_dnf_helpers(self) -> None:
        for fn in (
            "dnf_install()",
            "ensure_epel_if_needed()",
            "ensure_base_dependencies_dnf()",
            "ensure_node_dnf()",
        ):
            self.assertIn(fn, self.body, f"missing dnf helper: {fn}")

    def test_base_deps_dnf_includes_required_packages(self) -> None:
        for pkg in ("git", "curl", "jq", "ripgrep", "zip", "unzip", "tar", "gcc", "make"):
            self.assertIn(pkg, self.body)
        self.assertTrue(
            "Development Tools" in self.body or "@development" in self.body,
            "dnf base deps should pull a development toolchain group",
        )

    def test_epel_guarded_to_non_fedora(self) -> None:
        # epel-release legitimately appears twice: the `rpm -q epel-release`
        # idempotency guard and the `dnf_install epel-release` install.
        epel_block_start = self.body.index("ensure_epel_if_needed()")
        fedora_return = self.body.index('"${OS_ID}" == "fedora"', epel_block_start)
        epel_install = self.body.index("dnf_install epel-release", epel_block_start)
        rpm_guard = self.body.index("rpm -q epel-release", epel_block_start)
        self.assertLess(
            fedora_return, epel_install, "fedora early-return must precede epel-release install"
        )
        self.assertLess(
            rpm_guard, epel_install, "rpm -q idempotency guard must precede epel-release install"
        )

    def test_node_dnf_prefers_appstream_then_consent_gated_nodesource(self) -> None:
        self.assertIn("dnf module reset", self.body)
        self.assertIn("dnf module enable -y nodejs:20", self.body)
        self.assertIn("FORCE_NODE_EXTERNAL", self.body)
        self.assertIn("yes_no_prompt", self.body)
        self.assertIn("rpm.nodesource.com/setup_lts.x", self.body)

    def test_nodesource_preserves_proxy_env(self) -> None:
        # The rpm NodeSource pipe must keep `sudo -E` so proxy/CA env survives.
        self.assertIn("https://rpm.nodesource.com/setup_lts.x | sudo -E bash -", self.body)

    def test_ensure_sudo_covers_dnf(self) -> None:
        sudo_start = self.body.index("ensure_sudo()")
        sudo_block = self.body[sudo_start : sudo_start + 250]
        self.assertIn('"${PACKAGE_MODE}" == "dnf"', sudo_block)

    def test_main_dispatch_has_dnf_arm(self) -> None:
        self.assertIn('elif [[ "${PACKAGE_MODE}" == "dnf" ]]', self.body)
        self.assertIn("ensure_base_dependencies_dnf", self.body)
        self.assertIn("ensure_node_dnf", self.body)

    def test_no_homebrew_command(self) -> None:
        # The word "Homebrew" appears only in the not-supported message; never a brew command.
        self.assertNotIn("brew install", self.body)
        self.assertNotIn("brew tap", self.body)

    def test_apt_and_macports_paths_unchanged(self) -> None:
        self.assertIn("port install nodejs20", self.body)
        self.assertIn("https://deb.nodesource.com/setup_lts.x", self.body)
        self.assertIn("ensure_base_dependencies_macports", self.body)

    def test_dnf_bin_resolution_logic_in_subshell(self) -> None:
        """Prove prefer-dnf / fallback-yum / error without a real host.

        Replicates the resolution block verbatim and runs it against a fake
        PATH containing dnf only, yum only, or neither.
        """
        snippet = (
            'if command -v dnf >/dev/null 2>&1; then DNF_BIN="dnf"; '
            'elif command -v yum >/dev/null 2>&1; then DNF_BIN="yum"; '
            'else echo "none" >&2; exit 1; fi; echo "$DNF_BIN"'
        )

        def run_with_fakes(*names: str) -> subprocess.CompletedProcess[str]:
            with tempfile.TemporaryDirectory() as tmp:
                for n in names:
                    fake = Path(tmp) / n
                    fake.write_text("#!/usr/bin/env bash\nexit 0\n")
                    fake.chmod(0o755)
                return subprocess.run(
                    [BASH, "-c", snippet],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={"PATH": tmp},
                )

        both = run_with_fakes("dnf", "yum")
        self.assertEqual(both.returncode, 0)
        self.assertEqual(both.stdout.strip(), "dnf")

        yum_only = run_with_fakes("yum")
        self.assertEqual(yum_only.returncode, 0)
        self.assertEqual(yum_only.stdout.strip(), "yum")

        neither = run_with_fakes()
        self.assertNotEqual(neither.returncode, 0)


if __name__ == "__main__":
    unittest.main()
