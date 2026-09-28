"""Explicit install choices and opt-in tracked indexes; synthetic repositories only."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app
from test_local_only import git, repository, bundle


class InstallDecisionTests(unittest.TestCase):
    def test_missing_choices_fail_without_any_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "choices"
            repository(root)
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            for options in ({}, {"deployment_mode": "Local-first"}, {"agent_doc_mode": "indexed"}):
                for storage in app.BOOTSTRAP_MODES:
                    with self.subTest(options=options, storage=storage), self.assertRaisesRegex(ValueError, "必须由用户明确选择"):
                        app.initialize(root, "合成", bootstrap_mode=storage, **options)
                self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})
            result = subprocess.run([sys.executable, "-X", "utf8", str(app.BASE / "bootstrap.py"), "init", str(root)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("必须由用户明确选择", result.stderr.decode("utf-8"))
            self.assertFalse(bundle(root).exists())

    def test_all_four_choices_preserve_user_edits_and_only_expose_authorized_indexes(self):
        with tempfile.TemporaryDirectory() as temp:
            for deploy in app.DEPLOYMENT_MODES:
                for mode in app.AGENT_DOC_MODES:
                    with self.subTest(deployment=deploy, document_mode=mode):
                        root = Path(temp) / (deploy + mode)
                        repository(root)
                        (root / "AGENTS.md").write_bytes(b"original\r\nuser work without final newline")
                        (root / "task.txt").write_text("user task edits")
                        original = {name: (root / name).read_bytes() for name in ("AGENTS.md", "CLAUDE.md", "task.txt")}
                        app.initialize(root, "合成", deployment_mode=deploy, agent_doc_mode=mode)
                        state = app.verify_install(root)
                        self.assertEqual(state["agent_doc_mode"], mode)
                        text = (bundle(root) / "AGENTS.md").read_text(encoding="utf-8")
                        self.assertIn("Deployment Mode: " + deploy, text)
                        self.assertIn("Agent Document Mode: " + mode, text)
                        self.assertEqual(app.initialize(root, "合成"), 0)
                        with self.assertRaisesRegex(ValueError, "冲突"):
                            app.initialize(root, "合成", agent_doc_mode="indexed" if mode == "isolated" else "isolated")
                        for name in ("AGENTS.md", "CLAUDE.md"):
                            data = (root / name).read_bytes()
                            expected = original[name] + (app.INDEX_BLOCK if mode == "indexed" else b"")
                            self.assertEqual(data, expected)
                        git(root, "add", ".")
                        staged = set(git(root, "diff", "--cached", "--name-only").decode().splitlines())
                        self.assertEqual(staged, {"AGENTS.md", "task.txt"} | ({"CLAUDE.md"} if mode == "indexed" else set()))
                        git(root, "reset")
                        # An owner edit outside the managed block survives removal.
                        (root / "AGENTS.md").write_bytes((root / "AGENTS.md").read_bytes() + b"\nowner addition")
                        app.deinitialize(root, yes=True)
                        self.assertEqual((root / "AGENTS.md").read_bytes(), original["AGENTS.md"] + b"\nowner addition")
                        self.assertEqual((root / "CLAUDE.md").read_bytes(), original["CLAUDE.md"])
                        self.assertEqual((root / "task.txt").read_bytes(), original["task.txt"])

    def test_committed_indexes_are_optional_for_collaborators_and_reused_in_worktree(self):
        with tempfile.TemporaryDirectory() as temp:
            root, other = Path(temp) / "primary", Path(temp) / "collaborator"
            repository(root)
            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            git(root, "add", "AGENTS.md", "CLAUDE.md")
            git(root, "commit", "-m", "docs: optional local bootstrap index")
            git(root, "worktree", "add", "-b", "test/collaborator", str(other))
            self.assertFalse(bundle(other).exists())
            self.assertEqual(git(other, "status", "--porcelain"), b"")
            before = {name: (other / name).read_bytes() for name in ("AGENTS.md", "CLAUDE.md")}
            for data in before.values():
                self.assertIn("若文件不存在，忽略本区块".encode(), data)
                self.assertNotIn(b"@.project-bootstrap", data)
            app.initialize(other, "合成", deployment_mode="Production-direct", agent_doc_mode="indexed")
            self.assertEqual(set(app.verify_install(other)["reused_entries"]), {"AGENTS.md", "CLAUDE.md"})
            self.assertEqual(git(other, "status", "--porcelain"), b"")
            app.deinitialize(other, yes=True)
            self.assertEqual(before, {name: (other / name).read_bytes() for name in before})
            self.assertEqual(git(other, "status", "--porcelain"), b"")
            app.deinitialize(root, yes=True)
            self.assertEqual(set(git(root, "diff", "--name-only").decode().splitlines()), {"AGENTS.md", "CLAUDE.md"})
            self.assertEqual(git(root, "diff", "--cached"), b"")

    def test_index_fallback_dot_claude_and_shadowing_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "fallback"
            repository(root)
            git(root, "rm", "AGENTS.md", "CLAUDE.md")
            (root / ".claude").mkdir()
            (root / ".claude/CLAUDE.md").write_text("original nested client entry")
            git(root, "add", "."); git(root, "commit", "-m", "test: alternate entry")
            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            state = app.verify_install(root)
            self.assertEqual(state["indexed_entries"], [".claude/CLAUDE.md"])
            self.assertTrue((root / "AGENTS.override.md").is_file())
            app.deinitialize(root, yes=True)
            self.assertEqual(git(root, "status", "--porcelain"), b"")
            root = Path(temp) / "shadowed"
            repository(root)
            (root / "AGENTS.override.md").write_text("higher priority owner rules")
            config = (root / ".git/config").read_bytes()
            with self.assertRaisesRegex(ValueError, "遮蔽"):
                app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            self.assertFalse(bundle(root).exists())
            self.assertEqual((root / ".git/config").read_bytes(), config)
            (root / "AGENTS.override.md").unlink()
            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            (root / "AGENTS.override.md").write_text("later owner override")
            with self.assertRaisesRegex(ValueError, "遮蔽"):
                app.verify_install(root)
            app.deinitialize(root, yes=True)
            self.assertEqual((root / "AGENTS.override.md").read_text(), "later owner override")

    def test_dangling_client_rule_links_fail_before_install_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            for name in ("CLAUDE.md", ".claude/CLAUDE.md"):
                with self.subTest(entry=name):
                    root = Path(temp) / name.replace("/", "-")
                    repository(root)
                    git(root, "rm", "CLAUDE.md")
                    link = root / name
                    link.parent.mkdir(exist_ok=True)
                    before_status = git(root, "status", "--porcelain")
                    before_config = (root / ".git/config").read_bytes()
                    original_is_symlink = Path.is_symlink
                    with patch.object(Path, "is_symlink", lambda path: path == link or original_is_symlink(path)):
                        with self.assertRaisesRegex(ValueError, "链接或 junction"):
                            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
                    self.assertEqual(git(root, "status", "--porcelain"), before_status)
                    self.assertEqual((root / ".git/config").read_bytes(), before_config)
                    self.assertFalse(link.exists())
                    self.assertFalse(bundle(root).exists())

    def test_index_line_endings_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "line-endings"
            repository(root)
            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            for name in ("AGENTS.md", "CLAUDE.md"):
                p = root / name
                p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
            app.verify_install(root)
            app.deinitialize(root, yes=True)
            self.assertNotIn(b"Project Bootstrap Index", (root / "AGENTS.md").read_bytes())
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            real = app.atomic_bytes
            def fail_entry(path, data):
                if path == root / "CLAUDE.md" and app.INDEX_BLOCK in data:
                    raise OSError("synthetic entry write failure")
                return real(path, data)
            with patch.object(app, "atomic_bytes", side_effect=fail_entry), self.assertRaisesRegex(OSError, "entry write failure"):
                app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_v2_remains_readable_without_mode_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "v2"
            repository(root)
            app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="isolated")
            state_file = bundle(root) / "install-state.json"
            state_file.write_text(app.encode({"version": 2, "bootstrap_mode": "Local-only", "entry_existed": {name: False for name in app.ENTRY_NAMES}}))
            original_state = state_file.read_bytes()
            self.assertEqual(app.initialize(root, "合成"), 0)
            self.assertEqual(state_file.read_bytes(), original_state)
            app.verify_install(root)
            app.deinitialize(root, yes=True)
            self.assertEqual(git(root, "status", "--porcelain"), b"")

    def test_non_utf8_core_document_is_not_mixed_with_utf8_index(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "encoding"
            repository(root)
            original = "原项目规则".encode("utf-16")
            (root / "CLAUDE.md").write_bytes(original)
            config = (root / ".git/config").read_bytes()
            with self.assertRaisesRegex(ValueError, "不是 UTF-8"):
                app.initialize(root, "合成", deployment_mode="Local-first", agent_doc_mode="indexed")
            self.assertEqual((root / "CLAUDE.md").read_bytes(), original)
            self.assertEqual((root / ".git/config").read_bytes(), config)
            self.assertFalse(bundle(root).exists())

    def test_technical_cli_cannot_claim_independent_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pending"
            repository(root)
            result = subprocess.run([sys.executable, "-X", "utf8", str(app.BASE / "bootstrap.py"), "init", str(root),
                "--deployment-mode", "Local-first", "--agent-doc-mode", "isolated"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("未 PASS 不得报告初始化完成", result.stdout.decode("utf-8"))
            result = subprocess.run([sys.executable, "-X", "utf8", str(bundle(root) / "bootstrap.py"), "verify-install", str(root)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("不代表独立子 Agent 验收通过", result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
