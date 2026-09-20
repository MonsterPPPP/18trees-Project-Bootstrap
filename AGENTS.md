# Bootstrap 开发约定

先阅读 `docs/interface-spec.md`，再按语义修改规范或工具链。

本仓库只交付规范、模板、skill 与工具链；示例必须是合成数据，不实现业务。
工程遵循 [ponytail](https://github.com/DietrichGebert/ponytail)，交互遵循
[i-have-adhd](https://github.com/ayghri/i-have-adhd)，地图采用
[archify](https://github.com/tt-a1i/archify)。上游正文不入库。

Bootstrap Mode: Standard

人类安装入口是目标项目 Agent 对话框；README 只提供对话示例，INSTALL.md 面向执行安装的 Agent。
目标项目默认 Local-only + Local-first；本地工具与薄入口不得改变原规则或进入业务提交。

Engineering Protocol 同时使用 Ponytail + [Stop That Shit](https://github.com/lennney/stop-that-shit) + Semantic Boundary。
采用完成需求所需的最小充分修改，必要调用方、迁移与测试不能省略；禁止无需求扩张与重复工作。
Reviewer 按 STS 五项审查，只报告不改代码；证据足够后不额外启动重复确认 Agent。

长期规则写入本文件或规范文档。完成有效任务后判断是否存在语义或结构变化；
不按文件或 commit 自动同步地图。明确的 `只修改 NODE:X` 是硬边界。
小步语义化提交；运行 `python -m unittest discover -s tests -v` 验证工具链。

按 `docs/interface-spec.md` 的《Git Workflow（Gateway Flow）》开发：从最新 main 创建
`feat/<task>`、`fix/<task>`、`refactor/<task>` 或 `chore/<task>`，禁止 Coder 直接修改或 push main。
完成实现与测试后自动启动独立干净上下文的 Review Subagent；Reviewer 只判断，不修改。
默认 PASS 后由 Merge Queue 按 Ready 顺序串行同步最新 main、运行集成检查并合并，随后删除任务分支。
冲突或集成失败交原 Coder 适配、测试、重新 Review、重新入队；后续分支等待前序处理结果。
只有明确 `require human merge` 才进入 WAIT_FOR_HUMAN_MERGE；没有服务端保护时如实说明。

Deployment Mode: Local-first

本仓库部署规则见 `docs/interface-spec.md` 的《Deployment 规范》。开发验证后提供本地文档或地图入口，
不自行发布 Production。本仓库只交付工具与规范，尚无生产部署目标；明确要求生产发布时，
须先定义必要测试、Build、阻断检查和现有部署要求，不把“测试通过”当作已完成生产部署。

下一步（1 分钟）：打开 `docs/interface-spec.md` 确认修改对应的语义范围。
