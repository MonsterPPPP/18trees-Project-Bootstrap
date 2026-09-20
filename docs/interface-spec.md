# Human–Agent Project Interface

从产品目标或用户流程提出需求，例如「修改 Auth / Session Management」。
人主要操作前三层；Agent 负责将语义映射到实现。

| 基础 | 职责 | 引用 |
|---|---|---|
| i-have-adhd | 面向人的交互与文档 | [上游 skill](https://github.com/ayghri/i-have-adhd) |
| ponytail | 最小实现、编码与测试原则 | [上游 skill](https://github.com/DietrichGebert/ponytail) |
| archify | 可验证、自包含 HTML 与 SVG 可视化 | [上游 skill](https://github.com/tt-a1i/archify) |

只引用上游链接，不复制 skill 正文。Bootstrap 定义协作接口，不另造编码规范。

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

下一步（1 分钟）：用一句话描述你要修改的 Product、Feature 或 Capability。
