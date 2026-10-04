"""Delivery authorization and honest, persistent initialization receipts."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app
from test_local_only import isolated_agent_env


class InstallationReceiptTests(unittest.TestCase):
    def install(self, root, mode="Standard", **kwargs):
        kwargs.setdefault("git_remote_setup", "local")
        return app.initialize(root, "Synthetic", bootstrap_mode=mode, **kwargs)

    def test_explicit_delivery_scope_and_reuse_does_not_select_new_remote(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            self.install(root, git_completion_mode="Auto")
            before = (root / "AGENTS.md").read_bytes()
            subprocess.run(["git", "-C", str(root), "remote", "add", "unselected", "https://example.invalid/new.git"], check=True)
            with patch("builtins.input", side_effect=AssertionError("choice repeated")):
                app.initialize(root, None, interactive=True)
            self.assertEqual(before, (root / "AGENTS.md").read_bytes())
            self.assertEqual(app.git_output(root, "diff", "--cached", "--name-only"), "")
            self.assertIn(b"Git Remote Name: none", before)

    def test_new_mode_uses_only_selected_remote_and_rejects_duplicate_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            subprocess.run(["git", "-C", str(root), "init"], capture_output=True, check=True)
            for name in ("origin", "backup"):
                subprocess.run(["git", "-C", str(root), "remote", "add", name, "https://example.invalid/" + name], check=True)
            self.install(root, git_remote_setup="existing", remote_name="backup", git_completion_mode="Manual")
            text = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Git Completion Mode: Manual", text)
            self.assertIn("Git Push Mode: Remote-auto", text)
            self.assertIn("Git Remote Name: backup", text)
            with self.assertRaisesRegex(ValueError, "只选择"):
                self.install(Path(temp) / "bad", git_completion_mode="Auto", git_push_mode="Local-only")
            self.assertFalse((Path(temp) / "bad").exists())

    def test_old_installation_does_not_expand_or_migrate_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            self.install(root, git_push_mode="Local-only")
            entry = root / "AGENTS.md"
            entry.write_text(entry.read_text(encoding="utf-8").replace("Git Completion Mode: Unselected\n", ""), encoding="utf-8")
            before = entry.read_bytes()
            app.initialize(root, None)
            self.assertEqual(before, entry.read_bytes())
            summary, _ = app.installation_report(root, {"status": "skipped"})
            self.assertIn("未授权新版完整自动交付", summary)

    def test_crlf_git_policy_and_explicit_mode_update_preserve_newlines(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            self.install(root, git_completion_mode="Auto")
            entry = root / "AGENTS.md"
            text = entry.read_text(encoding="utf-8")
            entry.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            app.initialize(root, None, git_completion_mode="Manual")
            result = entry.read_bytes()
            self.assertIn(b"Git Completion Mode: Manual\r\n", result)
            self.assertNotIn(b"\n", result.replace(b"\r\n", b""))

    def test_both_layouts_report_pending_and_require_external_verifier_reference(self):
        for mode in ("Standard", "Local-only"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "project"
                self.install(root, mode, git_completion_mode="Manual")
                summary, report = app.installation_report(root, {"status": "unavailable", "argv": ["PRIVATE_PATH"], "error": "SECRET"})
                self.assertIn("初始化验收未完成", summary)
                self.assertIn("不可用", summary)
                self.assertIn("等待人类合并", summary)
                self.assertNotIn("SECRET", summary)
                self.assertNotIn("PRIVATE_PATH", summary)
                self.assertTrue(report.is_file())
                if mode == "Local-only":
                    self.assertEqual(app.git_output(root, "status", "--porcelain"), "")
                verifier = Path(temp) / "verifier.txt"
                verifier.write_text("PASS\n原因：合成测试结果；不冒充真实独立验收。", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "任务引用"):
                    app.installation_report(root, {"status": "skipped"}, verifier)

    def test_acceptance_is_snapshot_bound_and_preserves_unmanaged_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            self.install(root, git_completion_mode="Auto")
            summary, report = app.installation_report(root, {"status": "skipped"})
            report.write_text("既有授权及规则证据\n" + report.read_text(encoding="utf-8"), encoding="utf-8")
            verifier = Path(temp) / "verifier.txt"
            verifier.write_text("PASS\n原因：合成测试证据。", encoding="utf-8")
            summary, _ = app.installation_report(root, {"status": "skipped"}, verifier, "synthetic-verifier")
            self.assertIn("基础初始化成功", summary)
            self.assertTrue(report.read_text(encoding="utf-8").startswith("既有授权及规则证据"))
            summary, _ = app.installation_report(root, {"status": "skipped"})
            self.assertIn("基础初始化成功", summary)
            entry = root / "AGENTS.md"
            entry.write_text(entry.read_text(encoding="utf-8") + "\n原项目新约束\n", encoding="utf-8")
            summary, _ = app.installation_report(root, {"status": "skipped"})
            self.assertIn("初始化验收未完成", summary)
            verifier.write_text("REQUEST_CHANGES\n原因：合成限制待处理。", encoding="utf-8")
            summary, _ = app.installation_report(root, {"status": "skipped"}, verifier, "synthetic-verifier-2")
            self.assertNotIn("基础初始化成功", summary)
            self.assertIn("REQUEST_CHANGES", summary)

    def test_cli_writes_readable_receipt_and_portable_report_entry(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, isolated_agent_env(Path(temp))):
            root = Path(temp) / "project with spaces"
            command = [sys.executable, str(app.BASE / "bootstrap.py"), "init", str(root), "--name", "Synthetic",
                       "--git-remote-setup", "local", "--git-completion-mode", "Auto", "--low-cost-agent", "skip"]
            result = subprocess.run(command, capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("配置项", result.stdout)
            self.assertIn("已跳过", result.stdout)
            self.assertIn("初始化验收未完成", result.stdout)
            installed = root / app.LOCAL_HOME / "bootstrap.py"
            result = subprocess.run([sys.executable, str(installed), "report-install", str(root)], capture_output=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Auto", result.stdout)
            self.assertEqual(app.git_output(root, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
