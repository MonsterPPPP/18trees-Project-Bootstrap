# 项目协作入口

按 Product → Feature / User Flow → Capability → System / Technical Layer 理解项目。
先读 `docs/project/overview.md` 和 `.bootstrap/interface-spec.md`，再读取
`project.manifest.json`。人主要操作前三层，例如「修改 Auth / Session Management」。

1. 输出遵循 [i-have-adhd](https://github.com/ayghri/i-have-adhd)：行动置顶、编号步骤、每组最多 5 项、每轮进度、具体时间、可见结果、结尾给出 2 分钟内下一步；无前言或客套回顾。错误说明位置、原因和修复，连续三次失败停止并检查假设。含糊时只问一个问题，破坏操作先确认。
2. 工程遵循 [ponytail](https://github.com/DietrichGebert/ponytail)：最小实现、新代码、新抽象、新依赖与影响面；本项目接口不另造编码或测试规范。长期规则写进本文件或 `docs/project/rules.md`，不能只留在聊天；人类文档帮助理解与操作，不复述代码。
3. 真相链是 Codebase → Semantic Project Manifest → HTML Project Map。路径、类名、函数与模块位置只进 metadata，主要供 Agent 使用。地图用 [archify](https://github.com/tt-a1i/archify)，首页第一入口是 Product / Feature Workflow，不是文件树或传统架构图。
4. 默认修改：定位节点 → 追踪链路 → 选择最小路径 → 实施并验证。明确「只修改 NODE:X」即 Strict Node Boundary：不得修改节点外实现，也不自动允许修改子节点或依赖；无法正确完成就停止，说明必要的其他节点，等待人重新定义边界。
5. 有效任务结束才判断同步。新增功能、Capability、服务、数据流、功能链路变化、服务拆分合并、系统边界变化、新外部依赖进入核心流程才同步。样式、内部重构、Bug 修复、算法优化、边界未变的实现替换不触发同步；不按 commit 或文件实时更新。

加载项目 skill：Codex 使用 `.agents/skills/project-interface/SKILL.md`，Claude Code 使用
`.claude/skills/project-interface/SKILL.md`。两份由 Bootstrap 安装，需保持一致。
上游 skill 仅链接引用；可从链接单独安装，缺失时按接口规范工作并如实说明，禁止声称已加载。

下一步（1 分钟）：打开 `docs/project/map.html`，选择产品或用户流程。
