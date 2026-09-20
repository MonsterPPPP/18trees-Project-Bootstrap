<p align="center">
  <img src="./assets/banner.webp" alt="十八木" width="100%" />
</p>

# 18trees-Project-Bootstrap

**把一个已经跑了很久的项目交给 AI Agent，而不污染它。**

适用于支持 skills 的 Coding Agent（Codex / Claude Code）。人只描述目标，Agent 负责安装、理解、修改、测试、独立 Review 与按队列合并。

> A minimal-intrusion collaboration layer for AI coding agents working on **existing** codebases: a four-layer semantic map instead of a file tree, a complete Task Branch → Review Gate → Merge Queue → Deployment workflow, and **Local-only by default — nothing enters your Git history**.

---

## 它解决什么问题

你有一个写了很久的项目。你想让 AI Agent 帮忙改东西，但：

- 它不知道你的项目长什么样，每次都要重新读一遍代码
- 它会改到不该改的地方，你说不清楚边界
- 改完之后没有一个独立的评审，你自己也不知道对不对
- 更烦的是：**这些工具会往你仓库里塞文件**——skills 目录、配置文件、规则文件，全部变成你的提交历史

Project Bootstrap 做三件事：

1. **装进去** —— 在已有项目里建立协作规则。**默认 Local-only**：用 Git 条件配置把 Bootstrap 限制在安装所在的工作区，安装前后 tracked / staged diff 不变，普通 `git status` 不增加 Bootstrap 条目
2. **建立地图** —— 把项目投影成 **Product / Feature / Capability / System** 四层语义地图。你在 Product / Feature 层下任务（"修改 Auth / Session Management"），技术路径留给 Agent 去定位
3. **跑流程** —— Task Branch → 独立干净上下文的 Review → Merge Queue → 部署模式，职责边界成文

然后你只说话：

> 修改登录失败提示，让用户知道如何重试。

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
| **本项目** | **0** | 接管**已有项目**：四层语义地图 + 完整工作流闭环 + **默认不污染仓库** |

### 怎么选

| 你的情况 | 建议 |
|---|---|
| 想在生成流程前加一层规格，让 Agent 先写清再动手 | spec-kit / OpenSpec |
| 想要完整敏捷方法论与角色分工（PM / 架构 / 开发 / QA） | BMAD |
| 想要多智能体 swarm 编排 | ruflo |
| 想让 Agent 学你代码库既有的标准与约定 | agent-os |
| 想在关键节点插人工审批 | humanlayer |
| **项目已有年头，且你不想让 Agent 相关文件进入 Git 历史** | **本项目** |
| 还在做全新项目、还没有历史包袱 | 上面任选，可能都比本项目合适 |

**一句话**：它们多数在回答"怎么给 Agent 更好的规格"，本项目在回答"**怎么让 Agent 进来，而不在你的项目里留下痕迹**"。

---

## 我们的贡献

### 做了的

1. **Local-only 安装。** 安装前后 tracked / staged diff 不变，普通 `git status` 不增加 Bootstrap 条目。用 **Git 条件配置**把影响限制在安装所在的工作区——**不改共享 `info/exclude`、不改全局 Git 配置、不改 `.gitignore`**。想让规范随项目提交，显式选 Standard 模式。
2. **四层语义地图。** Product / Feature Workflow / Capability / System，人类在前两层操作，不需要记文件路径或类名。用 [archify](https://github.com/tt-a1i/archify) 生成，可完全离线查看。
3. **可逆。** `deinit` 干净移除：恢复 exclude 原字节、恢复薄入口原内容、保留你的任务改动。薄入口对已有文件只**追加自己的标记区块**，不改已跟踪的 `AGENTS.md` / `CLAUDE.md`。
4. **完整工作流闭环，职责边界成文。** Task Branch → 不继承会话的独立 Review Subagent → 按 Ready 顺序的 Merge Queue（每次都基于最新 main 重新验证）→ 部署模式（Local-first / Production-direct）。含 `require human merge` 人工开关。
5. **不新增竞争性编码规范。** 实现幅度用 [ponytail](https://github.com/DietrichGebert/ponytail)，停止条件用 [Stop That Shit](https://github.com/lennney/stop-that-shit)，交互用 [i-have-adhd](https://github.com/ayghri/i-have-adhd)，可视化用 archify。上游正文只链接引用、不入库。
6. **验收记录如实标注边界。** 见 [docs/verification.md](docs/verification.md)——明确写清了哪些没验证、哪些是合成演练。

### 没做的（是设计选择）

- **不生成代码。** 它建立协作环境，不替你写业务实现。
- **不配置服务端。** 不装 CI、不配分支保护、不搭建 Merge Queue 服务。规范说明了这些 gate 应该怎么设，但初始化不会替你设置。
- **不做多智能体编排。** 那是 ruflo 的领域。
- **不做规格生成器。** 那是 spec-kit / OpenSpec 的领域。

### 诚实的短板

- **Claude Code 客户端行为验收未完成。** 只有 Codex 的新会话加载被真实验证过（真实 `codex exec` 新会话正确读取规则并报告模式）。Claude Code 侧此前三次尝试因超时 / Connection error 未完成，用户明确决定绕过——**这不是"通过"，是"未测"**。
- **服务端未经验证。** 本仓库没有远端配置，因此**分支保护与托管 Merge Queue 未经实测**。
- **语义判断仍由 Agent 执行。** Strict Node Boundary、代码证据、地图同步——工具不自动证明这些语义事实，只提供规范与校验。
- **只在 Windows 上做过完整验收**（Python 3.12.7 / Node.js 24.12.0 / archify 2.15.0）。
- **Git exclude 是本地可见性机制，不是强制提交拦截器。** `git add -f` 能绕过；规范要求 Agent 检查自己的暂存内容，但工具无法从机制上阻止。
- **安装期间，目标项目原有的未跟踪薄入口会被临时隐藏。** 安装前后普通 `git status` 不增加条目，但如果项目里原本就有一个未跟踪的 `AGENTS.override.md` / `CLAUDE.local.md`，它会在安装期内被本地排除、卸载后恢复可见。这是有意的，但属于"状态有变化"而非"完全无感"。
- **依赖四个上游 skill。** 上游变更可能影响行为。
- **0 star，新项目。** 实机使用案例还少。

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

```
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

## License

[MIT](LICENSE) © 2026 十八木
