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


def initialize(target, name, explicit=None):
    if not (BASE / "templates/AGENTS.md").is_file():
        raise ValueError("init 需要完整 Bootstrap 源仓库；请在源仓库运行 python bootstrap.py init <目标目录>。项目内使用 map / validate")
    root = Path(os.path.abspath(target))
    manifest = validate_manifest(starter(name))
    files = {relative: source.read_bytes() for relative, source in install_files().items()}
    files["project.manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
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
    try:
        for relative, data in files.items():
            path = check_target(root, relative)
            if path.exists():
                if path.read_bytes() != data:
                    raise ValueError(f"初始化时文件被其他进程修改：{path}；停止写入")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
        validate_map(manifest, map_path)
    except Exception:
        # Only remove files created by this invocation, never pre-existing content.
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
            count = initialize(args.target, args.name, args.archify)
            print(f"初始化通过：新增 {count} 个文件。下一步（1 分钟）：打开 {args.target / 'docs/project/map.html'}")
        else:
            manifest = validate_manifest(read_json(args.manifest))
            if args.command == "map":
                if args.output.resolve() == args.manifest.resolve():
                    raise ValueError("地图输出不能覆盖 manifest；请使用 docs/project/map.html")
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
