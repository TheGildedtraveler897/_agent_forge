from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "enforce-branch-discipline.sh"


class BranchDisciplineTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT), *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_blocks_primary_branch_by_default(self) -> None:
        result = self.run_script("--branch", "master")

        self.assertEqual(result.returncode, 2)
        self.assertIn("integration-only", result.stderr)

    def test_allows_primary_branch_when_explicit(self) -> None:
        result = self.run_script("--branch", "master", "--allow-primary")

        self.assertEqual(result.returncode, 0)
        self.assertIn("branch discipline ok: master", result.stdout)

    def test_allows_feature_branch(self) -> None:
        result = self.run_script("--branch", "feat/gsd-extraction-foundation")

        self.assertEqual(result.returncode, 0)
        self.assertIn("branch discipline ok: feat/gsd-extraction-foundation", result.stdout)


if __name__ == "__main__":
    unittest.main()
