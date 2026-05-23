from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
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

    def test_legacy_hosts_frontmatter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "global" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: demo\n"
                "description: Demo skill.\n"
                "capability_class: workflow\n"
                "hosts: [\"claude\"]\n"
                "---\n"
                "# Demo\n"
            )
            original_root = omni_factory.ROOT
            omni_factory.ROOT = root
            try:
                errors, warnings = omni_factory.validate_skill_frontmatter()
            finally:
                omni_factory.ROOT = original_root

        self.assertTrue(any("legacy 'hosts'" in error for error in errors))
        self.assertEqual(warnings, [])

    def test_empty_governed_projects_warns_with_bootstrap_nudge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects.json"
            projects.write_text(json.dumps({"version": 1, "governed_projects": []}) + "\n")
            original_path = omni_factory.PROJECTS_CATALOG_PATH
            omni_factory.PROJECTS_CATALOG_PATH = projects
            try:
                errors, warnings = omni_factory.validate_projects_catalog()
            finally:
                omni_factory.PROJECTS_CATALOG_PATH = original_path

        self.assertEqual(errors, [])
        self.assertTrue(any("governed_projects is empty" in warning for warning in warnings))
        self.assertTrue(any("bootstrap-project.sh --name" in warning for warning in warnings))

    def test_stale_plan_and_memory_pointers_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans = root / "docs" / "plans"
            plans.mkdir(parents=True)
            (plans / "old.md").write_text(
                "---\n"
                "status: in-progress\n"
                "last_updated: 2026-05-01T00:00:00Z\n"
                "---\n"
            )
            (root / "MEMORY.md").write_text(
                "<!-- section:active_tasks -->\n"
                "<!-- entries:start -->\n"
                "- Plan: docs/plans/missing.md - stale pointer\n"
                "<!-- entries:end -->\n"
            )
            original_root = omni_factory.ROOT
            omni_factory.ROOT = root
            try:
                errors, warnings = omni_factory.validate_plan_hygiene(
                    now=datetime(2026, 5, 23, tzinfo=timezone.utc)
                )
            finally:
                omni_factory.ROOT = original_root

        self.assertEqual(errors, [])
        self.assertTrue(any("stale plan file" in warning for warning in warnings))
        self.assertTrue(any("stale MEMORY.md active_tasks pointer" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
