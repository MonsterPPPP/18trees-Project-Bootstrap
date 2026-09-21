<p align="center">
  <img src="./assets/banner.webp" alt="十八木" width="100%" />
</p>

<p align="center">
  中文 · <a href="./README.en.md">English</a>
</p>

# 18trees-Project-Bootstrap

**人类看着项目地图说需求，Agent 按纪律开分支、改代码、过独立评审。**

一个**个人定制化的 Bootstrap**：把四层语义地图、工作子 Agent 协作纪律，以及四个已验证的上游 skill 规范，集成为一次可用的项目初始化。

适用于支持 skills 的 Coding Agent（Codex / Claude Code）。人只描述目标，Agent 负责安装、理解、修改、测试、独立 Review 与按队列合并。

> A personal Bootstrap that integrates a four-layer semantic map, a review-gated sub-agent workflow, and four proven upstream skills into one initialization. Installed non-invasively into existing codebases.

---

## 它解决什么问题

你有一个写了很久的项目。你想让 AI Agent 帮忙改东西，但：

- **它不知道你的项目长什么样**——每次都要重新读代码，而你还是得用文件路径和类名跟它说话
- **它会改到不该改的地方**——你想说"就改这一块"，但"这一块"在代码里对应什么，你说不清楚
- **改完了没有人独立检查**——它说"已完成"，你也看不出对不对
- （顺带一提：不少工具还会往你仓库里塞文件，skills 目录、配置文件全变成你的提交历史）

Project Bootstrap 对应做三件事：

1. **给项目画一张语义地图**——Product / Feature / Capability / System 四层。你在图上指着说"改这里"，Agent 负责把它映射到实现
2. **给协作定一套纪律**——每个任务一条分支、自动启动独立 Review、按队列串行合并，职责边界成文
3. **把好规范引进来**——交互、编码、工程三套规范分别来自四个已验证的上游 skill，不另造一套

然后你只说话：

> 修改登录失败提示，让用户知道如何重试。

---

## 我们的贡献

### 1. 人类看图驱动代码修改

**这是本项目最核心的交互范式。**

多数 Agent 工具让人用工程语言下命令：文件路径、函数名、模块结构。你得先知道代码长什么样，才能说清楚要改哪里——而这恰恰是你想把活交给 AI 的理由。

本项目把项目投影成**四层语义地图**：

```text
Product  →  Feature / User Flow  →  Capability  →  System / Technical Layer
    ↑ 人在这里说话                                        ↑ Agent 负责映射到实现
```

地图首页第一入口是 **Product / Feature Workflow**，不是文件树，也不是传统架构图。**人主要操作前三层**，说「修改 Auth / Session Management」或「修改登录失败提示」，技术路径由 Agent 定位。

由此带来几个直接后果：

- **不需要记文件路径或类名。** 你在产品语义层说话，Agent 在技术层找落点。
- **边界是可指认的。** 说「只修改 NODE:X」就是硬边界——Agent 不得越界；需要涉及其他节点时必须停下说明，等你重新定义。这比口头说"别改太多"可执行得多。
- **同一份 manifest，两种读者。** 渲染成离线可查的 HTML 给人看，同时是 Agent 定位实现的索引。
- **真相链是单向的。** `Codebase → Semantic Project Manifest → HTML Project Map`。路径、类名只进 metadata，不污染人看的那一层。

### 2. Agent 协作纪律：每个任务一条分支 + 强制独立 Review

这是本项目在**工程流程**上的主要产出，也是它和"给 Agent 加个 AGENTS.md"最不一样的地方。

**一次任务的完整链路：**

```text
Human 下达任务
      │
      ▼
Coding Agent ── 基于最新 main 建 Task Branch ── 实现 + 测试
      │
      ▼
自动启动 Review Subagent（不需要人触发）
      │
      ├── PASS ──────────────► Merge Queue
      │                              │
      └── REQUEST_CHANGES            按 Ready 顺序串行
              │                     同步最新 main → 集成检查 → Merge → 删分支
              ▼
   Coder 修改 → 重新测试 → 全新上下文重新 Review
```

**每次改动都单独开一条分支。** `feat/<task>`、`fix/<task>`、`refactor/<task>`、`chore/<task>`——一个分支一个明确任务，合并后删除。**Coding Agent 禁止直接修改、提交或 push `main`。**

**Review 是默认动作，不是可选步骤。** 每个开发任务自动启动 Review Subagent，**不能用 Coder 自审替代**。

**Reviewer 在独立干净的上下文里工作**，不继承 Coding Agent 的聊天、推理或先前结论。它只拿到五类资料：

| 交付给 Reviewer | 内容 |
| --- | --- |
| 原始任务与验收目标 | 原文及成功标准 |
| Semantic Node 与修改边界 | 节点、普通 / Strict、允许行为、共享影响 |
| 当前代码 Diff | 绑定 base / head SHA |
| 测试结果 | 对应 head 的命令、退出码、结果、**未验证项** |
| 规范 | ponytail 与 Project Bootstrap 规范 |

**Reviewer 只读。** 不改代码、不解决冲突、不提交、不合并。只输出两种判定：

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

**证据不足时只能 REQUEST_CHANGES，不能猜测通过。** 把"别让 AI 说'看起来没问题'"写成协议，比写在提示词里可靠。

**审查五项**：原始需求与范围（含 Strict Node Boundary）→ ponytail 最小实现 → STS 行为守卫 → 测试与回归 → 语义同步。

**Merge Queue 串行化。** 入队顺序是「先 Ready 先入队」——**不按分支创建时间**。Ready = 开发完成 + 本分支测试通过 + Review PASS。后入队的必须基于最新 `main` 重新验证；**之前那次 Review PASS 不是无条件合并的依据**。

**冲突不交给 Reviewer 修。** 集成失败时：`Queue FAIL → 移出队列 → 返回原 Coding Agent → 基于最新 main 重新适配 → 测试 → 重新 Review → 重新入队`。Review Agent 不得直接修改。

**职责边界写死：**

| 角色 | 负责 | 不负责 |
| --- | --- | --- |
| Coding Agent | 实现、测试、修复、解决冲突 | 自己批准 Review、直接改 / push `main` |
| Review Agent | 独立审查，`PASS` / `REQUEST_CHANGES` | 修改代码、适配冲突、执行合并 |
| Merge Queue | 串行化、同步最新 main、最终集成验证、合并与清理分支 | 替代 Coder 修改失败实现、绕过 Review |
| Human | 下达任务、设定边界；明确要求时最终 Merge | 默认重复 Review 或 Merge |

**人默认不承担重复的 Review 与 Merge。** 想亲自合并，加一句 `require human merge` 即可——这个开关只改变最终合并责任，不免除独立评审、测试与串行要求。

完整十节规范、Reviewer 可独立执行的契约、`PASS` / `REQUEST_CHANGES` 合成样例见 [接口规范](docs/interface-spec.md)。

**这不是纸面规范——本仓库自己的历史就是按这套跑的。** 每次功能落地都走完了「任务分支 → 独立 Review → merge」：

```text
*   4351362 merge: land Gateway Flow after independent review
|\
| * 21a051a docs: record Gateway Flow acceptance and isolate reviewer context
|/
*   d3dbb27 merge: land deployment policy after independent review
|\
| * 69cd7ee docs: record deployment policy acceptance evidence
|/
*   172cca4 merge: land STS and local-only bootstrap after review
|\
| * 44e8c73 fix: reject shared-worktree local exclusions before writes
|/
*   1381c53 merge: land agent-first bootstrap after independent review
|\
| * 936ed07 fix: atomically preserve rules and Git config on failed install
|/
```

四次 merge 全部标注了 independent review，每次都有一个独立的任务分支和一组它自己的提交。

> 注意：本项目交付的是**行为规范**，不会自动配置托管平台的分支保护、权限或 CI / 队列服务。服务端强制保护需要你在远端自行配置——这一点已列在下方短板里。

### 3. 把已验证的优秀规范引进来（集成者）

本项目**不发明新规范**。它选定四个已验证的上游，把它们编排成一套能协同工作的整体：

| 层 | 上游 | 这一层管什么 |
|---|---|---|
| **交互规范** | [i-have-adhd](https://github.com/ayghri/i-have-adhd) | 每条回复怎么组织：行动置顶、编号步骤、每轮进度、具体时间、可见结果 |
| **编码规范** | [ponytail](https://github.com/DietrichGebert/ponytail) | 怎么实现得尽量小：新代码、新抽象、新依赖与影响面 |
| **工程规范** | [Stop That Shit](https://github.com/lennney/stop-that-shit) | 什么时候停止继续加东西：范围膨胀、无用防御、意图越界、任务打转 |
| **可视化** | [archify](https://github.com/tt-a1i/archify) | 四层语义地图的渲染与校验 |

**集成本身就是工作。** 这四个上游各自独立、接口不同、正文互不引用。让它们在一套流程里协同——各自的适用边界在哪、Reviewer 按哪套标准审查、上游缺失时怎么办、冲突时听谁的——并把结论固化成初始化模板，是本项目的主要产出。

初始化的产出不是几个占位文件，而是一套能立刻开工的协作环境：

| 类别 | 装了什么 |
|---|---|
| **编码规范** | ponytail 的最小实现原则、新依赖与新抽象的门槛、影响面判定 |
| **交互规范** | i-have-adhd 的输出结构：行动置顶、编号步骤、每轮重述进度、具体时间、可见结果 |
| **工程规范** | Stop That Shit 的 S/H/I/T 四类识别与判断顺序；Strict Node Boundary；Reviewer 的审查项 |
| **配置约定** | Git 工作流（分支命名、Review Gate、Merge Queue、`require human merge`）、Deployment Mode、薄入口与加载方式 |

这些结论全部写进目标项目的 `AGENTS.md` 与项目 skill，新会话直接加载，**不需要你重新解释一遍规则**。

所以本项目**明确不新增竞争性的编码规范**：不定义代码风格、不定义测试规范、不定义目录约定。已有的好规范就用已有的，本项目负责让它们一起工作。

### 4. 附带特性：非侵入安装，可逆

前面三条是主动能力；这一条是让它们**不付出代价**的前提。

安装前后 tracked / staged diff 不变，普通 `git status` 不增加 Bootstrap 条目。用 **Git 条件配置**把影响限制在安装所在的工作区——**不改共享 `info/exclude`、不改全局 Git 配置、不改 `.gitignore`**。想让规范随项目提交，显式选 Standard 模式。

并且**可逆**：`deinit` 恢复 exclude 原字节、恢复薄入口原内容、保留你的任务改动。薄入口对已有文件只**追加自己的标记区块**，不改已跟踪的 `AGENTS.md` / `CLAUDE.md`。

### 没做的（是设计选择）

- **不生成代码。** 它建立协作环境，不替你写业务实现。
- **不配置服务端。** 不装 CI、不配分支保护、不搭建 Merge Queue 服务。
- **不做多智能体编排。** 那是 ruflo 的领域。
- **不做规格生成器。** 那是 spec-kit / OpenSpec 的领域。

### 短板（简述）

- **Claude Code 客户端行为验收未完成**——只有 Codex 的新会话加载被真实验证过。这是「未测」，不是「通过」。
- **服务端与语义层未验证**：无远端配置，分支保护与托管 Merge Queue 未经实测；Strict Node Boundary、地图同步等语义事实仍由 Agent 判断，工具不自动证明。
- **只在 Windows 上做过完整验收**（Python 3.12.7 / Node.js 24.12.0 / archify 2.15.0）。
- **Git exclude 不是强制提交拦截器**，`git add -f` 能绕过；且依赖四个上游 skill。
- **0 star，新项目**，实机使用案例还少。

完整边界逐项记录在 [docs/verification.md](docs/verification.md)——那里明确标注了哪些没验证、哪些是合成演练。

---

## 安装

在目标项目的 Coding Agent 对话框里发：

> 请根据这个仓库，在当前项目初始化 Project Bootstrap：`https://github.com/MonsterPPPP/18trees-Project-Bootstrap`。仅本地生效，不把 Bootstrap 文件带进 Git；保留项目已有规则，完成后告诉我怎么使用。

Agent 会读 [INSTALL.md](INSTALL.md) 并执行全流程——准备依赖、理解项目、生成地图、校验安装。

### 前置条件

Python 3.12+、Node.js 22+、Git，以及 [archify](https://github.com/tt-a1i/archify)。缺依赖时 Agent 会在项目外的缓存目录准备隔离环境，**不写进你的项目**。

### ⚠️ 网页版聊天机器人用不了这个项目

**它在你的机器上执行命令**：克隆源码、建 venv、跑 `bootstrap.py init`、修改工作区的 Git 本地配置、生成地图文件。网页版 ChatGPT / Gemini / DeepSeek / Kimi / 豆包 没有工具能力，做不到这些。

需要的是**能执行 shell 命令、能读写文件的 Coding Agent**（Codex / Claude Code，或同类）。

判断一个项目能不能靠粘贴使用，看它**需不需要执行命令或访问文件系统**：

| 类型 | 例子 | 粘贴给网页版聊天机器人 |
|---|---|---|
| 纯文本变换 | 写作、翻译、审阅 | ✅ 能用 |
| 需要执行命令 / 访问文件系统 | 本项目、部署、跑测试 | ❌ 用不了，必须有工具能力 |

同组织的 [18trees-AI-writing-skill](https://github.com/MonsterPPPP/18trees-AI-writing-skill) 属于前者，可以粘贴使用；本项目属于后者，不行。

---

## 使用

装好之后，在同一个对话框里继续：

1. **了解项目** —— "告诉我这个项目能做什么，并打开项目地图。"
2. **提出修改** —— "修改登录失败提示，让用户知道如何重试。"
3. **限定范围** —— "只修改 NODE:X；需要涉及其他节点时先停下说明。"
4. **查看结果** —— "告诉我完成了什么、如何验证。" 默认独立 Review 通过后排队合并；要亲自合并就补 `require human merge`。
5. **退出** —— "移除当前项目的 Bootstrap，保留我的任务改动。"

详细说明见 [人类使用手册](MANUAL.md)。

**默认 Local-only + Local-first**：Bootstrap 留在本机，生产发布需要明确授权。

---

## 仓库结构

```text
.
├── README.md / MANUAL.md / INSTALL.md / AGENTS.md   入口文档
├── bootstrap.py                     CLI：init / map / validate / verify-install / deinit
├── docs/
│   ├── interface-spec.md            接口规范（四层地图、真相链、Gateway Flow、Deployment）
│   ├── toolchain.md                 工具契约：schema、冲突策略、校验边界
│   └── verification.md              验收记录与验证边界
├── schema/                          manifest 的 JSON Schema
├── templates/                       初始化时写入目标项目的模板
├── skills/project-interface/        随初始化安装到目标项目的项目 skill
├── examples/synthetic.manifest.json 合成四层示例（无业务实现）
└── tests/                           工具链测试，`python -m unittest discover -s tests -v`
```

本仓库只交付规范、模板、skill 与工具链；**示例全部是合成数据，不含业务实现**。

---

## 开发

```bash
python -m unittest discover -s tests -v
```

工程遵循 ponytail，开发流程遵循本仓库 [AGENTS.md](AGENTS.md) 里定义的 Gateway Flow。贡献前请读 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 和同类项目比

这个生态已经很成熟了，我们很小。先把全貌摆出来，方便你判断该用哪个。

**数据截至 2026-09-20，star 为当日快照。**

| 项目 | Star | 定位 |
|---|---:|---|
| [github/spec-kit](https://github.com/github/spec-kit) | **138,043** | 给 coding agent 结构化流程与可复用模板（spec / plan / tasks / implement） |
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo)（原 claude-flow） | 72,908 | Agent 编排：多智能体 swarm 与自主协调 |
| [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 69,643 | Spec-driven development，主张 fluid not rigid、iterative not waterfall |
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53,267 | Agile AI Driven Development，覆盖从想法或变更请求到可运行软件的全过程 |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 11,590 | 复杂代码库里的 human-in-the-loop 审批 |
| [steipete/agent-rules](https://github.com/steipete/agent-rules) | 5,686 | 给 Claude Code / Cursor 的规则与知识合集 |
| [buildermethods/agent-os](https://github.com/buildermethods/agent-os) | 5,430 | 从代码库提取既有标准，按需注入 |
| [michaelshimeles/skills](https://github.com/michaelshimeles/skills) | 1,032 | AGENTS.md 工作流模板 + worktree 隔离 + 证据链 |
| **本项目** | **0** | 看图驱动的交互 + 协作纪律 + 集成已验证规范，装进**已有项目**且不留痕迹 |

### 怎么选

| 你的情况 | 建议 |
|---|---|
| 想在生成流程前加一层规格，让 Agent 先写清再动手 | spec-kit / OpenSpec |
| 想要完整敏捷方法论与角色分工（PM / 架构 / 开发 / QA） | BMAD |
| 想要多智能体 swarm 编排 | ruflo |
| 想让 Agent 学你代码库既有的标准与约定 | agent-os |
| 想在关键节点插人工审批 | humanlayer |
| **想让不懂代码结构的自己也能看图指挥改动，且要有强制独立评审** | **本项目** |
| 还在做全新项目、还没有历史包袱 | 上面任选，可能都比本项目合适 |

**一句话**：它们多数在回答"怎么给 Agent 更好的规格"，本项目在回答"**人怎么在不读代码的前提下指挥改动，并且改动必须过独立评审**"。

## License

[MIT](LICENSE) © 2026 十八木
