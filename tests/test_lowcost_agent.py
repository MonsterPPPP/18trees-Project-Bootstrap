"""Synthetic boundary tests; real DSH acceptance is recorded separately."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import bootstrap as app
import lowcost_agent as agent
from test_local_only import repository


def events(stop="end_turn", output="BOOTSTRAP_DSH_OK", exit_code=0, response_id=1):
    frames = [
        {"id": 1, "method": "session/prompt"},
        {"method": "session/update", "params": {"update": {
            "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": output}}}},
        {"id": response_id, "result": {"stopReason": stop}},
    ]
    return subprocess.CompletedProcess([], exit_code, "\n".join(map(json.dumps, frames)), "secret stderr")


class LowCostAgentTests(unittest.TestCase):
    def test_unknown_and_skip_never_probe_or_install_and_persist_answer(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(agent, "npm_entry") as launcher:
            root = Path(temp)
            home = root / "machine"
            self.assertEqual(agent.configure(root, home=home)["status"], "choice-required")
            self.assertFalse(home.exists())
            self.assertEqual(agent.configure(root, "skip", home=home)["status"], "skipped")
            self.assertEqual(agent.configure(root, home=home)["status"], "skipped")
            launcher.assert_not_called()

    def test_real_completion_required_not_partial_cancel_permission_or_unrelated_result(self):
        self.assertTrue(agent.prompt_result(events())["ok"])
        for result in (events("cancelled"), events("max_tokens"), events(exit_code=5),
                       events(response_id=99), subprocess.CompletedProcess([], 0, '{"text":"done"}', "")):
            with self.subTest(result=result):
                report = agent.prompt_result(result)
                self.assertFalse(report["ok"])
                self.assertEqual(report["text"], "")
                self.assertNotIn("secret", json.dumps(report))

    def test_missing_dsh_is_resumable_and_never_claims_ready(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(agent, "npm_entry", side_effect=ValueError("DSH_MISSING")):
            home = Path(temp) / "machine"
            report = agent.configure(temp, "enable", True, home)
            self.assertFalse(report["ok"])
            self.assertEqual(agent.load(home / "bootstrap-dsh.json")["choice"], "enable")
            self.assertEqual(agent.load(home / "bootstrap-dsh.json")["status"], "unavailable")

    def test_native_tool_failure_cannot_claim_success_even_with_end_turn(self):
        result = events()
        result.stdout += '\n' + json.dumps({"method": "session/update", "params": {"update": {
            "sessionUpdate": "tool_call_update", "toolCallId": "synthetic-denied", "status": "failed"}}})
        report = agent.prompt_result(result)
        self.assertFalse(report["ok"])
        self.assertEqual(report["error"], "ACP_TOOL_FAILED")
        self.assertEqual(report["toolFailures"], 1)

    def test_fresh_then_other_project_reuses_without_install_or_paid_smoke(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "machine"
            first, second = Path(temp) / "first project", Path(temp) / "second project"
            first.mkdir(); second.mkdir()
            config_path = home / "config.json"
            original = {"auth": {"synthetic": "not-a-real-key"}, "agents": {"other": {"argv": ["other"]}},
                        "defaultPermissions": "approve-all"}
            agent.save(config_path, original)
            def entry(name, *_):
                return ["node", str(Path(temp) / (name + ".js"))]
            def version(argv, _):
                return "24.12.0" if len(argv) == 1 else "0.19.4"
            with patch.object(agent, "npm_entry", side_effect=entry), patch.object(agent, "version", side_effect=version), \
                 patch.object(agent, "probe", return_value={"ok": True, "protocolVersion": 1, "agentCapabilities": {}}) as probe, \
                 patch.object(agent, "invoke", return_value={"ok": True, "text": "BOOTSTRAP_DSH_OK", "stopReason": "end_turn"}) as smoke, \
                 patch.object(agent, "acpx_install") as install:
                self.assertFalse(agent.configure(first, "enable", True, home)["reused"])
                self.assertTrue(agent.configure(second, home=home)["reused"])
                self.assertEqual(probe.call_args.args[2], second)
                self.assertFalse(probe.call_args.kwargs["inspect"])
                smoke.assert_called_once()
                install.assert_not_called()
                config = agent.load(config_path)
                self.assertEqual(config["auth"], original["auth"])
                self.assertEqual(config["defaultPermissions"], "approve-all")
                self.assertEqual(config["agents"]["other"], original["agents"]["other"])
                # Existing foreign registration must never be silently replaced.
                config["agents"][agent.AGENT] = {"argv": ["foreign"]}
                agent.save(config_path, config)
                self.assertEqual(agent.configure(second, home=home)["error"], "ACPX_AGENT_REGISTRATION_CONFLICT")
                self.assertEqual(agent.load(config_path), config)

    def test_auth_failure_then_resume_and_version_change_triggers_deeper_check(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "machine"
            with patch.object(agent, "npm_entry", return_value=["node", "/synthetic/cli.js"]), \
                 patch.object(agent, "version", return_value="24.12.0") as version, \
                 patch.object(agent, "probe", return_value={"ok": True, "protocolVersion": 1, "agentCapabilities": {}}) as probe, \
                 patch.object(agent, "invoke", return_value={"ok": False}) as smoke:
                self.assertFalse(agent.configure(temp, "enable", home=home)["ok"])
                smoke.return_value = {"ok": True, "text": "BOOTSTRAP_DSH_OK", "stopReason": "end_turn"}
                self.assertTrue(agent.configure(temp, home=home)["ok"])
                version.return_value = "24.13.0"
                self.assertFalse(agent.configure(temp, home=home)["reused"])
                self.assertTrue(probe.call_args.kwargs["inspect"])
                self.assertEqual(smoke.call_count, 3)

    def test_invocation_forces_deny_no_extra_mcp_and_literal_cwd_stdin(self):
        with patch.object(agent, "process", return_value=events()) as process:
            cwd = Path("project with spaces")
            report = agent.invoke(["node", "acpx path/cli.js"], cwd, "synthetic $() ` text")
            self.assertTrue(report["ok"])
            argv = process.call_args.args[0]
            self.assertIn("--deny-all", argv)
            self.assertIn('{"defaultAction":"deny"}', argv)
            self.assertIn("--mcp-config", argv)
            self.assertEqual(argv[argv.index("--cwd") + 1], str(cwd))
            self.assertEqual(process.call_args.kwargs["stdin"], "synthetic $() ` text")

    def test_distribution_contains_rules_tools_and_official_reference_in_both_modes(self):
        for files, prefix in ((app.install_files(), ".bootstrap/"), (app.local_sources(), "")):
            for name in ("lowcost_agent.py", "agent_probe.mjs", "low-cost-agent.md"):
                self.assertTrue(files[prefix + name].is_file())
        template = (app.BASE / "templates/AGENTS.md").read_text(encoding="utf-8")
        local = app.local_text(template)
        self.assertIn(".bootstrap/low-cost-agent.md", template)
        self.assertIn(".project-bootstrap/low-cost-agent.md", local)
        self.assertIn("此为偏好", template)

    def test_old_local_bundle_can_still_verify_and_repeat_without_forced_upgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "old synthetic project"
            repository(root)
            app.initialize(root, "合成旧安装")
            home = root / app.LOCAL_HOME
            state = app.read_json(home / "install-state.json")
            state.pop("low_cost_agent_bundle")
            agent.save(home / "install-state.json", state)
            for name in ("lowcost_agent.py", "agent_probe.mjs", "low-cost-agent.md"):
                (home / name).unlink()
            before = (home / "AGENTS.md").read_bytes()
            app.verify_install(root)
            self.assertEqual(app.initialize(root, "合成旧安装"), 0)
            self.assertEqual((home / "AGENTS.md").read_bytes(), before)
            self.assertFalse((home / "lowcost_agent.py").exists())
