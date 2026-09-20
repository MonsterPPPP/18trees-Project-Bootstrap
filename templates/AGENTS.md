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

**Git Workflow（Gateway Flow）· 1. 基本原则**

`main ← Merge Queue ← Review Gate ← Task Branch ← Coding Agent`。
所有开发任务默认从最新 main 创建独立短生命周期 Task Branch；Coding Agent 禁止直接修改、提交或 push main。

**2. Task Branch**

命名 `feat/<task>`、`fix/<task>`、`refactor/<task>`、`chore/<task>`；一个分支一个明确任务，
生命周期尽可能短，合并后删除。按 ponytail 将修改限制在最小语义范围，继续遵守 Strict Node Boundary。

**3. 自动 Code Review**

`Human Task → Coding Agent → 实现 + 测试 → 自动启动 Review Subagent`，无需人额外触发。
Reviewer 必须是独立干净上下文，只接收原始任务与验收、Semantic Node 与边界、当前代码 Diff、
测试结果、ponytail 与 Project Bootstrap 规范，不继承 Coder 会话或判断。
Reviewer 不改代码，只输出 PASS 或 REQUEST_CHANGES，加原因与修改要求；证据不足不得 PASS。
`Review FAIL → Coding Agent 修改 → 重新测试 → 重新 Review`，直到通过或发现当前约束下无法完成。
硬边界受阻立即停止；连续三次修复失败按交互规范停止并检查假设。

**4. Review 检查范围**

核对原始需求完成度、Semantic Node / Strict Node Boundary、ponytail 最小实现，
排除不必要重构、依赖和复杂度；检查测试通过与必要风险覆盖、明显回归，
以及 Semantic / Structural Change 后 manifest、地图与相关文档同步情况。
无语义变化不强制更新地图；不得借同步或测试修改越过边界。

**5. 默认 Merge 与人工开关**

默认 `Review PASS → 自动进入 Merge Queue → 最终检查通过 → 自动 Merge 到 main`。
人明确指定 `require human merge`（任务指令或长期规则）时，`Review PASS → WAIT_FOR_HUMAN_MERGE`，
等待人最终合并；其余 Review、最新 main 验证、测试和串行要求不变。

**6. 并行与队列顺序**

不同分支可并行开发；Ready = 开发完成 + 本 Branch 测试通过 + Review PASS。
先 Ready 先入队，不按分支创建时间；PASS 绑定当前 head，实现再改需重新测试与 Review。
由托管队列或一个协调 Agent 串行处理队首，禁止多个 Coder 同时更新 main。

**7. 增量 Merge**

每个队首，尤其后入队分支，都要同步最新 main → 检查冲突 → 重新运行 Integration Checks → Merge。
验证任务与最新 main 的组合；检查后 main 再变则重新验证，旧 Review PASS 不能作为无条件合并依据。
有远端先获取最新 main；适配修改后必须重新 Review。

**8. 冲突闭环**

无冲突：`Sync latest main → Tests PASS → Merge`。
冲突或集成测试失败：`Merge Queue FAIL → 移出 Queue → 返回原 Coding Agent → 基于最新 main 重新适配 → 测试 → 重新 Review → 重新进入 Merge Queue`。
Reviewer 不得修复；重新 Ready 后按新顺序入队。前序任务仍在处理时，后续 Branch 等待，
不提前强行解决尚未确定的冲突。适配需要越过 Strict Node Boundary 时停止并等待人重新定义边界。

**9. 职责边界**

| 角色 | 职责 |
|---|---|
| Coding Agent | 实现、测试、修复、解决冲突；不批准自己的 Review，不直接修改或 push main |
| Review Agent | 独立判断 PASS / REQUEST_CHANGES；不修改、不合并 |
| Merge Queue | 串行合并、最新 main 最终验证、清理已合并任务分支；失败交回 Coder |
| Human | 下达任务、设定边界；仅明确要求时最终 Merge |

Coder 修改、Reviewer 判断、Merge Queue 串行化；人类默认不承担重复 Review 与 Merge。

**10. main 保护**

main 为受保护分支，禁止 Coding Agent 直接 push；必须经过 Task Branch、Review Gate、必要测试，
默认经 Merge Queue 合并，合并后删除 Task Branch。本 Bootstrap 不自动配置服务端保护或 CI；
接入远端时按上述 gate 配置保护。缺 Reviewer、队列能力或权限时报告阻碍，不能绕过。
完整规范与可独立执行的评审包、PASS / REQUEST_CHANGES 样例见 `.bootstrap/interface-spec.md`。

**Deployment · 项目长期配置**

Deployment Mode: @@DEPLOYMENT_MODE@@

此行是本项目部署模式的唯一配置源。每次任务主动读取，不重复询问当前模式，不擅自改变；
用户可以显式修改此行。缺失或无效时不得推断生产授权，应说明配置问题。
用户在初始化主动选择 Production-direct，即授予长期 Production Deployment 权限；
一次长期授权替代每次部署前确认，后续任务检查全部通过即自动部署，不再次问是否部署。
初始化选择 Local-first 或未指定模式，均不授予生产权限。

**Deployment · 按模式执行**

| 模式 | 完成开发后的行为 |
|---|---|
| Local-first（默认） | 完成修改 → 执行测试 → 启动 Local / Preview → 提供可查看入口 → 停止；不得自行进入 Production，只有用户明确提出部署生产环境才继续 |
| Production-direct | 完成修改 → 执行测试 → 执行项目 Deployment Check → 检查全部通过 → 自动部署 Production；长期授权不代表跳过检查 |

Local-first 适用于 UI / UX 调整、产品功能验证、尚需人工确认效果或生产风险较高的项目。
Local-first 下单次明确生产请求不自动将模式改为 Production-direct。

**Deployment Check · 项目自定义位置**

在 `docs/project/rules.md` 的「Deployment Check」填写本项目的必要测试、Build、阻断检查、
已有部署要求与执行入口。两种模式进入 Production 前都必须满足这些检查，不强制统一 CI/CD。
未定义、未执行、结果缺失或有失败都不能视为通过；说明具体阻碍，不以询问是否部署代替修复。
Local / Preview 启动方式与可查看入口也在该位置定义；启动后验证可访问再报告，不虚构成功。

**Deployment · 与 Gateway Flow 衔接**

`Development Complete → Testing / Deployment Check → Deployment Policy → Local / Preview / Production`。
代码修改完成与部署是不同阶段。先完成开发与验证；Production 还必须完成 Gateway Flow 的
Review Gate、Merge Queue / 人工合并及最终检查，再对实际待部署版本执行 Deployment Check。
Production-direct 不绕过 `require human merge`，也不授权从未合并任务分支发布生产。
Local / Preview 可以作为任务分支的查看入口，但不替代 Review / Merge，也不会触发 Production。
若现有合并流水线会自动发布生产，Local-first 下须先按项目流程阻止该发布，不能借自动 Merge 绕过部署授权。
无法分离时报告阻碍并保留分支，不能冒充已获得生产授权。

下一步（1 分钟）：核对本文件的 Deployment Mode，并打开 `docs/project/rules.md` 填写部署检查入口。
