"""Synthetic Git lifecycle: preserve original rules, tasks and worktree isolation."""
from pathlib import Path
import os
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
    for name, text in {"task.txt": "before\n", "AGENTS.md": "Keep original project rules.\n",
                       "CLAUDE.md": "Keep original Claude rules.\n"}.items():
        (root / name).write_text(text, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "test: synthetic baseline")


def bundle(root):
    return root / app.LOCAL_HOME


def cli(root, *args):
    return subprocess.run([sys.executable, "-X", "utf8", str(bundle(root) / "bootstrap.py"), *args], capture_output=True)


class LocalOnlyTests(unittest.TestCase):
    def test_default_lifecycle_preserves_rules_tasks_and_entry_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "cooperation with spaces"
            repository(root)
            config = root / ".git/config"
            config_before = config.read_bytes()
            (root / "docs/project").mkdir(parents=True)
            (root / "docs/project/overview.md").write_text("existing project document")
            (root / "project.manifest.json").write_text("existing unrelated manifest")
            git(root, "add", "docs", "project.manifest.json")
            git(root, "commit", "-m", "test: preserve existing documents")
            original = {p: (root / p).read_bytes() for p in ("AGENTS.md", "CLAUDE.md")}
            for name in app.ENTRY_NAMES:
                (root / name).write_bytes(b"original local preference without newline")
            (root / "task.txt").write_text("user work in progress\n")
            before_diff = git(root, "diff")
            with patch("builtins.input", side_effect=AssertionError("no prompts")):
                app.initialize(root, "合成", interactive=True)
            self.assertEqual(git(root, "status", "--porcelain"), b" M task.txt\n")
            self.assertEqual(git(root, "diff"), before_diff)
            self.assertEqual(git(root, "diff", "--cached"), b"")
            self.assertEqual(original, {p: (root / p).read_bytes() for p in original})
            self.assertEqual((root / "docs/project/overview.md").read_text(), "existing project document")
            self.assertEqual((root / "project.manifest.json").read_text(), "existing unrelated manifest")
            (bundle(root) / "docs/rules.md").write_text("local customization")
            self.assertEqual(app.initialize(root, "合成"), 0)
            self.assertEqual((bundle(root) / "docs/rules.md").read_text(), "local customization")
            self.assertEqual((bundle(root) / "docs/usage.md").read_bytes(), (app.BASE / "MANUAL.md").read_bytes())
            self.assertTrue((bundle(root) / app.read_json(bundle(root) / "project.manifest.json")["$schema"]).is_file())
            self.assertEqual(cli(root, "verify-install", str(root)).returncode, 0)
            git(root, "switch", "-c", "fix/synthetic-message")
            git(root, "add", ".")
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), b"task.txt\n")
            git(root, "commit", "-m", "fix: synthetic message")
            git(root, "switch", "main")
            git(root, "merge", "--ff-only", "fix/synthetic-message")
            git(root, "branch", "-d", "fix/synthetic-message")
            for name in app.ENTRY_NAMES:
                path = root / name
                path.write_bytes(path.read_bytes() + b"\nnew owner preference\n")
            config.write_bytes(config.read_bytes() + b"\n# new owner config\n")
            self.assertEqual(cli(root, "deinit", str(root)).returncode, 0)
            self.assertTrue(bundle(root).exists())
            result = cli(root, "deinit", str(root), "--yes")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(bundle(root).exists())
            self.assertEqual(config.read_bytes(), config_before + b"\n# new owner config\n")
            for name in app.ENTRY_NAMES:
                self.assertEqual((root / name).read_bytes(), b"original local preference without newline\nnew owner preference\n")
            self.assertEqual(git(root, "diff"), b"")
            self.assertEqual(git(root, "show", "--pretty=", "--name-only", "HEAD"), b"task.txt\n")

    def test_worktrees_install_independently_and_keep_standard_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            primary, linked, standard = (Path(temp) / name for name in ("primary", "linked", "standard"))
            repository(primary)
            git(primary, "worktree", "add", "-b", "chore/linked", str(linked))
            git(primary, "worktree", "add", "-b", "chore/standard", str(standard))
            # Standard installation in a synthetic empty branch shares the repository.
            git(standard, "rm", "AGENTS.md", "CLAUDE.md")
            git(standard, "commit", "-m", "test: prepare standard fixture")
            app.initialize(standard, "合成", bootstrap_mode="Standard")
            status = git(standard, "status", "--porcelain", "--untracked-files=all")
            config = primary / ".git/config"
            before = config.read_bytes()
            app.initialize(primary, "合成")
            app.initialize(linked, "合成")
            self.assertEqual(git(primary, "status", "--porcelain"), b"")
            self.assertEqual(git(linked, "status", "--porcelain"), b"")
            self.assertEqual(git(standard, "status", "--porcelain", "--untracked-files=all"), status)
            git(standard, "add", ".")
            self.assertIn(b"AGENTS.md", git(standard, "diff", "--cached", "--name-only"))
            app.deinitialize(primary, yes=True)
            app.verify_install(linked)
            self.assertEqual(git(linked, "status", "--porcelain"), b"")
            app.deinitialize(linked, yes=True)
            self.assertEqual(config.read_bytes(), before)
            self.assertEqual(set(p.name for p in primary.iterdir()), {".git", "task.txt", "AGENTS.md", "CLAUDE.md"})

    def test_original_ignore_rules_refresh_without_global_or_shared_edits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "ignore"
            repository(root)
            rules = Path(temp) / "inherited.ignore"
            rules.write_bytes(b"*.secret\n")
            git(root, "config", "core.excludesFile", str(rules))
            shared = root / ".git/info/exclude"
            shared_before = shared.read_bytes()
            config_before = (root / ".git/config").read_bytes()
            (root / "a.secret").write_text("synthetic")
            app.initialize(root, "合成")
            self.assertEqual(git(root, "status", "--porcelain"), b"")
            rules.write_bytes(b"*.secret\n*.later\n")
            (root / "b.later").write_text("synthetic")
            app.verify_install(root)
            self.assertEqual(git(root, "status", "--porcelain"), b"")
            self.assertEqual(shared.read_bytes(), shared_before)
            app.deinitialize(root, yes=True)
            self.assertEqual((root / ".git/config").read_bytes(), config_before)
            self.assertEqual(git(root, "status", "--porcelain"), b"")

    def test_preflight_and_failure_restore_original_files_and_git_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "conflict"
            repository(root)
            config = root / ".git/config"
            before = config.read_bytes()
            (root / "AGENTS.override.md").write_bytes(b"local original")
            git(root, "add", "AGENTS.override.md")
            with self.assertRaisesRegex(ValueError, "跟踪或暂存"):
                app.initialize(root, "合成")
            self.assertFalse(bundle(root).exists())
            git(root, "reset", "--", "AGENTS.override.md")
            (root / ".gitignore").write_text("!AGENTS.override.md\n")
            with self.assertRaisesRegex(ValueError, "仍对 Git 可见"):
                app.initialize(root, "合成")
            self.assertFalse(bundle(root).exists())
            self.assertEqual((root / "AGENTS.override.md").read_bytes(), b"local original")
            self.assertFalse((root / "CLAUDE.local.md").exists())
            self.assertEqual(config.read_bytes(), before)
            with patch.object(app, "render_diagrams", side_effect=ValueError("render failed")):
                with self.assertRaisesRegex(ValueError, "render failed"):
                    app.initialize(root, "合成")
            self.assertFalse(bundle(root).exists())
            self.assertEqual(config.read_bytes(), before)

            # A directory created by someone else during rendering is not ours to remove.
            rendered = app.render_diagrams(app.starter("合成"))
            def occupy_during_render(*args):
                bundle(root).mkdir()
                (bundle(root) / "owner.txt").write_text("keep")
                return rendered
            with patch.object(app, "render_diagrams", side_effect=occupy_during_render):
                with self.assertRaises(FileExistsError):
                    app.initialize(root, "合成")
            self.assertEqual((bundle(root) / "owner.txt").read_text(), "keep")
            self.assertEqual(config.read_bytes(), before)

    def test_cleanup_and_map_reject_tracked_files_and_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "safe"
            repository(root)
            app.initialize(root, "合成")
            result = cli(root, "map", str(bundle(root) / "project.manifest.json"), "--output", str(root / "visible.html"))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "visible.html").exists())
            git(root, "add", "-f", "AGENTS.override.md")
            with self.assertRaisesRegex(ValueError, "跟踪或暂存"):
                app.deinitialize(root, yes=True)
            git(root, "reset", "--", "AGENTS.override.md")
            outside = Path(temp) / "outside"
            outside.mkdir()
            (outside / "keep.txt").write_text("keep")
            link = bundle(root) / "docs/external"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, "链接或 junction"):
                app.deinitialize(root, yes=True)
            self.assertEqual((outside / "keep.txt").read_text(), "keep")
            link.rmdir() if not link.is_symlink() else link.unlink()
            app.deinitialize(root, yes=True)

    def test_verify_fails_for_changed_entries_and_deinit_can_remove_visible_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "verify"
            repository(root)
            app.initialize(root, "合成")
            entry = root / "AGENTS.override.md"
            original = entry.read_bytes()
            entry.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "入口区块"):
                app.verify_install(root)
            entry.write_bytes(original)
            (root / ".gitignore").write_text("!AGENTS.override.md\n")
            with self.assertRaisesRegex(ValueError, "仍对 Git 可见"):
                app.verify_install(root)
            app.deinitialize(root, yes=True)
            self.assertFalse(entry.exists())
            self.assertEqual((root / ".gitignore").read_text(), "!AGENTS.override.md\n")

    def test_legacy_install_is_not_migrated_and_can_be_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "legacy"
            repository(root)
            # Synthetic v1 owned files, with no pre-existing project rules.
            git(root, "rm", "AGENTS.md", "CLAUDE.md")
            git(root, "commit", "-m", "test: legacy fixture")
            home = root / ".bootstrap"
            home.mkdir()
            (home / "install-state.json").write_text(app.encode({"bootstrap_mode": "Local-only", "preexisting_dirs": [], "exclude_existed": True}))
            (root / "AGENTS.md").write_text("Bootstrap Mode: Local-only\n")
            exclude = root / ".git/info/exclude"
            before = exclude.read_bytes()
            exclude.write_bytes(before + app.EXCLUDE_BLOCK)
            with self.assertRaisesRegex(ValueError, "旧版 Local-only"):
                app.initialize(root, "合成")
            self.assertTrue(home.exists())
            app.deinitialize(root, yes=True)
            self.assertFalse(home.exists())
            self.assertEqual(exclude.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
