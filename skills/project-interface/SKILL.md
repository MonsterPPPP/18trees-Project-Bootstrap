---
name: project-interface
description: 在具有 project.manifest.json 的项目中按产品、功能或能力定位修改，执行严格节点边界，并在任务结束时判断是否同步语义地图。
---

先读取项目根目录的 `AGENTS.md` 与 `.bootstrap/interface-spec.md`；
本 skill 的路径均相对于项目根目录。若未初始化，停止地图操作并说明缺少的文件。

1. 从 `project.manifest.json` 定位 Product、Feature / User Flow、Capability；追踪 contains、precedes、depends_on、data_flow 与 metadata，再读代码核实证据。HTML 只是 Codebase → Manifest → HTML 链的输出。
2. 按 [ponytail](https://github.com/DietrichGebert/ponytail) 选择最少语义节点、最小影响的正确修改。明确「只修改 NODE:X」是硬边界，不自动包含子节点或依赖；边界外只读。若必须修改其他节点，停止并说明原因，等人重新定义边界，不通过修改 metadata 扩权。
3. 人类输出遵循 [i-have-adhd](https://github.com/ayghri/i-have-adhd) 与 AGENTS.md：行动置顶、每组至多 5 项、每轮进度与具体时间、结果可见、结尾一个 2 分钟内行动。长期规则写入 AGENTS.md 或 `docs/project/rules.md`；人类文档不复述代码。
4. 有效任务结束后按接口规范判断 Semantic / Structural Change。新增功能、能力、服务、数据流、链路变化、拆分合并、系统边界、新外部依赖进入核心流程才同步；语义未变的样式、重构、Bug、算法或实现替换不更新。禁止按 commit 或文件实时同步。
5. 需要同步时先核实代码，再编辑 manifest，运行 `python .bootstrap/bootstrap.py validate project.manifest.json`、`python .bootstrap/bootstrap.py map project.manifest.json --output docs/project/map.html`、`python .bootstrap/bootstrap.py validate project.manifest.json --map docs/project/map.html`。生成依赖外部 [archify](https://github.com/tt-a1i/archify)，CLI 缺失时说明安装或 `--archify` 路径，不伪造地图成功。

地图以 Product / Feature Workflow 为首页，四层明确分开，metadata 默认折叠。
CLI 校验不证明语义证据正确，也不自动强制节点实现边界；这两项由 Agent 核实。

下一步（1 分钟）：在 manifest 中找到本次需求的语义节点。
