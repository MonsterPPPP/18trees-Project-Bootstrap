# Human–Agent Project Interface

从产品目标或用户流程提出需求，例如「修改 Auth / Session Management」。
人主要操作前三层；Agent 负责将语义映射到实现。

| 基础 | 职责 | 引用 |
|---|---|---|
| i-have-adhd | 面向人的交互与文档 | [上游 skill](https://github.com/ayghri/i-have-adhd) |
| ponytail | 最小实现、编码与测试原则 | [上游 skill](https://github.com/DietrichGebert/ponytail) |
| archify | 可验证、自包含 HTML 与 SVG 可视化 | [上游 skill](https://github.com/tt-a1i/archify) |

只引用上游链接，不复制 skill 正文。Bootstrap 定义协作接口，不另造编码规范。

```text
Project Bootstrap
├── Human–Agent Communication
├── Semantic Project Map
├── Semantic Modification Protocol
├── Engineering Protocol
│   ├── Ponytail
│   └── Stop That Shit
├── Git Workflow
│   ├── Coding Agent
│   └── Review Agent
└── Deployment
```

**Engineering Protocol · Ponytail + Stop That Shit**

[Ponytail](https://github.com/DietrichGebert/ponytail) 指导怎么实现得尽量小；
[Stop That Shit（STS）](https://github.com/lennney/stop-that-shit) 指导何时停止继续加东西。
STS 针对 Scope creep、无用 hardening、违反用户意图与重复折腾；两者互补，不是二选一。

> 所有 Coding Agent 默认遵循 Ponytail + Stop That Shit：在完整满足当前需求的前提下，采用最小充分实现，禁止无需求的范围膨胀、未来假设、防御性复杂度和重复工作；Review Agent 使用相同原则检查是否存在越界，但不得自行修改代码。

Coding Agent 同时应用 **Ponytail + Stop That Shit + Semantic Boundary**。
最小充分修改 ≠ 最少代码：必要调用方、数据迁移、测试和文档必须一起完成，即使 diff 更大。
必要后果也不能突破 Strict Node Boundary，触及边界先说明并等待人重定义。
真实失败路径需要的保护应保留；不能凭名称删除现有 checksum、校验或恢复机制。

例如「修改登录页错误提示」：完成文案及必要验证，不顺手重构 Auth Service，
不加未来 abstraction、不加无人使用的 checksum / validation、不再叫 Subagent 重复确认，
修完并充分验证后不继续“顺便优化”。Gateway Flow 要求的首次独立 Review 仍执行；
仅在改动、失败或新验收问题使旧证据不再充分时重测或重新 Review。

Reviewer 用 STS 判断问题，不按 STS 优化或修代码；以下五项并入既有 Review 核心检查，不另造流程：

1. 有没有 Scope Creep？
2. 有没有无需求复杂度？
3. 有没有违反用户明确边界？
4. 有没有重复验证 / 重复 Agent 调用？
5. 有没有为了未来假设而增加机制？

Review Agent = PASS / REQUEST_CHANGES ≠ 修改代码。「让它 Review，却自行修复」是违反意图的反例。
STS 仅以链接接入，Bootstrap 不安装其 Guard hooks、不复制正文，也不宣称机器强制拦截。

**交互与长期规则**

1. 答案或下一步行动置顶，命令与可操作入口优先；多步工作编号，每步一个行动，每组最多 5 项。
2. 每轮明确进度，以分钟或秒估算时间；修改后说明现在能工作的内容，结尾给出 2 分钟内可做的下一步。
3. 先解决当前问题；含糊时只问一个简短问题。解释请求充分回答，不添加前言、回顾或客套结束语。
4. 错误说明位置、原因和修复方法；连续三次修复失败后停止，指出可疑假设。破坏性操作执行前确认。
5. 给人的长期规则必须写入 AGENTS.md 或项目文档，不能只存在于聊天。人类文档说明目的、操作和验收，不复述代码。

**四层语义模型**

| 层 | manifest 类型 | 人关心的问题 |
|---|---|---|
| Product | product | 产品为谁解决什么问题？ |
| Feature / User Flow | feature | 用户能完成什么任务？按什么顺序？ |
| Capability | capability | 哪种能力支撑这些任务？ |
| System / Technical Layer | system | 哪些系统实现这些能力？ |

`contains` 只连接相邻层，同一 Capability 可被多个 Feature 复用。
`precedes` 表示 Feature 流程顺序；`depends_on` 表示同层能力或系统依赖；
`data_flow` 表示 Capability / System 之间的数据流，边的 label 必须说明语义。
所有节点必须从 Product 经 contains 可达；已实现的前三层必须具备下一层实现链路。

稳定 ID 格式为 `NODE:X`；改名不改 ID，删除须移除引用。
`metadata` 单独存储仓库相对路径、类、函数、模块位置和证据说明，主要供 Agent 使用；
不得用绝对路径、文件树或函数名替代语义层。地图默认折叠 metadata。
符号和路径用于定位，不能视为独占所有权；共享文件要继续分析到符号和行为。

**Source of Truth**

`Codebase → Semantic Project Manifest → HTML Project Map`。
Codebase 包含实现、测试和项目已落盘的产品决策。Manifest 是经 Agent 核实的语义投影，
HTML 是只读派生产物；不得从 HTML 反向更新 manifest 或据此推断实现。
空项目初始化生成 `planned` 的产品与启动流程，不声称业务已经实现。
已实现节点标记 `implemented` 并提供 metadata 证据；自动校验只能确认结构和引用，
不能证明证据与真实行为一致，Agent 必须阅读相关代码。

**语义修改协议**

1. 定位语义节点：按产品、Feature 或 Capability 识别需求，名称有歧义时只问一个问题。
2. 追踪相关链路：读取上下游、数据流、共享实现与测试，核实 metadata 证据。
3. 按 ponytail 选择最小修改路径：控制语义节点数量与影响范围。
4. 实施并验证用户行为：不以文件改动数量代替正确性；记录必要长期规则。
5. 有效任务完成后判断地图同步：向人报告结果、影响范围、验证和一个下一步。

Strict Node Boundary：人明确「只修改 NODE:X」时，X 是硬边界，**不自动包含子节点或依赖节点**。
可以只读追踪边界外证据，但不得修改节点外实现、共享行为、配置或测试来绕过约束，
也不得通过重标 metadata 偷偷扩大边界。若正确完成需要其他节点，立即停止修改，
说明必须涉及哪些节点及原因，等待人重新定义边界。保留并说明已发生的边界内改动，
不得擅自回滚人的修改。此协议由 Agent 执行，CLI 不宣称能自动判定实现所有权。

**任务结束时的地图同步**

| 判断 | 处理 |
|---|---|
| 新增功能、Capability、服务或数据流 | 同步 manifest，再生成 HTML |
| 功能链路变化、服务拆分合并、系统边界变化 | 同步 manifest，再生成 HTML |
| 新外部依赖进入核心流程 | 同步 manifest，再生成 HTML |
| 样式优化、内部重构、Bug 修复、算法优化 | 语义与结构未变时不更新地图 |
| 能力边界未变的实现替换 | 不更新地图 |

分类依据实际结果而非任务标题；Bug 修复若改变功能链路，仍应同步。
判定时机是一个有效任务完成之后，不是 commit 级、文件级实时同步。
仅路径移动也不触发地图同步：Agent 定位时核实旧线索，下次有语义同步时一并修正 metadata。
发现陈旧线索可记录任务结论，不把 HTML 改成真相源。

**Git Workflow（Gateway Flow）· 1. 基本原则**

`main ← Merge Queue ← Review Gate ← Task Branch ← Coding Agent`。
所有开发任务默认基于最新 `main` 创建独立、短生命周期的 Task Branch。
禁止 Coding Agent 直接修改、提交或直接 push 到 `main`；通过 Review Gate 后由 Merge Queue 执行合并。

**2. Task Branch**

使用 `feat/<task>`、`fix/<task>`、`refactor/<task>`、`chore/<task>`。
一个 Branch 对应一个明确任务，生命周期尽可能短，合并后删除。
修改遵循 [ponytail](https://github.com/DietrichGebert/ponytail)，限制在最小语义范围。
Strict Node Boundary 继续适用：只修改 NODE:X 不包含其子节点、依赖或共享实现的其他行为。

**3. 自动 Code Review**

`Human Task → Coding Agent → 实现 + 测试 → 自动启动 Review Subagent`。
Review 是每个开发任务的默认组成部分，不需要人类额外触发，也不能用 Coder 自审替代。
Review Subagent 使用独立、干净的上下文，不继承 Coding Agent 的聊天、推理或先前结论。
仅交付以下评审包（格式见下文契约）：

1. 原始任务与验收目标。
2. Semantic Node 与修改边界，包括是否为 Strict Node Boundary。
3. 当前代码 Diff，绑定 base / head；必要的原始上下文放在 Diff 中。
4. 测试结果，包括命令、退出码、对应 head、必要风险与未验证项。
5. ponytail 与 Project Bootstrap 规范；基础 skill 正文不复制进仓库。

Reviewer 只读，不改代码、不解决冲突、不提交、不合并，只输出 `PASS` 或
`REQUEST_CHANGES`，附原因与修改要求。证据不足时 REQUEST_CHANGES，不能猜测通过。
`Review FAIL（REQUEST_CHANGES）→ Coding Agent 修改 → 重新测试 → 新上下文重新 Review`，
直到通过或发现任务无法在当前约束下完成；遇到硬边界立即停止修改并说明需要人重新定义的边界。
连续三次修复失败时按交互规范暂停修复、检查假设，不以循环为由绕过停止条件。

**4. Review 核心检查**

| 检查对象 | 必须判断 |
|---|---|
| 原始需求与范围 | 是否真正完成验收；是否越过 Semantic Node，尤其 Strict Node Boundary |
| 最小实现 | 是否违反 ponytail；是否有不必要的重构、依赖或复杂度 |
| STS 行为守卫 | 按 Engineering Protocol 的五项检查审查范围、复杂度、明确边界、重复工作与未来假设；只判断，不修改 |
| 验证与回归 | 测试是否通过、覆盖必要风险；是否引入明显回归 |
| 语义同步 | 发生 Semantic / Structural Change 时，manifest、地图与相关文档是否同步 |

只读追踪边界外信息不授权修改；共享文件须按符号和行为判断，不能只看文件名。
同步仍按本规范的任务结束规则执行；内部实现变化不能为了“过 Review”强制刷新地图。

**5. 默认 Merge 规则**

人类未明确要求人工 Merge 时：`Review PASS → 自动进入 Merge Queue → 最终检查通过 → 自动 Merge 到 main`。
人类明确指定 `require human merge` 时：`Review PASS → WAIT_FOR_HUMAN_MERGE`，
禁止自动合并，等待人执行最终 Merge；可在任务指令或项目长期规则中指定该开关。
开关只改变最终合并责任，不免除独立评审、测试、最新 main 验证或串行合并要求。
人类未指定该开关时，不把重复 Review / Merge 确认交还给人。

**6. 并行 Agent 与 Merge Queue**

多个 Agent 可以在不同 Task Branch 上并行开发；队列按「先 Ready 先入队」排序，
Ready = 开发完成 + 本 Branch 测试通过 + Review PASS，不按 Branch 创建时间排序。
记录当前 head 对应的 Ready 状态；实现变更后原 PASS 失效，重新测试与 Review 后重新排队。
Merge Queue 每次只处理一个队首任务；没有托管队列时由一个协调 Agent 串行执行该职责，
不能由多个 Coding Agent 同时以队列身份更新 main。

**7. 增量 Merge**

尤其是后进入队列的 Branch，必须基于最新 `main` 重新验证：
`同步最新 main → 检查冲突 → 重新运行 Integration Checks → Merge`。
最终检查针对待合并结果（当前任务变更与最新 main 的组合），不是只重读旧测试报告。
有远端时先获取最新 main；验证后若 main 再次前移，丢弃这次最终检查结果并重新同步验证。
之前的 Review PASS 不是无条件 Merge 的依据。无冲突同步可沿用未改变任务实现的 Review；
适配修改、冲突解决或新增实现必须重新测试与 Review。

**8. 冲突处理**

无冲突：`Sync latest main → Tests PASS → Merge`。
出现代码冲突或集成测试失败：
`Merge Queue FAIL → 移出 Queue → 返回原 Coding Agent → 基于最新 main 重新适配 → 测试 → 重新 Review → 重新进入 Merge Queue`。
Review Agent 不得直接修改。重新入队按新的 Ready 顺序，不保留已失效的旧资格。
前序任务仍在处理或其冲突适配尚未确定时，后续 Branch 保持等待，不提前强行解决尚未确定的冲突；
待前序任务完成、明确退出或受阻状态得到明确处置后，再推进后续队首。
适配也不能越过 Strict Node Boundary；必须涉及其他节点时停止，等待人重新定义边界。

**9. Agent 职责边界**

| 角色 | 负责 | 不负责 |
|---|---|---|
| Coding Agent | 实现、测试、修复、解决冲突 | 自己批准 Review、直接修改或 push main |
| Review Agent | 独立审查，PASS / REQUEST_CHANGES | 修改代码、适配冲突、执行合并 |
| Merge Queue | 串行化、同步最新 main、最终集成验证、合并与分支清理 | 替代 Coder 修改失败实现、绕过 Review |
| Human | 下达任务、设定边界；明确要求时最终 Merge | 默认重复 Review 或 Merge 操作 |

Coder 负责修改，Reviewer 负责判断，Merge Queue 负责串行化，人类默认不承担重复的 Review 与 Merge。

**10. main 分支**

main 是受保护分支；禁止 Coding Agent 直接 push，必须经过 Task Branch、Review Gate 与必要测试，
默认通过 Merge Queue 合并，合并后删除 Task Branch（已发布的任务分支也需按仓库权限清理）。
本 Bootstrap 交付行为规范，不自动配置托管平台分支保护、权限或 CI / 队列服务。
接入远端时应把 main 保护设为禁止直接 push、要求 Review 与必要检查，并使用已有队列能力；
未配置时必须如实说明，不宣称文档能提供服务端强制保护。
缺少独立 Reviewer、队列执行能力或必要权限时保留任务分支并报告具体阻碍，不伪造 PASS 或绕过 gate。

**Review Subagent 独立执行契约**

以全新上下文启动 Reviewer。只传第 3 节的五类资料，可用如下任务包；
未提供的验收证据不得视为通过。Reviewer 只审当前包，不读取 Coder 会话或自行扩充任务。

```text
原始任务与验收目标：<原文及成功标准>
Semantic Node 与修改边界：<节点、普通/Strict、允许行为、共享影响>
当前代码 Diff：<base SHA、head SHA、完整 diff；必要上下文使用扩展 diff>
测试结果：<对应 head；命令、退出码、结果、必要风险与未验证项>
规范：<ponytail skill 链接/可读取位置；Project Bootstrap 规范与项目生效规则>
```

若只凭 Diff 无法判断正确性，输出 REQUEST_CHANGES，要求 Coder 补足扩展 Diff 或测试证据。
输出只能使用下面的判定格式；不额外输出实施计划、进度叙述或合并指令。
本格式是机器间 Review 契约，不套用面向人的“结尾下一步行动”格式。

```text
PASS
原因：<需求、边界、最小实现、测试/回归、同步判断的证据>
修改要求：无
```

```text
REQUEST_CHANGES
原因：<具体不符合项及证据，不能只说“有风险”>
修改要求：<可验证的修复或补充证据要求；不授权扩大边界>
```

**合成契约样例（非真实项目评审）**

原始任务：只修改 `NODE:guide` 的使用说明，将重试上限从 2 次写为 3 次；
验收是限制正确、其他节点未变。边界为 Strict，仅文档文字，不涉及语义/结构变化。
合成 Diff A 仅把说明中的 `最多重试 2 次` 改为 `最多重试 3 次`，测试记录为对应 head 的
文档断言通过（退出码 0），范围检查确认只修改该节点。预期输出：

```text
PASS
原因：Diff A 完成指定说明修正，仅涉及 NODE:guide，无额外重构或依赖；文档断言通过，无行为回归；语义/结构未变，无需同步地图。
修改要求：无
```

合成 Diff B 除上述文字外，还修改 `NODE:retry-engine` 的重试实现；测试记录仍通过（退出码 0）。预期输出：

```text
REQUEST_CHANGES
原因：Diff B 修改 NODE:retry-engine 的实现，超出仅允许 NODE:guide 的 Strict Node Boundary；测试通过不能免除越界。
修改要求：由 Coding Agent 移除本次越界改动并重新验证；若验收必须修改重试实现，停止修改，说明涉及 NODE:retry-engine 的原因，等待人重新定义边界后再测试和 Review。
```

**Deployment 规范 · 1. 初始化时选择部署模式**

项目初始化时选择 Deployment Mode，默认 **Local-first**。
交互终端未传选项时显示两种模式，回车选择 Local-first；脚本 / 非交互调用未传选项时使用 Local-first。
也可明确传 `--deployment-mode Local-first` 或 `--deployment-mode Production-direct`。
Agent 代用户初始化时不得自行选择 Production-direct，必须有用户的主动选择；
命令参数或交互选择是该长期授权的落盘方式，初始化本身不执行部署。

| 模式 | 流程与授权 |
|---|---|
| Local-first（默认） | Agent 完成修改 → 执行测试 → 启动 Local / Preview 环境 → 提供可查看入口 → 停止。Agent 不得自行进入 Production；只有用户明确提出部署生产环境后，才可以继续 Production Deployment |
| Production-direct | 用户在初始化主动选择即授予 Agent 长期 Production Deployment 权限。Agent 完成修改 → 执行测试 → 执行项目 Deployment Check → 检查全部通过 → 自动部署 Production；后续任务完成无需再次询问是否部署 |

Local-first 适用于 UI / UX 调整、产品功能验证、尚需人工确认效果的任务和生产风险较高的项目。
Production-direct 是**使用初始化时的一次长期授权，替代每次部署前的人工确认**，不代表跳过检查。
Local-first 的单次生产部署请求只授权该次部署，不自动切换长期模式。

**2. Deployment Check**

无论哪种模式，进入 Production 前都必须满足项目定义的 Deployment Check，至少保证：

1. 必要测试通过。
2. Build 成功。
3. 不存在阻断部署的检查失败。
4. 满足当前项目已有的部署要求。

Deployment Check 是统一概念，不强制所有项目使用相同 CI/CD 技术实现。
项目在 `docs/project/rules.md` 的「Deployment Check」填写具体命令、执行入口和通过标准，
同时定义 Local / Preview 启动入口与 Production 发布方式；可引用项目已有 CI / 部署文档。
检查必须对应实际待部署版本；检查未定义、未运行、结果缺失或失败都不算通过。
Agent 应报告具体缺失 / 失败项，处理阻碍后重新检查，不以再问一次是否部署替代 Deployment Check。
Local / Preview 启动后应验证入口可访问；若项目还没有运行入口，说明缺失，不能声称已启动或改去生产。

**3. 项目级长期配置**

模式在初始化时确定并写入根目录 `AGENTS.md` 的 `Deployment Mode: <模式>`，这是唯一配置源。
Agent 后续任务主动读取，不重复询问当前使用哪种模式，不擅自改变模式；用户可以显式修改。
用户明确修改模式时更新该配置，后续按新模式执行；不得把任务文本中的偶然提及当作授权变更。
配置缺失或无效时不得推断 Production 权限，应指出配置问题；有效 Production-direct 配置无需逐次确认。
重复初始化读取已有模式、不再询问；显式传入不同模式会按既有冲突规则报错，不覆盖项目内容。
`init` 不是模式切换器，模式变更由用户显式指示后编辑长期配置。

**4. 阶段与权限边界**

`Development Complete → Testing / Deployment Check → Deployment Policy → Local / Preview / Production`。
Deployment 与代码修改完成属于不同阶段：先完成开发与验证，再依据模式推进环境。
Gateway Flow 的独立 Review、串行 Merge 和最新 main 检查保持不变；Production 发布应在相应
Review / Merge 流程完成后，对实际待发布版本通过 Deployment Check 再执行。
Production-direct 不绕过 `require human merge`：处于 WAIT_FOR_HUMAN_MERGE 时可以提供 Local / Preview，
不得从未合并分支提前发布 Production；人合并后，长期部署授权继续生效，无需再确认部署。
Local / Preview 可用于查看任务分支效果，但不替代 Review 或 Merge。

自动 Merge 不等于生产授权。若已有 main 流水线会连带发布 Production，Local-first 下先按项目已有机制
阻止生产发布再合并；不能分离时说明阻碍并保留分支，不能利用 Merge 绕过部署策略。
两种模式都不豁免 Strict Node Boundary 或项目已有部署要求。Reviewer 仍只读判断，不承担部署执行。
最终原则：**Local-first 默认保护生产环境；Production-direct 提供经用户预授权后的自动部署能力**。
Bootstrap 只安装规范与配置模板，不创建部署平台、统一 CI/CD 或真实业务部署实现。

**初始化落地模式 · Standard / Local-only**

初始化选择 `--bootstrap-mode Standard|Local-only`。Standard 默认，产物正常属于项目，按 Gateway Flow 提交。
Local-only 用于合作项目 / 他人的项目：所有 Bootstrap 产物留在本地，对 Agent 可见、可读取，
不进入 Git 暂存、提交、分支或 PR，不出现在普通 `git status` 与 `git diff` 中。
Bootstrap Mode 写入 AGENTS.md；Local-only 另有 `.bootstrap/install-state.json` 记录卸载所需的原目录状态。
Agent 开始任务主动读取，不重复询问；不以切换分支改变该模式。

使用 Git 本地 `info/exclude` 标记区块（通过 Git 查询实际位置），
不新增项目 `.gitignore` 条目，不改 Git 索引或已有跟踪状态，不使用 assume-unchanged / skip-worktree。
Git exclude 不会隐藏已跟踪文件，因此安装前拒绝占用的目标路径，尤其已有 AGENTS.md、CLAUDE.md、
manifest 或 docs/project。不能强制接管、取消跟踪或覆盖合作项目规则；请选择未冲突工作区或另行处理边界。
`info/exclude` 在 linked worktree 间共享，因此 Local-only 仅支持一个工作区的仓库；
存在多个 worktree 时在写入前拒绝，避免隐藏其他工作区尚未提交的 Standard 文件。需要隔离时使用独立 clone。
安装期间不得新增 linked worktree；先 deinit 再添加。若已添加，deinit 仍可执行以移除共享排除规则。

Local-only 的专用范围如下，含后续生成内容与模式配置；原项目在这些位置已有内容时安装报错：

| 专用范围 | 内容 |
|---|---|
| `AGENTS.md`、`CLAUDE.md`、`project.manifest.json` | Agent 入口、模式配置与语义 manifest |
| `.bootstrap/` | 工具、规范、schema、安装记录及运行缓存 |
| `docs/project/` | 人类文档、长期规则、HTML 地图与后续截图等产物 |
| `.agents/skills/project-interface/`、`.claude/skills/project-interface/` | 项目 skill 与配套资源 |

Agent 不得 `git add -f` Bootstrap 产物；任务分支只包含真实任务内容。新 Bootstrap 文档、截图、
报告都写进上述专用目录，不得散落到任务目录；不得把业务代码放进这些目录。
生成地图使用默认文档位置 `docs/project/map.html`，不另行输出到 Git 可见路径。
Git 仍可通过显式 `--ignored` 查看本地忽略项，这是正常的诊断能力，不表示产物进入分支。
普通 Git 操作遵守排除；本规范不声称能阻止人为强制添加。

初次 Local-only 需目标已是 Git 工作区根目录；先 `git init` 或使用现有 clone。
交互初始化先选 Bootstrap Mode，再选 Deployment Mode，回车分别默认 Standard 与 Local-first；
非交互不指定时使用各自默认值。重复 Local-only 初始化保留已有本地编辑与地图，不重复询问、
不追加第二个 exclude 区块；不是升级或修复器，模式切换仍不覆盖原文件。

**Local-only 退场**

1. 运行 `python .bootstrap/bootstrap.py deinit .` 预览固定清理范围。
2. 将需要保留的本地规则备份到项目外。
3. 确认后运行 `python .bootstrap/bootstrap.py deinit . --yes`。
4. 运行 `git status --short` 确认仅保留真实任务状态。

deinit 删除专用范围内全部 Bootstrap 文件（包含后续编辑 / 生成物），移除本次 exclude 区块，
删除本次新建的空父目录，保留初始化前已有的空目录、其他 exclude 内容与任务改动。
检测到已被强制跟踪的产物或链接目录时先停止，不自行改索引或删除外部文件。
Standard 不适用 deinit；没有安装记录也不猜测删除。真实项目清理属于破坏操作，Agent 必须先获确认，
`--yes` 是确认后的执行选项。已完成的真实任务提交不会随 Bootstrap 卸载回滚。

Local-only 只管 Bootstrap 的 Git 可见性；Local-first 只管部署去向。二者独立，可组合。
Local-only 下 Gateway Flow、Deployment、STS 与语义边界照常执行；长期本地规则不能因此进入 PR。

下一步（1 分钟）：选择落地方式与部署模式，再开始当前任务。
