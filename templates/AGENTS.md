# 项目协作入口

Bootstrap Mode: @@BOOTSTRAP_MODE@@

Agent Document Mode: @@AGENT_DOC_MODE@@

Git Remote Setup: @@GIT_REMOTE_SETUP@@

Git Push Mode: @@GIT_PUSH_MODE@@

Git 配置是项目长期策略，不代表服务器已配置分支保护或托管 Merge Queue。Remote-auto 仅允许在测试、独立 Review、Merge Queue 最终检查通过后由队列推送；Coding Agent 不得直接 push main。Remote-pending 表示本地初始化已完成但远端尚未配置；Local-only 不自动推送。

人类唯一操作入口是项目 Agent 对话框。首次安装先识别生产目标；没有生产目标时采用 Local-first，有目标时展示配置并询问是否授权 Production-direct。
Agent Document Mode 默认 isolated；不主动询问 indexed。只有人提出要提交条件索引时，才检查并展示精确路径、确认不清楚的授权范围。超时或无回复不授予 Production-direct / indexed；已安装项目沿用有效记录。
只有索引允许进入 Git：indexed 在用户同意的原核心文档追加条件索引，其余 Bootstrap 正文和产物留在本地。
isolated 不修改原核心文档，使用本地薄入口。索引引用的本地文件不存在时忽略，不安装、不下载、不要求协作者补齐。
Local-only 的配置入口为 `.project-bootstrap/AGENTS.md`；显式 Standard 使用根 AGENTS.md，并保留原无覆盖布局。

首次写入前由安装 Agent 读取原核心/覆盖/嵌套规则与引用流程，逐条检查 Git、Review、部署、语义边界及子 Agent 限制。
无法兼容的冲突立即终止安装，列出位置、原规则、Bootstrap 要求、原因和待裁决事项，等待用户决定后重新检查。
允许添加索引不授权改写旧规则。更严格但兼容的限制应保留，例如 require human merge；不能静默宣布 Bootstrap 优先。
安装后先技术自查，再启动独立干净上下文的安装验收子 Agent，由它沿实际入口读取原规则、规范和 skill，并用合成任务检查流程。
验收子 Agent 只读，返回 PASS / REQUEST_CHANGES；不能继承安装 Agent 的结论，不能修改、提交或部署。
无子 Agent、启动失败或未 PASS，只能报告“文件已落地，初始化验收未完成”。详细契约见接口规范的安装验收章节。
这是 Installation Verifier；开发任务的 Review Subagent 仍只接收既有五类评审包，不混用两个角色。

Local-only 的正文、地图、截图及报告均存入 .project-bootstrap/，不得暂存或强制添加；indexed 仅授权索引可按 Gateway Flow 提交。
记录入库文件中的索引不会使其他协作者获得本机生产授权。安装本身不发布生产；两种部署模式均遵守必要检查。
每次任务先用已记录的外部 Python 执行 `python .project-bootstrap/bootstrap.py verify-install .`，核对本地文件与索引；
该命令只证明技术一致性，不能替代语义冲突判断或独立安装验收。执行路径记录在本地 rules.md，不改业务依赖。
进入新 worktree 先检查是否已安装；同一项目已有明确且适用的选择可沿用，否则必须重新提问；每次新安装均需冲突检查及独立验收。
indexed 写入原文档必须在 Task Branch，提交前核对只包含自身索引，不能混入人的未提交改动。
退出请求先预览 deinit、备份需要保留的内容，确认后 --yes；只移除本次拥有的区块，保留其他内容与任务改动。
已提交索引的移除作为普通 Git 差异处理，不改历史；从他处继承的既有索引可保留为无本地规则时的空操作。
人类使用说明见 `docs/project/usage.md`，日常仍只说目标，不操作 CLI。

按 Product → Feature / User Flow → Capability → System / Technical Layer 理解项目。
先读 `docs/project/overview.md` 和 `.bootstrap/interface-spec.md`，再读取
`project.manifest.json`。人主要操作前三层，例如「修改 Auth / Session Management」。

1. 输出遵循 [i-have-adhd](https://github.com/ayghri/i-have-adhd)：行动置顶、编号步骤、每组最多 5 项、每轮进度、具体时间、可见结果、结尾给出 2 分钟内下一步；无前言或客套回顾。错误说明位置、原因和修复，连续三次失败停止并检查假设。含糊时只问一个问题，破坏操作先确认。
2. 工程遵循 [ponytail](https://github.com/DietrichGebert/ponytail)：最小实现、新代码、新抽象、新依赖与影响面；本项目接口不另造编码或测试规范。长期规则写进本文件或 `docs/project/rules.md`，不能只留在聊天；人类文档帮助理解与操作，不复述代码。
3. 真相链是 Codebase → Semantic Project Manifest → HTML Project Map。路径、类名、函数与模块位置只进 metadata，主要供 Agent 使用。地图用 [archify](https://github.com/tt-a1i/archify)，首页第一入口是 Product / Feature Workflow，不是文件树或传统架构图。
4. 默认修改：定位节点 → 追踪链路 → 选择最小路径 → 实施并验证。明确「只修改 NODE:X」即 Strict Node Boundary：不得修改节点外实现，也不自动允许修改子节点或依赖；无法正确完成就停止，说明必要的其他节点，等待人重新定义边界。
5. 有效任务结束才判断同步。新增功能、Capability、服务、数据流、功能链路变化、服务拆分合并、系统边界变化、新外部依赖进入核心流程才同步。样式、内部重构、Bug 修复、算法优化、边界未变的实现替换不触发同步；不按 commit 或文件实时更新。

加载同一份项目 skill：Local-only 读取 `.project-bootstrap/skills/project-interface/SKILL.md`；
Standard 的两个自动发现位置分别为 `.agents/skills/project-interface/SKILL.md` 与
`.claude/skills/project-interface/SKILL.md`。内容一致，不维护两套客户端工作流。
上游 skill 仅链接引用；可从链接单独安装，缺失时按接口规范工作并如实说明，禁止声称已加载。

**Engineering Protocol · Ponytail + Stop That Shit + Semantic Boundary**

工程同时应用 [ponytail](https://github.com/DietrichGebert/ponytail) 与
[stop-that-shit](https://github.com/lennney/stop-that-shit)：前者指导最小实现，后者约束何时停止额外工作。

> 所有 Coding Agent 默认遵循 Ponytail + Stop That Shit：在完整满足当前需求的前提下，采用最小充分实现，禁止无需求的范围膨胀、未来假设、防御性复杂度和重复工作；Review Agent 使用相同原则检查是否存在越界，但不得自行修改代码。

最小充分修改 ≠ 最少代码。完成必要调用方、迁移、测试与文档，即使 diff 更大；
但必要工作不能突破 Strict Node Boundary，涉及边界外先停止并请人重定义。
「修改登录页错误提示」不附带 Auth Service 重构、未来 abstraction、无用 checksum / validation、
重复 Subagent 确认或修完继续“顺便优化”。必须的独立 Review 保留，证据足够后停止重复检查。
不要仅凭名称删除既有保护；STS 正文仅链接引用，不自动安装 Guard hooks。

Reviewer 将以下五项纳入既有 Review Gate，只报告 PASS / REQUEST_CHANGES、原因与修改要求，不自行改代码：

1. 有没有 Scope Creep？
2. 有没有无需求复杂度？
3. 有没有违反用户明确边界？
4. 有没有重复验证 / 重复 Agent 调用？
5. 有没有为了未来假设而增加机制？

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
用户针对已识别目标主动选择 Production-direct，即授予长期 Production Deployment 权限；
一次长期授权替代每次部署前确认，后续任务检查全部通过即自动部署，不再次问是否部署。仅有 URL 不等于授权。
没有生产目标时默认 Local-first；不得推断任何部署授权。

**Deployment · 按模式执行**

| 模式 | 完成开发后的行为 |
|---|---|
| Local-first（无生产目标时的默认值） | 完成修改 → 执行测试 → 独立 Review → Merge Queue 合并；Remote-auto 时同步已配置远端，Local-only 时留在本地。无 remote 时报告缺失。可提供已有 Local / Preview 入口。不得自行进入 Production，只有用户明确提出单次部署才继续 |
| Production-direct | 完成修改 → 执行测试 → 执行项目 Deployment Check → 检查全部通过 → 自动部署 Production；长期授权不代表跳过检查 |

Local-first 适用于 UI / UX 调整、产品功能验证、尚需人工确认效果或生产风险较高的项目。
Local-first 下单次明确生产请求不自动将模式改为 Production-direct。

**Deployment Check · 项目自定义位置**

初始化发现生产目标时，在 `docs/project/rules.md` 的「Deployment Check」记录目标 URL、平台/项目、已有发布入口、必要测试、Build、阻断检查、已有部署要求与执行入口；未知项保持待确认，不编造或创建流水线。两种模式进入 Production 前都必须满足这些检查，不强制统一 CI/CD。
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

下一步（1 分钟）：请人描述想完成的任务，由 Agent 定位语义节点。
