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


def deinitialize(target, yes=False):
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


def initialize(target, name, explicit=None, deployment_mode=None, interactive=False, bootstrap_mode=None):
    if not (BASE / "templates/AGENTS.md").is_file():
        raise ValueError("init 需要完整 Bootstrap 源仓库；请在源仓库运行 python bootstrap.py init <目标目录>。项目内使用 map / validate")
    root = Path(os.path.abspath(target))
    agents = check_target(root, "AGENTS.md")
    saved_agents = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    state_path = check_target(root, ".bootstrap/install-state.json")
    if bootstrap_mode is None:
        saved_mode = re.search(r"^Bootstrap Mode: (Standard|Local-only)$", saved_agents, re.M)
        if saved_mode:
            bootstrap_mode = saved_mode[1]
        elif interactive and not agents.exists():
            try:
                choice = input("Bootstrap Mode：1 = Standard（默认，提交项目）；2 = Local-only（仅本地，不进入 Git）[1]：").strip()
            except EOFError as error:
                raise ValueError("Bootstrap 模式选择未完成；请传 --bootstrap-mode Standard 或 Local-only") from error
            bootstrap_mode = {"": "Standard", "1": "Standard", "2": "Local-only"}.get(choice, choice)
        else:
            bootstrap_mode = "Standard"
    if bootstrap_mode not in BOOTSTRAP_MODES:
        raise ValueError("无效 Bootstrap Mode；请选择 Standard 或 Local-only")
    if state_path.is_file():
        state = read_json(state_path)
        if state.get("bootstrap_mode") != "Local-only" or bootstrap_mode != "Local-only":
            raise ValueError("初始化冲突：已有 Local-only 安装，不能通过 init 切换模式")
        exclude = local_repository(root, installing=True)
        if not exclude.is_file() or exclude.read_bytes().count(EXCLUDE_BLOCK) != 1:
            raise ValueError("Local-only exclude 区块缺失或重复；请恢复后重试")
        if deployment_mode and f"Deployment Mode: {deployment_mode}\n" not in saved_agents:
            raise ValueError("初始化冲突：部署模式不同；请显式编辑 AGENTS.md，不使用 init 切换")
        local_contents(root)
        if "Bootstrap Mode: Local-only\n" not in saved_agents or any(not (root / p).is_file() for p in install_files()):
            raise ValueError("Local-only 安装文件缺失或模式被修改；请先备份，再 deinit / init 重装")
        return 0  # Existing local rules and generated maps are user-owned changes; preserve them.
    exclude = None
    exclude_before = b""
    prior_dirs = []
    if bootstrap_mode == "Local-only":
        exclude = local_repository(root, installing=True)
        local_contents(root)
        for scope in LOCAL_SCOPES:
            path = root / scope
            if path.exists() and (not path.is_dir() or any(path.iterdir())):
                raise ValueError(f"Local-only 初始化冲突：{path} 已存在；本地排除不能隐藏或接管已有项目内容")
            for directory in (path, *path.parents):
                if directory == root:
                    break
                if directory.is_dir():
                    prior_dirs.append(directory.relative_to(root).as_posix())
        exclude_before = exclude.read_bytes() if exclude.exists() else b""
        if b"# BEGIN Project Bootstrap Local-only" in exclude_before:
            raise ValueError("Local-only exclude 区块已存在但安装记录缺失；请先核实旧安装")
    if deployment_mode is None:
        if agents.is_file():
            saved = re.search(r"^Deployment Mode: (Local-first|Production-direct)$", agents.read_text(encoding="utf-8"), re.M)
            deployment_mode = saved[1] if saved else "Local-first"
        elif interactive:
            print("Deployment Mode：1 = Local-first（默认，仅 Local / Preview）；2 = Production-direct（长期授权，Deployment Check 全通过后自动部署生产，不再逐次确认）")
            try:
                choice = input("选择模式 [1]：").strip()
            except EOFError as error:
                raise ValueError("部署模式选择未完成；请用 --deployment-mode Local-first 或 Production-direct 重试") from error
            deployment_mode = {"": "Local-first", "1": "Local-first", "2": "Production-direct"}.get(choice, choice)
        else:
            deployment_mode = "Local-first"
    if deployment_mode not in DEPLOYMENT_MODES:
        raise ValueError("无效 Deployment Mode；请选择 Local-first 或 Production-direct，未写入任何文件")
    manifest = validate_manifest(starter(name))
    files = {relative: source.read_bytes() for relative, source in install_files().items()}
    files["AGENTS.md"] = files["AGENTS.md"].replace(b"@@DEPLOYMENT_MODE@@", deployment_mode.encode("utf-8"))
    files["AGENTS.md"] = files["AGENTS.md"].replace(b"@@BOOTSTRAP_MODE@@", bootstrap_mode.encode("utf-8"))
    files["project.manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if exclude is not None:
        files[".bootstrap/install-state.json"] = encode({"bootstrap_mode": "Local-only", "preexisting_dirs": sorted(set(prior_dirs)),
                                                       "exclude_existed": exclude.exists()}).encode("utf-8")
    # Preflight ALL paths before the first write. No merge or force mode.
    for relative, data in files.items():
        path = check_target(root, relative)
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"初始化冲突：{path} 已有不同内容，未写入任何文件。请用空目录初始化后人工合并")
    map_path = check_target(root, "docs/project/map.html")
    if map_path.exists():
        try:
            validate_map(manifest, map_path)
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f"初始化冲突：{map_path} 已有地图不匹配，未写入任何文件。请用空目录初始化后人工合并；原因：{error}") from error
    else:
        files["docs/project/map.html"] = map_document(manifest, render_diagrams(manifest, explicit)).encode("utf-8")
    created = []
    created_dirs = set()
    try:
        if exclude is not None:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            exclude.write_bytes(exclude_before + EXCLUDE_BLOCK)
        for relative, data in files.items():
            path = check_target(root, relative)
            if path.exists():
                if path.read_bytes() != data:
                    raise ValueError(f"初始化时文件被其他进程修改：{path}；停止写入")
                continue
            for directory in path.parents:
                if directory == root.parent:
                    break
                if not directory.exists():
                    created_dirs.add(directory)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
        validate_map(manifest, map_path)
        if exclude is not None:
            visible = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "--", *LOCAL_SCOPES],
                                     capture_output=True, encoding="utf-8", check=True).stdout
            if visible:
                raise ValueError("项目忽略规则覆盖了本地 exclude，Bootstrap 仍对 Git 可见；初始化已回滚，请检查项目规则")
    except Exception:
        # Only remove files created by this invocation, never pre-existing content.
        for path in reversed(created):
            path.unlink(missing_ok=True)
        for directory in sorted(created_dirs, key=lambda p: len(p.parts), reverse=True):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        if exclude is not None:
            if exclude_before or json.loads(files[".bootstrap/install-state.json"])["exclude_existed"]:
                exclude.write_bytes(exclude_before)
            else:
                exclude.unlink(missing_ok=True)
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
                      help="落地模式：Standard（默认，提交项目）或 Local-only（Git 本地排除）")
    deinit = commands.add_parser("deinit", help="预览 Local-only 清理；加 --yes 删除本地 Bootstrap 与 exclude 区块")
    deinit.add_argument("target", type=Path)
    deinit.add_argument("--yes", action="store_true", help="确认删除全部本地 Bootstrap 产物，含后续编辑")
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
            print(f"初始化通过：新增 {count} 个文件。下一步（1 分钟）：打开 {args.target / 'docs/project/map.html'}")
        elif args.command == "deinit":
            deinitialize(args.target, args.yes)
        else:
            manifest = validate_manifest(read_json(args.manifest))
            if args.command == "map":
                if args.output.resolve() == args.manifest.resolve():
                    raise ValueError("地图输出不能覆盖 manifest；请使用 docs/project/map.html")
                for root in args.manifest.resolve().parents:
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
