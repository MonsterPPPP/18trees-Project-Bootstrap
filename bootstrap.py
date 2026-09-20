#!/usr/bin/env python3
"""Semantic Project Bootstrap: init, validate, map. Requires Python 3.10+."""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("缺少 jsonschema；运行 python -m pip install 'jsonschema>=4.23,<5'")

BASE = Path(__file__).resolve().parent
DEPLOYMENT_MODES = ("Local-first", "Production-direct")
BOOTSTRAP_MODES = ("Standard", "Local-only")
LOCAL_SCOPES = ("AGENTS.md", "CLAUDE.md", "project.manifest.json", ".bootstrap",
                "docs/project", ".agents/skills/project-interface", ".claude/skills/project-interface")
LOCAL_DIRS = LOCAL_SCOPES[3:]
EXCLUDE_BLOCK = ("\n# BEGIN Project Bootstrap Local-only\n" + "\n".join("/" + p + ("/" if p in LOCAL_DIRS else "") for p in LOCAL_SCOPES)
                 + "\n# END Project Bootstrap Local-only\n").encode("utf-8")
LAYERS = {"product": "Product", "feature": "Feature / User Flow",
          "capability": "Capability", "system": "System / Technical Layer"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_manifest(manifest):
    schema = read_json(BASE / "schema/semantic-project.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda e: str(e.json_path))
    if errors:
        raise ValueError(f"manifest {errors[0].json_path}: {errors[0].message}")
    nodes = {n["id"]: n for n in manifest["nodes"]}
    if len(nodes) != len(manifest["nodes"]):
        raise ValueError("manifest nodes: NODE ID 重复")
    levels = list(LAYERS)
    products = {n["id"] for n in nodes.values() if n["layer"] == "product"}
    if not products:
        raise ValueError("manifest nodes: 至少需要一个 Product")
    children = {key: set() for key in nodes}
    seen = set()
    for edge in manifest["relationships"]:
        source, target, kind = edge["from"], edge["to"], edge["kind"]
        if source not in nodes or target not in nodes or source == target:
            raise ValueError(f"manifest relationships: 无效端点 {source} → {target}")
        key = source, target, kind
        if key in seen:
            raise ValueError(f"manifest relationships: 重复关系 {key}")
        seen.add(key)
        a, b = nodes[source]["layer"], nodes[target]["layer"]
        if kind == "contains":
            if levels.index(b) != levels.index(a) + 1:
                raise ValueError(f"manifest contains: 必须连接相邻层 {source} → {target}")
            children[source].add(target)
        elif kind == "precedes" and (a != "feature" or b != "feature"):
            raise ValueError("manifest precedes: 只能连接 Feature")
        elif kind == "depends_on" and (a != b or a not in ("capability", "system")):
            raise ValueError("manifest depends_on: 只能连接同层 Capability 或 System")
        elif kind == "data_flow" and (a not in ("capability", "system") or b not in ("capability", "system")):
            raise ValueError("manifest data_flow: 只能连接 Capability / System")
    reachable = set(products)
    for _ in range(3):
        reachable |= {child for parent in list(reachable) for child in children[parent]}
    if reachable != nodes.keys():
        raise ValueError(f"manifest nodes: 未连接到 Product 的节点 {sorted(nodes.keys() - reachable)}")
    for node in nodes.values():
        if node["status"] == "implemented" and node["layer"] != "system":
            if not any(nodes[child]["status"] == "implemented" for child in children[node["id"]]):
                raise ValueError(f"manifest {node['id']}: 已实现节点缺少下一层已实现链路")
    flow_ids, used_features, used_precedes = set(), set(), set()
    for flow in manifest["workflows"]:
        if flow["id"] in flow_ids:
            raise ValueError(f"manifest workflows: ID 重复 {flow['id']}")
        flow_ids.add(flow["id"])
        if flow["product"] not in products:
            raise ValueError(f"manifest {flow['id']}: product 必须引用 Product")
        for step in flow["steps"]:
            if step not in children[flow["product"]]:
                raise ValueError(f"manifest {flow['id']}: {step} 不属于该产品的 Feature")
            used_features.add(step)
        for a, b in zip(flow["steps"], flow["steps"][1:]):
            if (a, b, "precedes") not in seen:
                raise ValueError(f"manifest {flow['id']}: 缺少 precedes {a} → {b}")
            used_precedes.add((a, b, "precedes"))
    features = {n["id"] for n in nodes.values() if n["layer"] == "feature"}
    if features != used_features:
        raise ValueError(f"manifest workflows: 未进入用户流程的 Feature {sorted(features - used_features)}")
    if any(edge[2] == "precedes" and edge not in used_precedes for edge in seen):
        raise ValueError("manifest workflows: precedes 关系必须出现在至少一个流程中")
    return manifest


def starter(name):
    return {
        "$schema": ".bootstrap/schema/semantic-project.schema.json", "schema_version": 1,
        "nodes": [
            {"id": "NODE:product", "layer": "product", "name": name,
             "summary": "待补充产品目标；当前没有已实现业务。", "status": "planned", "metadata": {"references": []}},
            {"id": "NODE:first-flow", "layer": "feature", "name": "待定义用户流程",
             "summary": "填写用户任务与成功标准后再实施。", "status": "planned", "metadata": {"references": []}}
        ],
        "relationships": [{"from": "NODE:product", "to": "NODE:first-flow", "kind": "contains", "label": "规划用户流程"}],
        "workflows": [{"id": "FLOW:first", "name": "首个用户流程（规划中）", "product": "NODE:product", "steps": ["NODE:first-flow"]}]
    }


def diagram_specs(manifest):
    """Three nodes per page, overlapping endpoints preserve every workflow edge."""
    nodes = {n["id"]: n for n in manifest["nodes"]}
    flows = list(manifest["workflows"])
    represented = {f["product"] for f in flows}
    for node in nodes.values():
        if node["layer"] == "product" and node["id"] not in represented:
            flows.append({"id": "FLOW:" + node["id"][5:], "name": node["name"], "product": node["id"], "steps": []})
    specs = []
    for flow in flows:
        sequence = [flow["product"], *flow["steps"]]
        for start in range(0, max(1, len(sequence) - 1), 2):
            page = sequence[start:start + 3]
            spec = {
                "schema_version": 1, "diagram_type": "workflow",
                "meta": {"title": "Product / Feature Workflow · " + flow["name"], "quality_profile": "showcase"},
                "lanes": [{"id": "journey", "label": "产品与用户流程"}],
                "nodes": [{"id": key[5:], "lane": "journey", "col": i * 2, "type": "frontend",
                           "label": nodes[key]["name"], "sublabel": "产品" if nodes[key]["layer"] == "product" else "用户流程",
                           "tag": "规划中" if nodes[key]["status"] == "planned" else "已实现"} for i, key in enumerate(page)],
                "edges": [{"from": a[5:], "to": b[5:]} for a, b in zip(page, page[1:])]
            }
            if len(page) > 1:
                spec["mainPath"] = [key[5:] for key in page]
            specs.append(spec)
    return specs


def archify_cli(explicit=None):
    candidates = []
    if explicit or os.environ.get("ARCHIFY_HOME"):
        candidates.append(Path(explicit or os.environ["ARCHIFY_HOME"]).expanduser())
    else:
        if os.environ.get("CODEX_HOME"):
            candidates.append(Path(os.environ["CODEX_HOME"]) / "skills/archify")
        for base in (Path.cwd(), Path.home()):
            candidates.extend(base / part for part in (".agents/skills/archify", ".claude/skills/archify", ".codex/skills/archify"))
    for path in candidates:
        cli = path / "bin/archify.mjs" if path.is_dir() else path
        if cli.is_file():
            return cli.resolve()
    raise ValueError("找不到 archify；从 https://github.com/tt-a1i/archify 安装，或传 --archify <skill目录> / 设置 ARCHIFY_HOME")


def render_diagrams(manifest, explicit=None):
    cli = archify_cli(explicit)
    node = shutil.which("node")
    if not node:
        raise ValueError("找不到 Node.js；安装 Node.js 22 或更新版本后重试")
    diagrams = []
    with tempfile.TemporaryDirectory(prefix="project-map-") as temp:
        for i, spec in enumerate(diagram_specs(manifest)):
            source, target = Path(temp) / f"flow-{i}.json", Path(temp) / f"flow-{i}.html"
            source.write_text(encode(spec), encoding="utf-8")
            result = subprocess.run([node, str(cli), "deliver", "workflow", str(source), str(target),
                                     "--quality", "showcase", "--json"], capture_output=True, encoding="utf-8", timeout=120)
            if result.returncode:
                raise ValueError(f"archify 流程第 {i + 1} 页失败；按诊断修改节点名称或布局后重试：\n{result.stdout}\n{result.stderr}")
            receipt = json.loads(result.stdout)
            if receipt.get("validation", {}).get("checksPassed") != 9 or receipt["validation"].get("warnings") != 0:
                raise ValueError("archify 未通过全部 9 项 showcase 检查；请检查版本与诊断")
            artifact = target.read_bytes()
            diagrams.append({"spec": spec, "html": artifact.decode("utf-8"),
                             "receipt": {key: receipt[key] for key in ("specification", "artifact", "validation")}})
    return diagrams


def safe_json(value):
    # JSON is embedded as inert script data; escape HTML parser delimiters.
    return encode(value).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def map_document(manifest, diagrams):
    escape = html.escape
    node_names = {node["id"]: node["name"] for node in manifest["nodes"]}
    products = [node for node in manifest["nodes"] if node["layer"] == "product"]
    title = " / ".join(node["name"] for node in products)
    controls = "".join(f'<option value="{i}">{escape(d["spec"]["meta"]["title"])} · {i + 1}/{len(diagrams)}</option>' for i, d in enumerate(diagrams))
    sections = []
    for layer, label in LAYERS.items():
        cards = []
        for node in manifest["nodes"]:
            if node["layer"] != layer:
                continue
            outgoing = [edge for edge in manifest["relationships"] if edge["from"] == node["id"]]
            links = "".join(f'<p class="relation"><a href="#{escape(e["to"])}">{escape(e["label"])} → {escape(node_names[e["to"]])}</a> <small>{e["kind"]}</small></p>' for e in outgoing)
            refs = escape(json.dumps(node["metadata"], ensure_ascii=False, sort_keys=True, indent=2))
            status = "规划中" if node["status"] == "planned" else "已实现"
            cards.append(f'<article id="{escape(node["id"])}" data-layer="{layer}"><small>{escape(node["id"])} · {status}</small><h3>{escape(node["name"])}</h3><p>{escape(node["summary"])}</p>{links}<details><summary>Agent metadata · 实现线索</summary><pre>{refs}</pre></details></article>')
        sections.append(f'<section id="{layer}"><h2>{label}</h2><div class="cards">{"".join(cards) or "<p>暂无已声明节点；请先核实产品与代码。</p>"}</div></section>')
    payload = safe_json({"manifest": manifest, "diagrams": diagrams})
    template = (BASE / "templates/map.html").read_text(encoding="utf-8")
    substitutions = {"TITLE": escape(title), "CONTROLS": controls, "SECTIONS": "".join(sections),
                     "PAYLOAD": payload, "HASH": digest(encode(manifest).encode("utf-8"))}
    return re.sub(r"@@(TITLE|CONTROLS|SECTIONS|PAYLOAD|HASH)@@", lambda m: substitutions[m[1]], template)


def validate_map(manifest, path):
    document = Path(path).read_text(encoding="utf-8")
    match = re.search(r'<script id="project-data" type="application/json">(.*?)</script>', document, re.S)
    if not match:
        raise ValueError("地图缺少 project-data；请重新生成")
    payload = json.loads(match[1])
    if encode(payload.get("manifest")) != encode(manifest):
        raise ValueError("地图与 manifest 不一致；请运行 map 重新生成")
    diagrams = payload.get("diagrams", [])
    if [d.get("spec") for d in diagrams] != diagram_specs(manifest):
        raise ValueError("地图的 archify 流程与 manifest 不一致；请重新生成")
    for diagram in diagrams:
        receipt = diagram["receipt"]
        for key, data in (("artifact", diagram["html"].encode("utf-8")), ("specification", encode(diagram["spec"]).encode("utf-8"))):
            if receipt[key] != {"sha256": digest(data), "bytes": len(data)}:
                raise ValueError(f"地图 {key} 校验和不一致；请重新生成")
        check = receipt["validation"]
        if check.get("checksPassed") != 9 or check.get("checkCount") != 9 or check.get("errors") != 0 or check.get("warnings") != 0 or check.get("compositionStatus") != "pass":
            raise ValueError("地图缺少通过的 archify showcase 验证")
    if document != map_document(manifest, diagrams):
        raise ValueError("地图页面内容已改变或生成器版本不同；请重新生成")


def write_map(manifest, output, explicit=None):
    output = Path(output)
    content = map_document(manifest, render_diagrams(manifest, explicit))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully rendered and validated artifact.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", suffix=".html", dir=output.parent, delete=False) as tmp:
        temporary = Path(tmp.name)
        tmp.write(content)
    try:
        validate_map(manifest, temporary)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def install_files():
    return {
        "AGENTS.md": BASE / "templates/AGENTS.md",
        "CLAUDE.md": BASE / "templates/CLAUDE.md",
        "docs/project/overview.md": BASE / "templates/overview.md",
        "docs/project/rules.md": BASE / "templates/rules.md",
        "docs/project/usage.md": BASE / "MANUAL.md",
        ".agents/skills/project-interface/SKILL.md": BASE / "skills/project-interface/SKILL.md",
        ".claude/skills/project-interface/SKILL.md": BASE / "skills/project-interface/SKILL.md",
        ".bootstrap/bootstrap.py": BASE / "bootstrap.py",
        ".bootstrap/requirements.txt": BASE / "requirements.txt",
        ".bootstrap/interface-spec.md": BASE / "docs/interface-spec.md",
        ".bootstrap/schema/semantic-project.schema.json": BASE / "schema/semantic-project.schema.json",
        ".bootstrap/templates/map.html": BASE / "templates/map.html"
    }


def check_target(root, relative):
    target = root / relative
    for path in (target, *target.parents):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"初始化冲突：{path} 是链接或 junction；请使用普通目录")
        if path != target and path.exists() and not path.is_dir():
            raise ValueError(f"初始化冲突：{path} 应为目录；请选择空目录")
    if target.exists() and not target.is_file():
        raise ValueError(f"初始化冲突：{target} 应为文件；请选择空目录")
    return target


def local_repository(root, installing=False):
    def git(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, encoding="utf-8")
        if result.returncode:
            raise ValueError("Local-only 需要普通 Git 工作区根目录；请先 git init，或检查仓库路径")
        return result.stdout.strip()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ValueError("Local-only 必须安装到 Git 工作区根目录，不能安装到子目录")
    if installing and sum(record.startswith("worktree ") for record in git("worktree", "list", "--porcelain", "-z").split("\0")) != 1:
        raise ValueError("Local-only 不支持多个 worktree：info/exclude 会影响其他工作区；请使用独立 clone，未修改项目")
    if git("ls-files", "--", *LOCAL_SCOPES):
        raise ValueError("Local-only 冲突：Bootstrap 路径已有被 Git 跟踪或暂存的文件，不能用 exclude 隐藏；未修改项目")
    exclude = Path(git("rev-parse", "--path-format=absolute", "--git-path", "info/exclude"))
    check_target(exclude.parent, exclude.name)
    return exclude


def local_contents(root):
    """Check every owned path before cleanup; do not follow links outside the project."""
    files, directories = [], []
    for relative in LOCAL_SCOPES:
        path = root / relative
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink() or (hasattr(ancestor, "is_junction") and ancestor.is_junction()):
                raise ValueError(f"Local-only 路径包含链接或 junction：{ancestor}；请先移走链接")
        if path.is_dir():
            for folder, dirnames, filenames in os.walk(path, followlinks=False):
                for entry in [Path(folder) / name for name in dirnames + filenames]:
                    if entry.is_symlink() or (hasattr(entry, "is_junction") and entry.is_junction()):
                        raise ValueError(f"Local-only 路径包含链接或 junction：{entry}；请先移走链接")
                directories.append(Path(folder))
                files.extend(Path(folder) / name for name in filenames)
        elif path.exists():
            files.append(path)
    return files, directories


def deinitialize_legacy(target, yes=False):
    root = Path(os.path.abspath(target))
    state_path = check_target(root, ".bootstrap/install-state.json")
    if not state_path.is_file():
        raise ValueError("找不到 Local-only 安装记录；未删除文件。Standard 或旧版安装不支持此清理")
    state = read_json(state_path)
    if state.get("bootstrap_mode") != "Local-only":
        raise ValueError("安装记录不是 Local-only；未删除文件")
    exclude = local_repository(root)
    before = exclude.read_bytes() if exclude.exists() else b""
    if before.count(EXCLUDE_BLOCK) != 1:
        raise ValueError("Local-only exclude 区块缺失或重复；请先恢复区块，未删除文件")
    files, directories = local_contents(root)
    # State may remember only ancestors of our fixed reserved scopes, never arbitrary paths.
    allowed_dirs = {p.as_posix() for scope in LOCAL_SCOPES for p in Path(scope).parents if str(p) != "."} | set(LOCAL_DIRS)
    prior_dirs = state.get("preexisting_dirs")
    if not isinstance(prior_dirs, list) or not all(p in allowed_dirs for p in prior_dirs):
        raise ValueError("Local-only 安装记录目录无效；未删除文件")
    print("清理范围：" + "、".join(LOCAL_SCOPES))
    print(f"将删除 {len(files)} 个本地 Bootstrap 文件（含后续修改及生成产物），并移除自身 exclude 区块；任务文件不在清理范围内")
    if not yes:
        print("当前仅预览。确认已备份需要保留的本地规则后，加 --yes 执行清理")
        return 0
    for path in files:
        if path != state_path:
            path.unlink()
    after = before.replace(EXCLUDE_BLOCK, b"", 1)
    if after or state.get("exclude_existed", True):
        exclude.write_bytes(after)
    else:
        exclude.unlink()
    state_path.unlink()
    candidates = set(directories) | {root / p for p in allowed_dirs}
    for path in sorted(candidates, key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and path.relative_to(root).as_posix() not in prior_dirs and not any(path.iterdir()):
            path.rmdir()
    print("Local-only 已清理；保留原有目录、其他 exclude 内容与真实任务文件")
    return len(files)


LOCAL_HOME = ".project-bootstrap"
ENTRY_NAMES = ("AGENTS.override.md", "CLAUDE.local.md")
LOCAL_PATHS = (LOCAL_HOME, *ENTRY_NAMES)
ENTRY_BLOCKS = {
    "AGENTS.override.md": ("\n<!-- BEGIN Project Bootstrap -->\n"
        "先读取本项目原有 AGENTS.md（若存在），保留其全部规则；再读取 .project-bootstrap/AGENTS.md 与其中指向的项目 skill。\n"
        "规则冲突不得静默覆盖；需要人裁决时说明具体冲突。\n<!-- END Project Bootstrap -->\n").encode("utf-8"),
    "CLAUDE.local.md": ("\n<!-- BEGIN Project Bootstrap -->\n"
        "保留原项目 CLAUDE.md / AGENTS.md 的规则；若存在 AGENTS.md，先读取。\n"
        "@.project-bootstrap/AGENTS.md\n"
        "读取上述入口指向的项目 skill；规则冲突不得静默覆盖。\n<!-- END Project Bootstrap -->\n").encode("utf-8"),
}


def git_output(root, *args, optional=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, encoding="utf-8")
    if result.returncode and not (optional and result.returncode == 1):
        raise ValueError(f"Git 检查失败：{result.stderr.strip()}")
    return result.stdout


def local_git(root):
    if Path(git_output(root, "rev-parse", "--show-toplevel").strip()).resolve() != root.resolve():
        raise ValueError("Local-only 必须安装到 Git 工作区根目录")
    gitdir = Path(git_output(root, "rev-parse", "--absolute-git-dir").strip())
    common = Path(git_output(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    config = check_target(common, "config")
    # Exact gitdir condition: no shared exclude, no global config or worktree extension.
    pattern = gitdir.as_posix()
    for char in ("[", "*", "?"):
        if char in pattern:
            raise ValueError("Git directory 含 glob 字符，不能安全绑定排除规则；请使用普通路径")
    if any(c in pattern for c in '\n\r"'):
        raise ValueError("Git directory 含不支持的字符；未修改项目")
    include = (root / LOCAL_HOME / "git.config").as_posix()
    if "\n" in include or "\r" in include:
        raise ValueError("项目路径含换行，不能安全记录安装区块")
    condition = "gitdir/i" if os.name == "nt" else "gitdir"
    block = (f'\n# BEGIN Project Bootstrap {include}\n'
             f'[includeIf "{condition}:{pattern}"]\n'
             f'\tpath = {json.dumps(include, ensure_ascii=False)}\n'
             f'# END Project Bootstrap {include}\n').encode("utf-8")
    return config, block


def check_local_paths(root):
    if git_output(root, "ls-files", "--", *LOCAL_PATHS):
        raise ValueError("Local-only 路径已被跟踪或暂存；不能覆盖规则或改动索引")
    for relative in LOCAL_PATHS:
        path = root / relative
        check_target(root, relative + "/install-state.json" if relative == LOCAL_HOME else relative)
        if path.is_dir():
            for folder, dirs, files in os.walk(path, followlinks=False):
                for name in dirs + files:
                    item = Path(folder) / name
                    if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
                        raise ValueError(f"Local-only 路径包含链接或 junction：{item}")


def inherited_excludes(root):
    """Read effective core.excludesFile without our conditional include's value."""
    values = git_output(root, "config", "--null", "--show-origin", "--path", "--get-all",
                        "core.excludesFile", optional=True).split("\0")
    own = root / LOCAL_HOME / "git.config"
    inherited = None
    for origin, value in zip(values[::2], values[1::2]):
        if origin.startswith("file:") and Path(origin[5:]).resolve() == own.resolve():
            continue
        inherited = value
    if inherited is None:
        source = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "git/ignore"
    elif not inherited:
        return b""
    else:
        source = Path(inherited).expanduser()
        if not source.is_absolute():
            source = root / source
    if source.resolve().is_relative_to((root / LOCAL_HOME).resolve()):
        raise ValueError("继承的排除文件指向 Bootstrap 自身；请恢复原 Git 配置")
    return source.read_bytes() if source.is_file() else b""


def local_exclude_bytes(root):
    return inherited_excludes(root) + b"\n# Project Bootstrap local files\n" + b"\n".join(
        ("/" + p + ("/" if p == LOCAL_HOME else "")).encode("utf-8") for p in LOCAL_PATHS) + b"\n"


def local_sources():
    return {
        "AGENTS.md": BASE / "templates/AGENTS.md",
        "docs/overview.md": BASE / "templates/overview.md",
        "docs/rules.md": BASE / "templates/rules.md",
        "docs/usage.md": BASE / "MANUAL.md",
        "skills/project-interface/SKILL.md": BASE / "skills/project-interface/SKILL.md",
        "bootstrap.py": BASE / "bootstrap.py",
        "requirements.txt": BASE / "requirements.txt",
        "interface-spec.md": BASE / "docs/interface-spec.md",
        "schema/semantic-project.schema.json": BASE / "schema/semantic-project.schema.json",
        "templates/map.html": BASE / "templates/map.html",
    }


def local_text(text):
    # Templates describe root-relative paths; the local bundle owns its own namespace.
    return (text.replace(".project-bootstrap/project.manifest.json", "@@LOCAL_MANIFEST@@")
            .replace("../../.bootstrap/interface-spec.md", "../interface-spec.md")
            .replace(".bootstrap/", LOCAL_HOME + "/")
            .replace("docs/project/", LOCAL_HOME + "/docs/")
            .replace("project.manifest.json", LOCAL_HOME + "/project.manifest.json")
            .replace(".agents/skills/project-interface/", LOCAL_HOME + "/skills/project-interface/")
            .replace(".claude/skills/project-interface/", LOCAL_HOME + "/skills/project-interface/")
            .replace("根目录 `AGENTS.md`", "`.project-bootstrap/AGENTS.md`")
            .replace("@@LOCAL_MANIFEST@@", ".project-bootstrap/project.manifest.json"))


def verify_install(target):
    root = Path(os.path.abspath(target))
    check_local_paths(root)
    home = root / LOCAL_HOME
    state = read_json(home / "install-state.json")
    if state.get("version") != 2 or state.get("bootstrap_mode") != "Local-only":
        raise ValueError("不支持的安装记录；不猜测修复或卸载")
    if set(state.get("entry_existed", {})) != set(ENTRY_NAMES) or not all(
            isinstance(v, bool) for v in state["entry_existed"].values()):
        raise ValueError("入口安装记录无效；未删除文件")
    config, block = local_git(root)
    if config.read_bytes().count(block) != 1:
        raise ValueError("本地 Git 配置区块缺失或重复；请恢复原安装位置或配置")
    for name, entry in ENTRY_BLOCKS.items():
        path = root / name
        if not path.is_file() or path.read_bytes().count(entry) != 1:
            raise ValueError(f"本地入口区块缺失或被修改：{name}；请恢复区块")
    for name in (*local_sources(), "project.manifest.json", "docs/map.html", "git.config", "git.exclude"):
        if not (home / name).is_file():
            raise ValueError(f"本地安装缺少 {name}；请备份后重新安装")
    agents = (home / "AGENTS.md").read_text(encoding="utf-8")
    if not re.search(r"^Bootstrap Mode: Local-only$", agents, re.M) or not re.search(
            r"^Deployment Mode: (Local-first|Production-direct)$", agents, re.M):
        raise ValueError("本地模式配置无效；请恢复 AGENTS.md 中的模式")
    expected_config = local_config(root)
    if (home / "git.config").read_bytes() != expected_config:
        raise ValueError("本地 Git 排除配置被修改；请恢复安装配置")
    exclude = home / "git.exclude"
    before = exclude.read_bytes()
    after = local_exclude_bytes(root)
    try:
        if before != after:
            exclude.write_bytes(after)
        effective = git_output(root, "config", "--path", "--get", "core.excludesFile").strip()
        if Path(effective).resolve() != exclude.resolve():
            raise ValueError("其他 Git 配置覆盖了本地排除；请先解决配置冲突")
        visible = git_output(root, "ls-files", "--others", "--exclude-standard", "--", *LOCAL_PATHS)
        if visible:
            raise ValueError("Bootstrap 仍对 Git 可见：项目 ignore 规则覆盖了本地排除")
        validate_map(validate_manifest(read_json(home / "project.manifest.json")), home / "docs/map.html")
    except Exception:
        if exclude.read_bytes() != before:
            exclude.write_bytes(before)
        raise
    return state


def local_config(root):
    exclude = (root / LOCAL_HOME / "git.exclude").as_posix()
    return f'[core]\n\texcludesFile = {json.dumps(exclude, ensure_ascii=False)}\n'.encode("utf-8")


def initialize_local(root, name, explicit, deployment_mode):
    config, block = local_git(root)
    check_local_paths(root)
    home = root / LOCAL_HOME
    if home.exists():
        if not (home / "install-state.json").is_file():
            raise ValueError("初始化冲突：.project-bootstrap 已存在但没有安装记录")
        verify_install(root)
        if deployment_mode and f"Deployment Mode: {deployment_mode}\n" not in (home / "AGENTS.md").read_text(encoding="utf-8"):
            raise ValueError("初始化冲突：不能通过 init 改变部署模式")
        return 0
    mode = deployment_mode or "Local-first"
    if mode not in DEPLOYMENT_MODES:
        raise ValueError("无效 Deployment Mode")
    entries = {name: (root / name).read_bytes() if (root / name).exists() else None for name in ENTRY_NAMES}
    if any(value is not None and b"<!-- BEGIN Project Bootstrap -->" in value for value in entries.values()):
        raise ValueError("入口已有 Bootstrap 区块但安装记录缺失；请先核实旧安装")
    before_config = config.read_bytes()
    if block in before_config:
        raise ValueError("Git 配置已有本安装区块；请先核实旧安装")
    files = {name: source.read_bytes() for name, source in local_sources().items()}
    for filename in ("AGENTS.md", "docs/overview.md", "docs/rules.md", "skills/project-interface/SKILL.md"):
        files[filename] = local_text(files[filename].decode("utf-8")).replace("@@BOOTSTRAP_MODE@@", "Local-only").replace(
            "@@DEPLOYMENT_MODE@@", mode).encode("utf-8")
    manifest = validate_manifest(starter(name))
    files["project.manifest.json"] = (encode(manifest) + "\n").encode("utf-8")
    files["docs/map.html"] = map_document(manifest, render_diagrams(manifest, explicit)).encode("utf-8")
    files["git.config"] = local_config(root)
    files["git.exclude"] = local_exclude_bytes(root)
    files["install-state.json"] = encode({"version": 2, "bootstrap_mode": "Local-only",
        "entry_existed": {name: value is not None for name, value in entries.items()}}).encode("utf-8")
    changed_entries = []
    home_created = False
    try:
        home.mkdir()
        home_created = True
        # Install exclusion before exposing any entry or bundle file to git add.
        (home / "git.config").write_bytes(files.pop("git.config"))
        (home / "git.exclude").write_bytes(files.pop("git.exclude"))
        if config.read_bytes() != before_config:
            raise ValueError("Git 配置在安装期间发生变化；请串行重试")
        config.write_bytes(before_config + block)
        for relative, data in files.items():
            path = home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for entry, content in entries.items():
            path = root / entry
            if (path.read_bytes() if path.exists() else None) != content:
                raise ValueError(f"入口在安装期间被修改：{entry}")
            path.write_bytes((content or b"") + ENTRY_BLOCKS[entry])
            changed_entries.append(entry)
        verify_install(root)
    except Exception:
        for entry in changed_entries:
            content = (root / entry).read_bytes().replace(ENTRY_BLOCKS[entry], b"", 1)
            if content or entries[entry] is not None:
                (root / entry).write_bytes(content)
            else:
                (root / entry).unlink()
        if block in config.read_bytes():
            config.write_bytes(config.read_bytes().replace(block, b"", 1))
        if home_created:
            shutil.rmtree(home)
        raise
    return len(files) + 2 + len(ENTRY_NAMES)


def deinitialize_local(target, yes=False):
    root = Path(os.path.abspath(target))
    # Cleanup must work even when a changed ignore rule makes verify-install fail.
    check_local_paths(root)
    home = root / LOCAL_HOME
    state = read_json(home / "install-state.json")
    entries = state.get("entry_existed", {})
    if (state.get("version") != 2 or state.get("bootstrap_mode") != "Local-only"
            or set(entries) != set(ENTRY_NAMES) or not all(isinstance(v, bool) for v in entries.values())):
        raise ValueError("安装记录无效；未删除文件")
    config, block = local_git(root)
    if config.read_bytes().count(block) != 1:
        raise ValueError("Git 本地区块缺失或重复；请恢复后清理")
    restored = {}
    for entry in ENTRY_NAMES:
        data = (root / entry).read_bytes()
        if data.count(ENTRY_BLOCKS[entry]) != 1:
            raise ValueError(f"入口区块缺失或被修改：{entry}；请先恢复区块")
        restored[entry] = data.replace(ENTRY_BLOCKS[entry], b"", 1)
    print("将清理 .project-bootstrap/ 全部本地编辑与生成物、两个入口中的 Bootstrap 区块及本 worktree 排除配置；保留原规则和任务改动")
    if not yes:
        print("当前仅预览；先备份需要保留的内容，获确认后加 --yes")
        return 0
    for entry, data in restored.items():
        if data or entries[entry]:
            (root / entry).write_bytes(data)
        else:
            (root / entry).unlink()
    config.write_bytes(config.read_bytes().replace(block, b"", 1))
    shutil.rmtree(home)
    print("本地 Bootstrap 已移除；原规则、其他 worktree 与任务改动保留")
    return 1


def deinitialize(target, yes=False):
    if (Path(target) / LOCAL_HOME).exists():
        return deinitialize_local(target, yes)
    return deinitialize_legacy(target, yes)


def initialize(target, name, explicit=None, deployment_mode=None, interactive=False, bootstrap_mode=None):
    if not (BASE / "templates/AGENTS.md").is_file():
        raise ValueError("init 需要完整 Bootstrap 源仓库；由 Agent 从源仓库执行")
    root = Path(os.path.abspath(target))
    if (root / ".bootstrap/install-state.json").exists():
        raise ValueError("检测到旧版 Local-only；请先备份本地编辑，确认后用旧版 deinit 卸载，再重新安装；不自动迁移")
    agents = check_target(root, "AGENTS.md")
    saved_agents = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    if bootstrap_mode is None:
        bootstrap_mode = "Standard" if (root / ".bootstrap/bootstrap.py").is_file() and re.search(
            r"^Bootstrap Mode: Standard$", saved_agents, re.M) and not (root / LOCAL_HOME).exists() else "Local-only"
    if bootstrap_mode not in BOOTSTRAP_MODES:
        raise ValueError("无效 Bootstrap Mode")
    if bootstrap_mode == "Local-only":
        return initialize_local(root, name, explicit, deployment_mode)
    if (root / LOCAL_HOME).exists():
        raise ValueError("初始化冲突：已有 Local-only；不能用 init 切换模式")
    saved = re.search(r"^Deployment Mode: (Local-first|Production-direct)$", saved_agents, re.M)
    deployment_mode = deployment_mode or (saved[1] if saved else "Local-first")
    if deployment_mode not in DEPLOYMENT_MODES:
        raise ValueError("无效 Deployment Mode")
    manifest = validate_manifest(starter(name))
    files = {relative: source.read_bytes() for relative, source in install_files().items()}
    files["AGENTS.md"] = files["AGENTS.md"].replace(b"@@DEPLOYMENT_MODE@@", deployment_mode.encode("utf-8"))
    files["AGENTS.md"] = files["AGENTS.md"].replace(b"@@BOOTSTRAP_MODE@@", b"Standard")
    for relative, data in files.items():
        path = check_target(root, relative)
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"初始化冲突：{path} 已有不同内容，未写入任何文件")
    files["project.manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = check_target(root, "project.manifest.json")
    if path.exists() and path.read_bytes() != files["project.manifest.json"]:
        raise ValueError("初始化冲突：manifest 已有不同内容")
    map_path = check_target(root, "docs/project/map.html")
    if map_path.exists():
        validate_map(manifest, map_path)
    else:
        files["docs/project/map.html"] = map_document(manifest, render_diagrams(manifest, explicit)).encode("utf-8")
    created = []
    try:
        for relative, data in files.items():
            path = check_target(root, relative)
            if path.exists():
                if path.read_bytes() != data:
                    raise ValueError(f"初始化时文件被修改：{path}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
        validate_map(manifest, map_path)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return len(created)


def main():
    parser = argparse.ArgumentParser(description="按产品与功能协作：初始化、校验、生成离线项目地图")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="无覆盖初始化；相同内容重复执行无操作")
    init.add_argument("target", type=Path)
    init.add_argument("--name", default="新项目")
    init.add_argument("--archify", help="外部 archify skill 目录或 bin/archify.mjs 路径")
    init.add_argument("--deployment-mode", choices=DEPLOYMENT_MODES,
                      help="部署模式：默认 Local-first；显式选择 Production-direct 即给予检查通过后自动部署生产的长期授权")
    init.add_argument("--bootstrap-mode", choices=BOOTSTRAP_MODES,
                      help="默认 Local-only（仅本地）；Standard 需用户明确选择")
    deinit = commands.add_parser("deinit", help="预览 Local-only 清理；加 --yes 删除本地 Bootstrap 与 exclude 区块")
    deinit.add_argument("target", type=Path)
    deinit.add_argument("--yes", action="store_true", help="确认删除全部本地 Bootstrap 产物，含后续编辑")
    verify = commands.add_parser("verify-install", help="核对本地安装、刷新继承排除规则并验证地图")
    verify.add_argument("target", type=Path)
    validate = commands.add_parser("validate", help="校验结构、引用和可选地图一致性")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--map", type=Path)
    render = commands.add_parser("map", help="用 archify 生成自包含离线地图")
    render.add_argument("manifest", type=Path)
    render.add_argument("--output", required=True, type=Path)
    render.add_argument("--archify")
    args = parser.parse_args()
    try:
        if args.command == "init":
            count = initialize(args.target, args.name, args.archify, args.deployment_mode,
                               interactive=sys.stdin.isatty(), bootstrap_mode=args.bootstrap_mode)
            print(f"初始化通过：新增 {count} 个文件。由 Agent 读取协作规则，返回项目使用说明和地图入口")
        elif args.command == "verify-install":
            verify_install(args.target)
            print("本地安装、Git 隔离与地图一致性通过；客户端新会话加载需另行核实")
        elif args.command == "deinit":
            deinitialize(args.target, args.yes)
        else:
            manifest = validate_manifest(read_json(args.manifest))
            if args.command == "map":
                if args.output.resolve() == args.manifest.resolve():
                    raise ValueError("地图输出不能覆盖 manifest；请使用 docs/project/map.html")
                for root in args.manifest.resolve().parents:
                    if root.name == LOCAL_HOME and (root / "install-state.json").is_file():
                        if not args.output.resolve().is_relative_to(root / "docs"):
                            raise ValueError("Local-only 地图必须输出到 .project-bootstrap/docs/，避免进入 Git")
                        check_target(root, str(args.output.absolute().relative_to(root)))
                        break
                    if (root / ".bootstrap/install-state.json").is_file():
                        if not args.output.resolve().is_relative_to(root / "docs/project"):
                            raise ValueError("Local-only 地图必须输出到 docs/project/，避免进入 Git")
                        check_target(root, str(args.output.absolute().relative_to(root)))
                        break
                write_map(manifest, args.output, args.archify)
                print(f"地图已生成：{args.output}。下一步（1 分钟）：离线打开 HTML")
            else:
                if args.map:
                    validate_map(manifest, args.map)
                print("校验通过。下一步（1 分钟）：核对一个语义节点与实际代码证据")
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
