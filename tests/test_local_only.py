"""Synthetic Git lifecycle and removal safety; no business implementation."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


def repository(root):
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Synthetic Test")
    git(root, "config", "user.email", "synthetic@example.invalid")
    (root / "task.txt").write_text("before\n", encoding="utf-8")
    git(root, "add", "task.txt")
    git(root, "commit", "-m", "test: synthetic baseline")


class LocalOnlyTests(unittest.TestCase):
    def test_local_lifecycle_and_task_commit_leave_no_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "cooperation"
            repository(root)
            (root / "docs/project").mkdir(parents=True)  # Pre-existing empty dirs survive.
            exclude = root / ".git/info/exclude"
            initial = exclude.read_bytes() + b"\n# owner rule\n*.owner\n"
            exclude.write_bytes(initial)
            before_dirs = {p.relative_to(root) for p in root.rglob("*") if p.is_dir() and ".git" not in p.parts}
            with patch("builtins.input", side_effect=["2", "1"]), patch("builtins.print"):
                self.assertEqual(app.initialize(root, "合成", interactive=True), 14)
            self.assertEqual(git(root, "status", "--porcelain"), b"")
            self.assertEqual(git(root, "diff"), b"")
            (root / "docs/project/report.txt").write_text("generated\n")
            (root / ".bootstrap/cache").mkdir()
            (root / ".bootstrap/cache/sample.txt").write_text("cache")
            (root / "docs/project/rules.md").write_text("local customization")
            with patch("builtins.input", side_effect=AssertionError("do not ask")):
                self.assertEqual(app.initialize(root, "合成", interactive=True), 0)
            self.assertEqual(exclude.read_bytes().count(app.EXCLUDE_BLOCK), 1)
            git(root, "switch", "-c", "fix/synthetic-message")
            (root / "task.txt").write_text("after\n", encoding="utf-8")
            git(root, "add", ".")
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), b"task.txt\n")
            git(root, "commit", "-m", "fix: synthetic message")
            self.assertEqual(git(root, "show", "--pretty=", "--name-only", "HEAD"), b"task.txt\n")
            git(root, "switch", "main")
            git(root, "merge", "--ff-only", "fix/synthetic-message")
            git(root, "branch", "-d", "fix/synthetic-message")
            # Later owner excludes must also survive deinit.
            exclude.write_bytes(exclude.read_bytes() + b"*.later\n")
            command = [sys.executable, str(root / ".bootstrap/bootstrap.py"), "deinit", str(root)]
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "AGENTS.md").exists())
            result = subprocess.run(command + ["--yes"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(exclude.read_bytes(), initial + b"*.later\n")
            self.assertEqual([p.name for p in root.rglob("*") if p.is_file() and ".git" not in p.parts], ["task.txt"])
            self.assertEqual(before_dirs, {p.relative_to(root) for p in root.rglob("*") if p.is_dir() and ".git" not in p.parts})
            self.assertEqual(git(root, "status", "--porcelain"), b"")
            self.assertEqual(git(root, "ls-files"), b"task.txt\n")

    def test_local_conflicts_and_failed_visibility_roll_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "conflict"
            repository(root)
            exclude = root / ".git/info/exclude"
            initial = exclude.read_bytes()
            (root / "AGENTS.md").write_text("existing rules")
            with self.assertRaisesRegex(ValueError, "冲突"):
                app.initialize(root, "合成", bootstrap_mode="Local-only")
            git(root, "add", "AGENTS.md")
            with self.assertRaisesRegex(ValueError, "跟踪或暂存"):
                app.initialize(root, "合成", bootstrap_mode="Local-only")
            self.assertEqual(exclude.read_bytes(), initial)
            self.assertFalse((root / ".bootstrap").exists())
            root = Path(temp) / "negated"
            repository(root)
            (root / ".gitignore").write_text("!AGENTS.md\n")
            git(root, "add", ".gitignore")
            git(root, "commit", "-m", "test: negated ignore")
            exclude = root / ".git/info/exclude"
            initial = exclude.read_bytes()
            with self.assertRaisesRegex(ValueError, "仍对 Git 可见"):
                app.initialize(root, "合成", bootstrap_mode="Local-only")
            self.assertEqual(exclude.read_bytes(), initial)
            self.assertFalse((root / ".bootstrap").exists())
            self.assertEqual(git(root, "status", "--porcelain"), b"")

    def test_cleanup_refuses_tracked_files_and_escaping_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "safe"
            repository(root)
            app.initialize(root, "合成", bootstrap_mode="Local-only")
            git(root, "add", "-f", "AGENTS.md")
            with self.assertRaisesRegex(ValueError, "跟踪或暂存"):
                app.deinitialize(root, yes=True)
            self.assertTrue((root / "AGENTS.md").exists())
            git(root, "reset", "--", "AGENTS.md")
            outside = Path(temp) / "outside"
            outside.mkdir()
            (outside / "keep.txt").write_text("keep")
            link = root / "docs/project/external"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, "链接或 junction"):
                app.deinitialize(root, yes=True)
            self.assertEqual((outside / "keep.txt").read_text(), "keep")
            # Remove only the known junction itself; never traverse its target.
            link.rmdir() if not link.is_symlink() else link.unlink()
            app.deinitialize(root, yes=True)

    def test_worktree_exclude_and_map_output_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            primary, worktree = Path(temp) / "primary", Path(temp) / "linked"
            repository(primary)
            git(primary, "worktree", "add", "-b", "chore/linked", str(worktree))
            exclude = primary / ".git/info/exclude"
            initial = exclude.read_bytes()
            app.initialize(worktree, "合成", bootstrap_mode="Local-only")
            self.assertEqual(git(worktree, "status", "--porcelain"), b"")
            self.assertIn(app.EXCLUDE_BLOCK, exclude.read_bytes())
            command = [sys.executable, str(worktree / ".bootstrap/bootstrap.py"), "map", str(worktree / "project.manifest.json"),
                       "--output", str(worktree / "visible.html")]
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertFalse((worktree / "visible.html").exists())
            app.deinitialize(worktree, yes=True)
            self.assertEqual(exclude.read_bytes(), initial)
            self.assertEqual(git(worktree, "status", "--porcelain"), b"")


if __name__ == "__main__":
    unittest.main()
