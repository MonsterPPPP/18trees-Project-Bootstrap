"""Small contract suite; real archify integration, no business implementation."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = app.read_json(app.BASE / "examples/synthetic.manifest.json")
        cls.diagrams = app.render_diagrams(cls.example)

    def test_example_schema_and_graph(self):
        app.validate_manifest(self.example)
        app.validate_manifest(app.starter("空项目"))
        for mutate in (
            lambda m: m["nodes"].append(copy.deepcopy(m["nodes"][0])),
            lambda m: m["nodes"][0].update(path="src/private.ts"),
            lambda m: m["relationships"][0].update(to="NODE:missing"),
            lambda m: m["relationships"][0].update(to="NODE:storage"),
            lambda m: m["relationships"].pop(6),
            lambda m: m["relationships"].pop(2),
            lambda m: m["nodes"][0].update(status="implemented"),
            lambda m: m["workflows"].clear(),
            lambda m: m["workflows"].append(copy.deepcopy(m["workflows"][0])),
        ):
            manifest = copy.deepcopy(self.example)
            mutate(manifest)
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                app.validate_manifest(manifest)

    def test_metadata_rejects_absolute_and_parent_paths(self):
        for path in ("C:/private/x", "../outside", "folder/../outside", "/private", "folder\\secret"):
            manifest = copy.deepcopy(self.example)
            manifest["nodes"][3]["metadata"]["references"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                app.validate_manifest(manifest)

    def test_map_detects_visible_changes_staleness_and_diagram_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "map.html"
            original = app.map_document(self.example, self.diagrams)
            path.write_text(original, encoding="utf-8")
            app.validate_map(self.example, path)
            stale = copy.deepcopy(self.example)
            stale["nodes"][0]["summary"] = "产品语义已改变"
            with self.assertRaisesRegex(ValueError, "manifest 不一致"):
                app.validate_map(stale, path)
            path.write_text(original.replace("<h3>草稿管理</h3>", "<h3>错误能力</h3>"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "页面内容"):
                app.validate_map(self.example, path)
            diagrams = copy.deepcopy(self.diagrams)
            diagrams[0]["html"] += "tamper"
            path.write_text(app.map_document(self.example, diagrams), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "校验和"):
                app.validate_map(self.example, path)

    def test_init_then_manifest_then_map_and_portable_cli(self):
        with tempfile.TemporaryDirectory(prefix="bootstrap-e2e-") as temp:
            project = Path(temp) / "新项目 with spaces"
            self.assertEqual(app.initialize(project, "空项目"), 13)
            before = {p.relative_to(project): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()}
            self.assertEqual(app.initialize(project, "空项目"), 0)
            self.assertEqual(before, {p.relative_to(project): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()})
            self.assertEqual((project / ".agents/skills/project-interface/SKILL.md").read_bytes(), (project / ".claude/skills/project-interface/SKILL.md").read_bytes())
            manifest = project / "project.manifest.json"
            manifest.write_text(app.encode(self.example), encoding="utf-8")
            command = [sys.executable, str(project / ".bootstrap/bootstrap.py")]
            output = project / "docs/project/map.html"
            for args in (["map", str(manifest), "--output", str(output)], ["validate", str(manifest), "--map", str(output)]):
                result = subprocess.run(command + args, cwd=temp, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            app.validate_map(self.example, output)

    def test_conflict_preflight_and_missing_renderer_leave_no_files(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "existing"
            project.mkdir()
            (project / "AGENTS.md").write_text("人的规则", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "冲突"):
                app.initialize(project, "test")
            self.assertEqual([p.name for p in project.iterdir()], ["AGENTS.md"])
            fresh = Path(temp) / "fresh"
            with self.assertRaisesRegex(ValueError, "archify"):
                app.initialize(fresh, "test", str(Path(temp) / "missing"))
            self.assertFalse(fresh.exists())
            blocked = Path(temp) / "blocked"
            blocked.mkdir()
            (blocked / "docs").write_text("文件不是目录")
            with self.assertRaisesRegex(ValueError, "应为目录"):
                app.initialize(blocked, "test")
            self.assertFalse((blocked / "AGENTS.md").exists())
            late = Path(temp) / "late-conflict"
            existing = late / ".claude/skills/project-interface/SKILL.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("已有项目 skill", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "冲突"):
                app.initialize(late, "test")
            self.assertFalse((late / "AGENTS.md").exists())
            self.assertEqual(existing.read_text(encoding="utf-8"), "已有项目 skill")

    def test_failed_render_preserves_old_map(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "map.html"
            target.write_bytes(b"existing")
            with patch.object(app, "render_diagrams", side_effect=ValueError("failed")):
                with self.assertRaises(ValueError):
                    app.write_map(self.example, target)
            self.assertEqual(target.read_bytes(), b"existing")

    def test_deployment_modes_cli_persist_without_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="deployment-modes-") as temp:
            for option, expected in (([], "Local-first"), (["--deployment-mode", "Local-first"], "Local-first"),
                                     (["--deployment-mode", "Production-direct"], "Production-direct")):
                with self.subTest(option=option):
                    project = Path(temp) / str(len(list(Path(temp).iterdir())))
                    command = [sys.executable, "-X", "utf8", str(app.BASE / "bootstrap.py"), "init", str(project)]
                    result = subprocess.run(command + option, input="", capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
                    template = (app.BASE / "templates/AGENTS.md").read_text(encoding="utf-8")
                    self.assertEqual(agents, template.replace("@@DEPLOYMENT_MODE@@", expected))
                    self.assertIn(f"Deployment Mode: {expected}\n", agents)
                    self.assertNotIn("@@DEPLOYMENT_MODE@@", agents)
                    rules = (project / "docs/project/rules.md").read_text(encoding="utf-8")
                    self.assertIn("Deployment Check", rules)
                    self.assertIn("Build", rules)
                    app.validate_map(app.read_json(project / "project.manifest.json"), project / "docs/project/map.html")
                    before = {p.relative_to(project): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()}
                    # Existing Production-direct must survive a later init without a mode flag.
                    with patch("builtins.input", side_effect=AssertionError("不得重新询问已有模式")):
                        self.assertEqual(app.initialize(project, "新项目", interactive=True), 0)
                    other = "Local-first" if expected == "Production-direct" else "Production-direct"
                    conflict = subprocess.run(command + ["--deployment-mode", other], input="", capture_output=True, text=True, encoding="utf-8")
                    self.assertNotEqual(conflict.returncode, 0)
                    self.assertIn("冲突", conflict.stderr)
                    self.assertEqual(before, {p.relative_to(project): (p.read_bytes(), p.stat().st_mtime_ns) for p in project.rglob("*") if p.is_file()})
            invalid = Path(temp) / "invalid"
            result = subprocess.run([sys.executable, str(app.BASE / "bootstrap.py"), "init", str(invalid),
                                     "--deployment-mode", "unknown"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(invalid.exists())

    def test_deployment_mode_interactive_cli(self):
        with tempfile.TemporaryDirectory(prefix="deployment-choice-") as temp:
            for index, (choice, expected) in enumerate((("", "Local-first"), ("1", "Local-first"), ("2", "Production-direct"))):
                project = Path(temp) / str(index)
                with self.subTest(choice=choice), patch.object(sys, "argv", ["bootstrap.py", "init", str(project)]), \
                        patch.object(sys.stdin, "isatty", return_value=True), patch("builtins.input", return_value=choice) as prompt, \
                        patch("builtins.print"):
                    self.assertEqual(app.main(), 0)
                    prompt.assert_called_once()
                    self.assertIn(f"Deployment Mode: {expected}\n", (project / "AGENTS.md").read_text(encoding="utf-8"))
            invalid = Path(temp) / "invalid"
            with patch("builtins.input", return_value="typo"), patch("builtins.print"), self.assertRaisesRegex(ValueError, "无效 Deployment Mode"):
                app.initialize(invalid, "test", interactive=True)
            self.assertFalse(invalid.exists())
            with patch("builtins.input", side_effect=EOFError), patch("builtins.print"), self.assertRaisesRegex(ValueError, "选择未完成"):
                app.initialize(invalid, "test", interactive=True)
            self.assertFalse(invalid.exists())

    def test_symlink_cannot_redirect_initialization(self):
        with tempfile.TemporaryDirectory() as temp:
            outside, project = Path(temp) / "outside", Path(temp) / "project"
            outside.mkdir()
            project.mkdir()
            try:
                (project / "docs").symlink_to(outside, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    raise
                subprocess.run(["cmd", "/c", "mklink", "/J", str(project / "docs"), str(outside)], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, "链接或 junction"):
                app.initialize(project, "test")
            self.assertEqual(list(outside.iterdir()), [])

    def test_long_workflows_preserve_every_transition(self):
        manifest = app.starter("长流程")
        for i in range(6):
            node = copy.deepcopy(manifest["nodes"][1])
            node.update(id=f"NODE:step-{i}", name=f"步骤 {i}")
            previous = manifest["workflows"][0]["steps"][-1]
            manifest["nodes"].append(node)
            manifest["relationships"].extend([
                {"from": "NODE:product", "to": node["id"], "kind": "contains", "label": "入口"},
                {"from": previous, "to": node["id"], "kind": "precedes", "label": "下一步"}])
            manifest["workflows"][0]["steps"].append(node["id"])
        app.validate_manifest(manifest)
        specs = app.diagram_specs(manifest)
        edges = [(e["from"], e["to"]) for spec in specs for e in spec["edges"]]
        sequence = ["product"] + [key[5:] for key in manifest["workflows"][0]["steps"]]
        self.assertEqual(edges, list(zip(sequence, sequence[1:])))

    def test_untrusted_labels_are_inert(self):
        manifest = copy.deepcopy(self.example)
        manifest["nodes"][0]["name"] = '</script><img src="https://invalid.test" onerror="alert(1)">@@HASH@@'
        page = app.map_document(manifest, self.diagrams)
        self.assertNotIn('<img src="https://invalid.test"', page)
        self.assertIn("&lt;/script&gt;", page)
        self.assertIn("\\u003c/script\\u003e", page)


if __name__ == "__main__":
    unittest.main()
