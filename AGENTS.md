# Bootstrap 开发约定

先阅读 `docs/interface-spec.md`，再按语义修改规范或工具链。

本仓库只交付规范、模板、skill 与工具链；示例必须是合成数据，不实现业务。
工程遵循 [ponytail](https://github.com/DietrichGebert/ponytail)，交互遵循
[i-have-adhd](https://github.com/ayghri/i-have-adhd)，地图采用
[archify](https://github.com/tt-a1i/archify)。上游正文不入库。

长期规则写入本文件或规范文档。完成有效任务后判断是否存在语义或结构变化；
不按文件或 commit 自动同步地图。明确的 `只修改 NODE:X` 是硬边界。
小步语义化提交；运行 `python -m unittest discover -s tests -v` 验证工具链。

按 `docs/interface-spec.md` 的《Git Workflow（Gateway Flow）》开发：从最新 main 创建
`feat/<task>`、`fix/<task>`、`refactor/<task>` 或 `chore/<task>`，禁止 Coder 直接修改或 push main。
完成实现与测试后自动启动独立干净上下文的 Review Subagent；Reviewer 只判断，不修改。
默认 PASS 后由 Merge Queue 按 Ready 顺序串行同步最新 main、运行集成检查并合并，随后删除任务分支。
冲突或集成失败交原 Coder 适配、测试、重新 Review、重新入队；后续分支等待前序处理结果。
只有明确 `require human merge` 才进入 WAIT_FOR_HUMAN_MERGE；没有服务端保护时如实说明。

下一步（1 分钟）：打开 `docs/interface-spec.md` 确认修改对应的语义范围。
