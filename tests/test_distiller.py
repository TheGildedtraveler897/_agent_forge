from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


distiller = _load_module(
    "lesson_distiller",
    ROOT / "skills" / "global" / "lesson-distiller" / "distiller.py",
)
archiver = _load_module(
    "handoff_archiver",
    ROOT / "skills" / "global" / "handoff-archiver" / "archiver.py",
)


SAMPLE_LESSONS = """# Lessons Learned
Last updated: 2026-04-29 (test fixture — 2 entries promoted, 1 active, 0 superseded)

## Rules

- Append-first.

## Entries

### 2026-04-23 - Sample Promoted Lesson

- `Date:` 2026-04-23
- `Context:` Test fixture context.
- `Lesson:` Test fixture lesson.
- `Architectural Decision:` Promote.
- `Evidence:` Tests.
- `Promotion Target:` `AGENTS.md`
- `Status:` promoted (`AGENTS.md` Rules already encode this)

### 2026-04-24 - Sample Bad Promotion

- `Date:` 2026-04-24
- `Context:` Test fixture context.
- `Lesson:` Test fixture lesson.
- `Architectural Decision:` Promote.
- `Evidence:` Tests.
- `Promotion Target:` `docs/NONEXISTENT.md`
- `Status:` promoted (`docs/NONEXISTENT.md` does not exist)

### 2026-04-25 - Sample Active Lesson

- `Date:` 2026-04-25
- `Context:` Active.
- `Lesson:` Active.
- `Architectural Decision:` Active.
- `Evidence:` Tests.
- `Promotion Target:` later
- `Status:` active
"""


SAMPLE_HANDOFF = """# Agent Forge Handoff

Last updated: 2026-04-29 (test fixture)

## What Changed

### Sprint: Recent (2026-04-29, Test)

Latest sprint body line one.
Latest sprint body line two.

### Sprint: Older (2026-04-25, Test)

Older sprint body line one.

### Sprint: Oldest (2026-04-23, Test)

Oldest sprint body line.

## Current State

Operator-state section that must not be archived.

## Final Verdict

Final.
"""


class EntryParsingTests(unittest.TestCase):
    def test_parse_entries_finds_three_blocks(self) -> None:
        _, entries_block = distiller.header_and_entries_split(SAMPLE_LESSONS)
        entries = distiller.parse_entries(entries_block)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["date"], "2026-04-23")
        self.assertEqual(entries[2]["status_value"], "active")

    def test_is_promoted_handles_status_prefix(self) -> None:
        self.assertTrue(distiller.is_promoted("promoted (foo)"))
        self.assertFalse(distiller.is_promoted("active"))
        self.assertFalse(distiller.is_promoted("superseded by 2026-04-24"))


class PromotionVerificationTests(unittest.TestCase):
    def test_resolves_existing_path(self) -> None:
        verification = distiller.verify_promotion_claim({
            "status_value": "promoted (`AGENTS.md` Rules)",
        })
        self.assertTrue(verification["ok"])
        self.assertIn("AGENTS.md", verification["paths_resolved"])

    def test_rejects_nonexistent_path(self) -> None:
        verification = distiller.verify_promotion_claim({
            "status_value": "promoted (`docs/DEFINITELY_NOT_HERE.md` foo)",
        })
        self.assertFalse(verification["ok"])
        self.assertEqual(verification["reason"], "no_paths_resolve")

    def test_rejects_no_paths(self) -> None:
        verification = distiller.verify_promotion_claim({
            "status_value": "promoted (just a code symbol `_FOO_BAR`)",
        })
        self.assertFalse(verification["ok"])
        self.assertEqual(verification["reason"], "no_paths_in_parenthetical")

    def test_skips_non_promoted(self) -> None:
        verification = distiller.verify_promotion_claim({
            "status_value": "active",
        })
        self.assertFalse(verification["ok"])
        self.assertEqual(verification["reason"], "not_promoted")


class IndexLineTests(unittest.TestCase):
    def test_index_line_format(self) -> None:
        line = distiller.build_index_line(
            {"date": "2026-04-23", "title": "Sample"},
            "AGENTS.md",
        )
        self.assertEqual(line, "- 2026-04-23 — Sample → AGENTS.md (archived)")


class HandoffSprintParsingTests(unittest.TestCase):
    def test_what_changed_block_bounded_by_next_top_level(self) -> None:
        start, end = archiver.find_what_changed_block(SAMPLE_HANDOFF)
        block = SAMPLE_HANDOFF[start:end]
        self.assertIn("### Sprint: Recent", block)
        self.assertNotIn("## Current State", block)

    def test_parse_three_sprints(self) -> None:
        start, end = archiver.find_what_changed_block(SAMPLE_HANDOFF)
        sections = archiver.parse_sprint_sections(SAMPLE_HANDOFF[start:end])
        self.assertEqual(len(sections), 3)
        dates = [s["date"] for s in sections]
        self.assertEqual(dates, ["2026-04-29", "2026-04-25", "2026-04-23"])

    def test_summary_table_rows_match_archived(self) -> None:
        sections = [
            {"date": "2026-04-25", "title": "Sprint: Older (2026-04-25, Test)"},
            {"date": "2026-04-23", "title": "Sprint: Oldest (2026-04-23, Test)"},
        ]
        table = archiver.build_summary_table(sections, "docs/archive/SPRINTS.md")
        self.assertIn("| 2026-04-25 |", table)
        self.assertIn("| 2026-04-23 |", table)
        self.assertIn("docs/archive/SPRINTS.md", table)


class IdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="distiller-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_lessons_distillation_dry_run_yields_consistent_count(self) -> None:
        # Real-repo dry-run twice; archived_count must be identical.
        result_a = distiller.distill_lessons(distiller.load_policy(), dry_run=True)
        result_b = distiller.distill_lessons(distiller.load_policy(), dry_run=True)
        self.assertEqual(result_a["archived_count"], result_b["archived_count"])
        self.assertEqual(result_a["delta_bytes"], result_b["delta_bytes"])

    def test_handoff_dry_run_yields_consistent_count(self) -> None:
        result_a = archiver.archive_handoff(archiver.load_policy(), keep=1, dry_run=True)
        result_b = archiver.archive_handoff(archiver.load_policy(), keep=1, dry_run=True)
        self.assertEqual(
            len(result_a.get("archived_sections", []) or []),
            len(result_b.get("archived_sections", []) or []),
        )


class PolicyShapeTests(unittest.TestCase):
    def test_policy_parses_and_has_three_targets(self) -> None:
        policy = json.loads((ROOT / "policies" / "distillation.json").read_text())
        self.assertEqual(policy["version"], 1)
        ids = [t["id"] for t in policy["targets"]]
        self.assertIn("lessons_ledger", ids)
        self.assertIn("handoff_log", ids)
        self.assertIn("triad_runs", ids)


if __name__ == "__main__":
    unittest.main()
