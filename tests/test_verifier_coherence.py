from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omni_factory_for_verifier_tests", ROOT / "scripts" / "omni_factory.py")
assert SPEC and SPEC.loader
omni_factory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = omni_factory
SPEC.loader.exec_module(omni_factory)


class VerifierCoherenceTests(unittest.TestCase):
    def test_skill_frontmatter_has_required_factory_fields(self) -> None:
        errors, warnings = omni_factory.validate_skill_frontmatter()

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_team_preferred_entries_reference_global_skill_ids(self) -> None:
        capabilities = omni_factory.discover_capabilities()

        self.assertEqual(omni_factory.validate_team_manifest_references(capabilities), [])


if __name__ == "__main__":
    unittest.main()
