---
name: project-interface
description: 在具有 project.manifest.json 的项目中按语义节点修改，执行严格节点边界与 Gateway Flow 分支、独立评审和串行合并，并判断任务结束时的地图同步。
---

先确定角色：被指派为 Review Subagent 时，跳过下方语义修改步骤，直接执行 Gateway Flow 的
Reviewer 契约，仅使用五类评审包，不自行读取 manifest、代码库或 Coder 会话。
其他角色先读取项目根目录的 `AGENTS.md` 与 `.bootstrap/interface-spec.md`；
本 skill 的路径均相对于项目根目录。若未初始化，停止地图操作并说明缺少的文件。

1. 从 `project.manifest.json` 定位 Product、Feature / User Flow、Capability；追踪 contains、precedes、depends_on、data_flow 与 metadata，再读代码核实证据。HTML 只是 Codebase → Manifest → HTML 链的输出。
2. 按 [ponytail](https://github.com/DietrichGebert/ponytail) 选择最少语义节点、最小影响的正确修改。明确「只修改 NODE:X」是硬边界，不自动包含子节点或依赖；边界外只读。若必须修改其他节点，停止并说明原因，等人重新定义边界，不通过修改 metadata 扩权。
3. 人类输出遵循 [i-have-adhd](https://github.com/ayghri/i-have-adhd) 与 AGENTS.md：行动置顶、每组至多 5 项、每轮进度与具体时间、结果可见、结尾一个 2 分钟内行动。长期规则写入 AGENTS.md 或 `docs/project/rules.md`；人类文档不复述代码。
4. 有效任务结束后按接口规范判断 Semantic / Structural Change。新增功能、能力、服务、数据流、链路变化、拆分合并、系统边界、新外部依赖进入核心流程才同步；语义未变的样式、重构、Bug、算法或实现替换不更新。禁止按 commit 或文件实时同步。
5. 需要同步时先核实代码，再编辑 manifest，运行 `python .bootstrap/bootstrap.py validate project.manifest.json`、`python .bootstrap/bootstrap.py map project.manifest.json --output docs/project/map.html`、`python .bootstrap/bootstrap.py validate project.manifest.json --map docs/project/map.html`。生成依赖外部 [archify](https://github.com/tt-a1i/archify)，CLI 缺失时说明安装或 `--archify` 路径，不伪造地图成功。

地图以 Product / Feature Workflow 为首页，四层明确分开，metadata 默认折叠。
CLI 校验不证明语义证据正确，也不自动强制节点实现边界；这两项由 Agent 核实。

**Gateway Flow 角色路由**

读取 `.bootstrap/interface-spec.md` 中完整的《Git Workflow（Gateway Flow）》与 Review Subagent 契约。
按收到的角色工作；不得把 Reviewer 角色当成编码任务，也不能把 Coder 自审视为独立 Review。

1. Coding Agent：先从最新 main 创建 `feat/<task>`、`fix/<task>`、`refactor/<task>` 或 `chore/<task>`；一分支一任务，按 ponytail 最小实现，禁止直接修改或 push main。实现、测试和必要的地图/文档同步完成后，自动启动 Review Subagent，无需人触发。
2. 评审交接：启动全新、不继承会话的 Reviewer，只交付原始任务与验收、Semantic Node 与边界、当前 Diff（base/head）、对应测试结果、ponytail 与 Bootstrap 规范。不得夹带 Coder 推理或结论；Reviewer 证据不足时要求补足 Diff 上下文或测试结果。
3. Review Agent：只读检查需求、Strict Node Boundary、最小实现、不必要复杂度/重构/依赖、测试风险、回归和必要的语义同步；只按契约输出 PASS 或 REQUEST_CHANGES，加原因与修改要求，不修改或合并。REQUEST_CHANGES 返回 Coder 修改、测试，再用新上下文 Review；硬边界受阻停止，连续三次修复失败检查假设。
4. Merge Queue：Ready = 开发完成 + 本分支测试通过 + 当前 head Review PASS，先 Ready 先入队。默认自动串行合并；队首同步最新 main、检查冲突、重跑 Integration Checks，检查后 main 前移则重新验证。旧 PASS 不无条件授权 Merge；冲突/集成失败移出队列，交原 Coder 适配、测试、重新 Review、按新 Ready 顺序入队。前序任务未处理完时后续分支等待，不抢先解决未确定冲突；Reviewer 不参与修复。
5. Human：下达任务与边界；明确 `require human merge` 时，PASS 后进入 WAIT_FOR_HUMAN_MERGE，不自动合并，也不免除最新 main 检查。否则人不承担重复 Review/Merge；由托管队列或一个协调 Agent 执行最终合并，合并后删除 Task Branch。main 必须受保护；缺独立评审、队列能力或权限时保留分支并报告，不能伪造已启用服务端保护。

适配与冲突修复也服从 Strict Node Boundary，不自动包含子节点/依赖，不以改 metadata 扩权。
本 skill 是行为契约，不自动安装 CI、配置服务端保护或创建常驻队列服务。
Reviewer 输出使用规范中的机器间判定格式；其他角色继续使用面向人的行动优先格式。

下一步（1 分钟）：确认本次角色与语义边界；Coding Agent 选择 Task Branch，Reviewer 核对评审包。
