"""Optional Bootstrap integration using acpx's own CLI, config and runtime."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

AGENT = "bootstrap-dsh"
CHOICES = ("enable", "skip")
PATCH = """# Bootstrap's read-only delegation profile; no permission expansion.
- id: sandbox-policy
  config:
    mode: read-only
    workspaceRoot: !!js process.cwd()
- id: approval
  config:
    policy: ask
- id: permission
  config:
    defaultPreset: read-only
    presets:
      read-only:
        sandbox: read-only
        approval: ask
"""


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    # Keep secrets in an existing acpx config private and preserve its file mode.
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".bootstrap-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
        if path.exists():
            shutil.copymode(path, name)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def npm_entry(command, package, entry):
    """Resolve installed npm launchers without shell quoting/batch interpolation."""
    executable = shutil.which(command)
    if executable:
        executable = Path(executable).resolve()
        candidates = [executable.parent / "node_modules" / package / entry,
                      executable.parent.parent / "lib/node_modules" / package / entry]
        if executable.suffix in (".js", ".mjs"):
            candidates.insert(0, executable)
        for candidate in candidates:
            if candidate.is_file():
                node = shutil.which("node")
                if not node:
                    raise ValueError("NODE_MISSING")
                return [node, str(candidate.resolve())]
        if os.name != "nt" or executable.suffix == ".exe":
            return [str(executable)]
    raise ValueError(command.upper() + "_MISSING_OR_LAUNCHER_UNRESOLVED")


def process(argv, cwd, *, stdin=None, timeout=35):
    env = dict(os.environ, DSH_PERMISSION_MODE="read-only")
    # Never print subprocess stderr; DSH startup/provider errors can expose secrets.
    return subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=timeout, env=env)


def version(argv, cwd):
    result = process([*argv, "--version"], cwd)
    text = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"v?\d+\.\d+\.\d+[\w.+-]*", text):
        raise ValueError("VERSION_CHECK_FAILED")
    return text


def acpx_install(cwd):
    # Only acpx is installed; no DSH upgrade, login or project dependency changes.
    npm = npm_entry("npm", "npm", "bin/npm-cli.js")
    result = process([*npm, "install", "-g", "acpx@latest"], cwd, timeout=180)
    if result.returncode:
        raise ValueError("ACPX_INSTALL_FAILED")
    return npm_entry("acpx", "acpx", "dist/cli.js")


def fingerprint(argv, versions):
    stamps = []
    dsh_home = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh"))
    for path in [dsh_home / "settings.yaml", dsh_home / ".credentials.yaml",
                 dsh_home / "cordis.patch.yml", dsh_home / "profiles/acp/package.json",
                 dsh_home / "profiles/acp/cordis.patch.yml"]:
        if path.is_file():
            stat = path.stat()
            stamps.append((str(path), stat.st_mtime_ns, stat.st_size))
    for arg in argv:
        path = Path(arg)
        if path.is_file():
            stat = path.stat()
            stamps.append((arg, stat.st_mtime_ns, stat.st_size))
    return hashlib.sha256(json.dumps([argv, versions, stamps]).encode()).hexdigest()


def probe(acpx, argv, cwd, inspect):
    if len(acpx) != 2:
        raise ValueError("ACPX_RUNTIME_UNRESOLVED")
    runtime = Path(acpx[1]).with_name("runtime.js")
    request = dict(runtime=str(runtime), argv=argv, cwd=str(cwd), inspect=inspect)
    result = process([acpx[0], str(Path(__file__).with_name("agent_probe.mjs"))], cwd,
                     stdin=json.dumps(request), timeout=60)
    try:
        report = json.loads(result.stdout)
    except ValueError:
        raise ValueError("ACP_PROBE_FAILED") from None
    if result.returncode or not report.get("ok"):
        raise ValueError("ACP_PROBE_FAILED")
    return report


def prompt_result(result):
    """A final assistant string alone is not proof that a turn completed."""
    submitted, completions, text, failed_tools = set(), [], [], set()
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("method") == "session/prompt" and event.get("id") is not None:
            submitted.add(event.get("id"))
        if "error" in event:
            return {"ok": False, "error": "ACP_TASK_FAILED", "exitCode": result.returncode}
        update = event.get("params", {}).get("update", {})
        if update.get("sessionUpdate") in ("tool_call", "tool_call_update") and update.get("status") == "failed":
            failed_tools.add(update.get("toolCallId", "unknown"))
        if update.get("sessionUpdate") == "agent_message_chunk":
            content = update.get("content", {})
            if content.get("type") == "text":
                text.append(content.get("text", ""))
        response = event.get("result", {})
        if isinstance(response, dict) and "stopReason" in response and event.get("id") in submitted:
            completions.append(response["stopReason"])
    stop = completions[-1] if completions else None
    ok = result.returncode == 0 and stop == "end_turn" and not failed_tools
    return {"ok": ok, "exitCode": result.returncode, "stopReason": stop,
            "text": "".join(text).strip() if ok else "", "toolFailures": len(failed_tools),
            "error": None if ok else "ACP_TOOL_FAILED" if failed_tools else "ACP_TASK_INCOMPLETE"}


def invoke(acpx, cwd, text, session=None, state_path=None):
    # CLI flags override potentially permissive global/project defaults.
    args = [*acpx, "--cwd", str(cwd), "--format", "json", "--json-strict",
            "--deny-all", "--permission-policy", '{"defaultAction":"deny"}',
            "--non-interactive-permissions", "fail", "--no-fs", "--no-terminal",
            "--timeout", "90", "--prompt-retries", "0", "--mcp-config",
            str(state_path or Path.home() / ".acpx/bootstrap-dsh.json"), AGENT]
    if session:
        ensure = process([*args, "sessions", "ensure", "--name", session], cwd, timeout=60)
        if ensure.returncode:
            return {"ok": False, "error": "SESSION_ENSURE_FAILED"}
        args += ["prompt", "--session", session]
    else:
        args += ["exec"]
    return prompt_result(process([*args, "--file", "-"], cwd, stdin=text, timeout=110))


def configure(cwd, choice=None, install=False, home=None):
    """Choice/progress is machine-local; project rules contain no machine paths."""
    cwd = Path(cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError("PROJECT_CWD_MUST_BE_DIRECTORY")
    home = Path(home) if home else Path.home() / ".acpx"
    state_path, config_path = home / "bootstrap-dsh.json", home / "config.json"
    try:
        state = load(state_path)
    except (ValueError, OSError):
        return {"ok": False, "status": "unavailable", "error": "MACHINE_STATE_INVALID"}
    if not isinstance(state, dict):
        return {"ok": False, "status": "unavailable", "error": "MACHINE_STATE_INVALID"}
    choice = choice or state.get("choice")
    if choice is None:
        return {"ok": False, "status": "choice-required",
                "next": "在 Agent 对话框询问是否启用低成本 DSH 子 Agent；跳过后继续常规初始化。"}
    if choice not in CHOICES:
        raise ValueError("INVALID_AGENT_CHOICE")
    if choice == "skip":
        save(state_path, {"choice": "skip", "status": "skipped"})
        return {"ok": True, "status": "skipped"}
    previous = dict(state)
    state.update(choice="enable", status="checking", mcpServers=[])
    save(state_path, state)  # Credential/login failures remain resumable.
    try:
        dsh = npm_entry("dsh", "@deepseek-ai/dsh", "lib/bin.js")
        try:
            acpx = npm_entry("acpx", "acpx", "dist/cli.js")
        except ValueError:
            if not install:
                raise ValueError("ACPX_MISSING_RUN_SETUP_WITH_INSTALL") from None
            acpx = acpx_install(cwd)
        versions = {"dsh": version(dsh, cwd), "acpx": version(acpx, cwd),
                    "node": version([shutil.which("node")], cwd)}
        node_parts = tuple(map(int, versions["node"].lstrip("v").split(".")[:2]))
        if node_parts < (22, 13):
            raise ValueError("NODE_VERSION_REQUIRES_ACPX_SUPPORTED_RUNTIME")
        patch_path = home / "bootstrap-dsh-read-only.yml"
        if patch_path.exists() and patch_path.read_text(encoding="utf-8") != PATCH:
            raise ValueError("READ_ONLY_PATCH_CONFLICT")
        config = load(config_path)
        argv = [*dsh, "--profile", "acp", "--patch", str(patch_path)]
        registered = config.get("agents", {}).get(AGENT)
        if registered is not None and registered != {"argv": argv}:
            # Only refresh a previously owned registration when its launch changed.
            if registered != {"argv": previous.get("argv")}:
                raise ValueError("ACPX_AGENT_REGISTRATION_CONFLICT")
        if not patch_path.exists():
            save(patch_path, PATCH)
        if registered != {"argv": argv}:
            config.setdefault("agents", {})[AGENT] = {"argv": argv}
            save(config_path, config)
        # acpx project configuration replaces whole same-name agent entries.
        project = load(cwd / ".acpxrc.json")
        if AGENT in project.get("agents", {}) and project["agents"][AGENT] != {"argv": argv}:
            raise ValueError("PROJECT_AGENT_SHADOWS_MACHINE_CONFIG")
        state.update(argv=argv, versions=versions)
        stamp = fingerprint(argv, versions)
        reusable = (previous.get("status") == "ready" and previous.get("fingerprint") == stamp
                    and previous.get("smoke", {}).get("ok") is True
                    and isinstance(previous.get("capabilities", {}).get("agentCapabilities"), dict))
        report = probe(acpx, argv, cwd, inspect=not reusable)
        if not reusable:
            state["capabilities"] = report
            if not report.get("protocolVersion") or not isinstance(report.get("agentCapabilities"), dict):
                raise ValueError("ACP_CAPABILITIES_MISSING")
            # Synthetic text only; no file, shell, network or other tool action requested.
            save(state_path, state)
            result = invoke(acpx, cwd, "Do not use any tools. Reply with exactly BOOTSTRAP_DSH_OK and nothing else.", state_path=state_path)
            if not result["ok"] or result["text"] != "BOOTSTRAP_DSH_OK":
                raise ValueError("SMOKE_FAILED_CHECK_DSH_AUTH_OR_PROVIDER")
            state["smoke"] = {"ok": True, "stopReason": result["stopReason"]}
        state.update(status="ready", fingerprint=fingerprint(argv, versions))
        state.pop("error", None)
        save(state_path, state)
        return {"ok": True, "status": "ready", "reused": reusable, "versions": versions,
                "handshake": True, "smoke": state.get("smoke"),
                "capabilities": state.get("capabilities"), "cwd": str(cwd)}
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "LOCAL_AGENT_CHECK_FAILED"
        state.update(status="unavailable", error=code)
        save(state_path, state)
        return {"ok": False, "status": "unavailable", "error": code,
                "next": "主 Agent 继续无关工作；检查本机 DSH ACP 启动与原生认证后重跑 agent setup，不创建凭据、不放宽权限。"}


def run(cwd, text, session=None):
    report = configure(cwd)
    if not report.get("ok") or report.get("status") != "ready":
        return report
    state_path = Path.home() / ".acpx/bootstrap-dsh.json"
    try:
        result = invoke(npm_entry("acpx", "acpx", "dist/cli.js"), Path(cwd).resolve(), text, session)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        result = {"ok": False, "error": "ACP_TASK_FAILED_OR_TIMEOUT"}
    if not result["ok"]:
        state = load(state_path)
        state.update(status="unavailable", error=result["error"])
        save(state_path, state)
    return result
