"""Git onboarding persists intent without staging, committing or uploading files."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()


class GitInitializationTests(unittest.TestCase):
    def initialize(self, root, **kwargs):
        kwargs.setdefault("bootstrap_mode", "Standard")
        kwargs.setdefault("deployment_mode", "Local-first")
        kwargs.setdefault("agent_doc_mode", "isolated")
        return app.initialize(root, kwargs.pop("name", "Synthetic"), **kwargs)

    def test_fresh_directory_initializes_git_and_keeps_files_unstaged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "fresh"
            self.initialize(root, git_remote_setup="local", git_push_mode="Local-only")
            self.assertEqual(Path(git(root, "rev-parse", "--show-toplevel")), root)
            self.assertEqual(git(root, "remote"), "")
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "")
            self.assertNotEqual(subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], capture_output=True).returncode, 0)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Git Remote Setup: Local-only", agents)
            self.assertIn("Git Push Mode: Local-only", agents)

    def test_remote_auto_without_remote_stays_pending_and_never_pushes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "pending"
            self.initialize(root, git_remote_setup="local", git_push_mode="Remote-auto")
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Git Remote Setup: Remote-pending", agents)
            self.assertIn("Git Push Mode: Remote-auto", agents)
            self.assertEqual(git(root, "remote"), "")
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "")

    def test_pending_remote_can_be_completed_by_repeating_init_with_url(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "resume"
            self.initialize(root, git_remote_setup="local", git_push_mode="Remote-auto")
            self.assertIn("Git Remote Setup: Remote-pending", (root / "AGENTS.md").read_text(encoding="utf-8"))
            manifest = root / "project.manifest.json"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertEqual(self.initialize(root, name=None, remote_url="https://github.com/example/resume.git"), 0)
            self.assertTrue(manifest.read_text(encoding="utf-8").endswith("\n\n"))
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Git Remote Setup: Remote-ready", agents)
            self.assertIn("Git Push Mode: Remote-auto", agents)
            self.assertEqual(git(root, "remote", "get-url", "origin"), "https://github.com/example/resume.git")

    def test_local_only_pending_remote_retry_does_not_reverify_or_rewrite_project_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "local-resume"
            self.initialize(root, name="Local Resume", bootstrap_mode="Local-only",
                git_remote_setup="local", git_push_mode="Remote-auto")
            manifest = root / app.LOCAL_HOME / "project.manifest.json"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertEqual(app.initialize(root, None, remote_url="https://github.com/example/local-resume.git"), 0)
            self.assertTrue(manifest.read_text(encoding="utf-8").endswith("\n\n"))
            self.assertEqual(git(root, "remote", "get-url", "origin"), "https://github.com/example/local-resume.git")
            self.assertIn("Git Remote Setup: Remote-ready",
                          (root / app.LOCAL_HOME / "AGENTS.md").read_text(encoding="utf-8"))

    def test_user_url_adds_remote_without_uploading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "url"
            self.initialize(root, git_remote_setup="url", remote_url="https://github.com/example/synthetic.git",
                            git_push_mode="Remote-auto")
            self.assertEqual(git(root, "remote", "get-url", "origin"), "https://github.com/example/synthetic.git")
            self.assertIn("Git Remote Setup: Remote-ready", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "")
            self.assertNotEqual(subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], capture_output=True).returncode, 0)

    def test_existing_remote_requires_selection_when_multiple(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "multi"
            root.mkdir()
            subprocess.run(["git", "-C", str(root), "init"], capture_output=True, check=True)
            git(root, "remote", "add", "origin", "https://example.invalid/one.git")
            git(root, "remote", "add", "backup", "https://example.invalid/two.git")
            with self.assertRaisesRegex(ValueError, "多个 remote"):
                self.initialize(root, git_remote_setup="existing", git_push_mode="Local-only")
            self.initialize(root, git_remote_setup="existing", remote_name="backup", git_push_mode="Local-only")
            self.assertIn("Git Remote Setup: Remote-ready", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual(git(root, "remote", "get-url", "origin"), "https://example.invalid/one.git")
            self.assertEqual(git(root, "remote", "get-url", "backup"), "https://example.invalid/two.git")

    def test_github_cli_create_is_private_by_default_and_does_not_push(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "created"
            calls = []

            class Result:
                def __init__(self, returncode=0, stdout="", stderr=""):
                    self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

            real_run = subprocess.run

            def fake_run(command, *args, **kwargs):
                if isinstance(command, list) and command and command[0] == "gh":
                    calls.append(command)
                    if command[1:3] == ["api", "user"]:
                        return Result(stdout="owner\n")
                    if command[1:3] == ["auth", "status"]:
                        return Result()
                    if command[1:3] == ["repo", "create"]:
                        git(root, "remote", "add", command[command.index("--remote") + 1],
                            "https://github.com/owner/synthetic-project.git")
                        return Result()
                return real_run(command, *args, **kwargs)

            real_which = app.shutil.which
            with patch.object(app.shutil, "which", side_effect=lambda command: "gh" if command == "gh" else real_which(command)), patch.object(app.subprocess, "run", side_effect=fake_run):
                self.initialize(root, git_remote_setup="create", repo_name="synthetic-project",
                                 git_push_mode="Remote-auto")
            create_call = next(call for call in calls if call[1:3] == ["repo", "create"])
            self.assertIn("--private", create_call)
            self.assertNotIn("--push", create_call)
            self.assertEqual(git(root, "remote", "get-url", "origin"), "https://github.com/owner/synthetic-project.git")
            self.assertIn("Git Push Mode: Remote-auto", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_missing_github_cli_leaves_remote_pending_but_keeps_local_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "no-gh"
            real_which = app.shutil.which
            with patch.object(app.shutil, "which", side_effect=lambda command: None if command == "gh" else real_which(command)):
                self.initialize(root, git_remote_setup="create", git_push_mode="Remote-auto")
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertIn("Git Remote Setup: Remote-pending", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("Git Push Mode: Remote-auto", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual(git(root, "remote"), "")

    def test_slug_suggestion_and_interactive_two_choice_prompts(self):
        self.assertEqual(app.slug_suggestion("Synthetic Project v2"), "synthetic-project-v2")
        self.assertEqual(app.repo_name_suggestions("Synthetic Project"),
                         ("synthetic-project", "synthetic-project-app", "synthetic-project-project"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "interactive"
            with patch("builtins.input", side_effect=["Demo", "local", "Remote-auto"]):
                app.initialize(root, None, bootstrap_mode="Standard", deployment_mode="Local-first",
                               agent_doc_mode="isolated", interactive=True)
            self.assertIn('"name": "Demo"', (root / "project.manifest.json").read_text(encoding="utf-8"))
            self.assertIn("Git Remote Setup: Remote-pending", (root / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
