from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omni_factory_symlink_tests", ROOT / "scripts" / "omni_factory.py")
assert SPEC and SPEC.loader
omni_factory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = omni_factory
SPEC.loader.exec_module(omni_factory)


class SymlinkFallbackTests(unittest.TestCase):
    """ensure_symlink / sync_symlink_dir must degrade to a managed copy on native
    Windows where the OS refuses a symlink (WinError 1314). Real Windows behavior
    is host-gated; here we simulate it by forcing os.name='nt' and making
    Path.symlink_to raise OSError. POSIX behavior (real symlinks) is also asserted.
    """

    def _make_source(self, tmp: Path) -> Path:
        source = tmp / "skill-src"
        source.mkdir()
        (source / "SKILL.md").write_text("# demo skill\n")
        return source

    def test_posix_creates_real_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = self._make_source(tmp)
            target = tmp / "out" / "skill"
            omni_factory.ensure_symlink(target, source)
            self.assertTrue(target.is_symlink())
            self.assertEqual(target.resolve(), source.resolve())

    def test_windows_falls_back_to_managed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = self._make_source(tmp)
            target = tmp / "out" / "skill"
            with mock.patch.object(omni_factory.os, "name", "nt"), \
                 mock.patch.object(Path, "symlink_to", side_effect=OSError(1314, "denied")):
                omni_factory.ensure_symlink(target, source)
            self.assertFalse(target.is_symlink())
            self.assertTrue(target.is_dir())
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertEqual((target / "SKILL.md").read_text(), "# demo skill\n")
            self.assertTrue((target / omni_factory.WINDOWS_COPY_MARKER).exists())
            self.assertTrue(omni_factory._is_managed_copy(target))

    def test_windows_copy_fallback_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = self._make_source(tmp)
            target = tmp / "out" / "skill"
            with mock.patch.object(omni_factory.os, "name", "nt"), \
                 mock.patch.object(Path, "symlink_to", side_effect=OSError(1314, "denied")):
                omni_factory.ensure_symlink(target, source)
                # Second call must refresh the managed copy, not raise.
                omni_factory.ensure_symlink(target, source)
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertTrue(omni_factory._is_managed_copy(target))

    def test_non_windows_oserror_is_not_swallowed(self) -> None:
        # On POSIX a symlink OSError is a real failure and must propagate.
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = self._make_source(tmp)
            target = tmp / "out" / "skill"
            with mock.patch.object(omni_factory.os, "name", "posix"), \
                 mock.patch.object(Path, "symlink_to", side_effect=OSError("nope")):
                with self.assertRaises(OSError):
                    omni_factory.ensure_symlink(target, source)

    def test_sync_symlink_dir_prunes_stale_managed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            keep_src = self._make_source(tmp)
            target_dir = tmp / "out"
            with mock.patch.object(omni_factory.os, "name", "nt"), \
                 mock.patch.object(Path, "symlink_to", side_effect=OSError(1314, "denied")):
                # First sync delivers a managed copy named "keep".
                omni_factory.sync_symlink_dir(target_dir, {"keep": keep_src})
                self.assertTrue(omni_factory._is_managed_copy(target_dir / "keep"))
                # Re-sync with an empty desired set must prune the stale copy.
                omni_factory.sync_symlink_dir(target_dir, {})
            self.assertFalse((target_dir / "keep").exists())

    def test_refuses_to_clobber_unmanaged_directory(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            source = self._make_source(tmp)
            target = tmp / "out" / "skill"
            target.mkdir(parents=True)
            (target / "operator-file.txt").write_text("do not delete\n")
            with self.assertRaises(RuntimeError):
                omni_factory.ensure_symlink(target, source)


if __name__ == "__main__":
    unittest.main()
