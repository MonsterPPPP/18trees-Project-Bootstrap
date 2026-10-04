# 给 Coding Agent 的安装说明

用户已在目标项目的对话框提供本仓库链接并要求安装时，由你执行全流程。
Bootstrap 正文默认 Local-only；无生产目标时默认 Local-first，无索引授权时默认 isolated。人不操作 CLI。

若目标目录就是当前 Bootstrap 源仓库本身，不对它再次运行 `init`。源仓库已使用 Standard 规则；按其 AGENTS.md 和 Gateway Flow 修改 Bootstrap 自身，并在任务结束时检查是否需要同步项目地图。

1. **只读识别目标与规则入口。** 记录目标 Git 根目录、status、工作树和 staged diff，读取原核心/覆盖/嵌套规则及其引用流程。识别已有生产目标：以项目部署配置、发布说明或用户提供的生产 URL 为证据；示例链接、开发预览地址不算目标。默认不检查或展示索引候选路径；仅在人要求跟踪索引时识别并展示精确修改路径。
2. **分别确认 Git 选择。** 检查并展示已有 remote 名称与 URL；询问使用哪个现有 remote、通过 GitHub CLI 创建、由用户提供 URL，或仅保留本地。若无 Git 工作区，初始化本地 Git，但不暂存、提交。再单独询问 `Remote-auto` 或 `Local-only` 推送策略；前者只在测试、独立 Review 与 Merge Queue 检查通过后同步远端。若 gh 不可用/未认证，可先完成本地安装，并记录远端待补；用户提供 URL 或完成 gh 认证后再配置。创建仓库默认 private，创建前展示 GitHub 账户、仓库名和可见性，绝不首次直接推送。
3. **只询问其他需要授权的选择。** 没有已配置的生产目标时，采用 Local-first，不自动发布生产；无需再问部署模式。有生产目标时，展示检测到的 URL、平台和部署入口，再询问是否授权 Production-direct 长期自动部署。isolated 是默认值；仅当人要求 indexed 且授权意图不清楚时，展示精确路径并确认。无回复不授予 Production-direct 或 indexed；已完成安装沿用适用的记录。
4. **冲突检查，不兼容就终止本次安装。** 核对 Git/Review/Merge、部署目标与流水线、语义边界、文件修改范围及子 Agent 限制；逐项列出原规则位置、Bootstrap 要求、冲突原因和待决策事项。此时目标项目零写入；用户决定后重新检查。允许索引不授权改写旧规则；更严格但兼容要求保留，例如 require human merge。
5. **检查通过后安装与理解项目。** 源码和环境准备在目标项目之外，复用已有 Python 3.12+、Node.js 22+、jsonschema 和 archify，不改业务依赖或全局设置。indexed 先按 Gateway Flow 建任务分支。无显式部署选项时传 Local-first，无显式文档选项时传 isolated；Production-direct 和 indexed 只在获得明确授权后传入。项目名使用用户给出的名称；缺失时询问。缺少仓库名时展示可选 slug 建议，允许用户选择或输入。读取规范与 skill，按代码证据整理四层语义、manifest、地图和必要测试/部署入口。若存在生产目标，填充规则模板里的 URL、平台、发布入口、检查和凭据引用；向用户确认缺项，绝不记录秘密值或虚构配置。无业务实现就保持 planned。将选择、已读规则、兼容决定、来源 URL/commit、工具路径和技术自查结果写入安装文档（Local-only 为 docs/installation-check.md；Standard 为 docs/project/installation-check.md）。
6. **技术自查 + 独立子 Agent 验收。** 校验安装和地图、原任务改动、索引差异与本地隔离。随后自动启动独立干净上下文的 Installation Verifier，只给目标目录、生效模式及其来源（明确授权或安全默认）和验收任务，不给“已通过”的结论。它只读检查并返回 PASS / REQUEST_CHANGES。缺能力、启动失败或未 PASS 只能报告“文件已落地，初始化验收未完成”；PASS 后记录其原始结果及任务引用，再交付使用说明与地图。仅有测试通过或模型口头自认不算验收完成。

Local-first 的常规交付是否自动同步由初始化时记录的 Git Push Mode 决定；Remote-auto 经 Gateway Flow 同步，Local-only 留在本地。remote 缺失时不得猜地址或推送。安装本身不发布生产。
若索引文件混有人的未提交修改，只能分离自己的区块按 Gateway Flow 提交；无法分离则保留待处理，不能一并暂存。
Standard 只有用户另外明确要求完整规范入库时才选；保持原无覆盖布局，原文件不同仍报冲突，不能强行接管。
旧版安装不能静默升级；要改变入口方式，先备份本地规则，经清理确认后卸载再安装。v2 原本地安装仍可核对和卸载。

**可选低成本子 Agent · 与现有初始化衔接**

冲突检查通过后，用 `python <源码>/bootstrap.py agent setup --cwd <目标>` 读取机器选择。
尚未配置且没有明确选择记录时，在 Agent 对话框询问“是否启用低成本 DSH 子 Agent？”，选启用或跳过；
已回答则复用记录，不重复询问。本会话已授权时不再询问。无回复不启用，常规 Bootstrap 继续。
把明确选择传给现有 init 的 `--low-cost-agent enable|skip`；已有选择时不传，工具读取机器记录。
启用后 Agent 自动复用/补装 acpx、解析真实 DSH 入口、握手及小额烟测；机器配置与项目规则分开。
缺认证、启动失败或权限不足时如实保留 unavailable 和续跑入口，主 Agent 继续无关工作。
不要输出凭据或原始配置/日志；当前宿主不能调用 CLI 时标明能力缺失，不宣称已配置。
技术自查中分别记录可选能力的 ready / skipped / unavailable，与 Bootstrap Installation Verifier 状态区分。
操作、最小任务包、权限与官方 Skill 引用见 [可选能力说明](docs/low-cost-agent.md)。

**执行命令（仅供 Agent；替换尖括号中的绝对路径）**

```text
<外部环境Python> <Bootstrap源码>/bootstrap.py init <目标项目> --name <产品名称> --archify <外部archify目录> [--deployment-mode Local-first|Production-direct] [--agent-doc-mode isolated|indexed] [--git-remote-setup existing|create|url|local] [--git-push-mode Remote-auto|Local-only] [--remote-name <名称>] [--remote-url <URL>] [--repo-name <仓库名>] [--repo-visibility private|public]
<外部环境Python> <目标项目>/.project-bootstrap/bootstrap.py map <目标项目>/.project-bootstrap/project.manifest.json --output <目标项目>/.project-bootstrap/docs/map.html --archify <外部archify目录>
<外部环境Python> <目标项目>/.project-bootstrap/bootstrap.py verify-install <目标项目>
```

用 `python -m venv <外部缓存>/venv` 准备隔离环境；Windows 的 Python 在 `venv/Scripts/python.exe`，
其他平台在 `venv/bin/python`。用该 Python 执行 `-m pip install -r <Bootstrap源码>/requirements.txt`。
普通操作只依赖 Git、Python、jsonschema、Node 和外部 archify；已有地图可完全离线查看。
不要设置系统级执行策略或全局 Git 配置；不要运行来源未核实的远程一键脚本。

**接入与持续使用**

所有客户端读取同一份 `.project-bootstrap/AGENTS.md` 和 `.project-bootstrap/skills/project-interface/SKILL.md`。
isolated 使用 AGENTS.override.md / CLAUDE.local.md 本地薄入口，不修改原核心文档。
indexed 只向已识别核心文档追加带标记的条件索引；该区块可入库，本地文件不存在就忽略，不能用无条件 @ 引入。
已有同样索引复用，不重复插入；索引不含生产授权或本机绝对路径，协作者只遵守各自原规则。
核心文档不存在时用对应本地薄入口；AGENTS.override.md 遮蔽原 AGENTS.md 时先停止，让人确定真实入口。
原正文、编码、换行及未提交内容保留，损坏/重复标记、链接、未授权跟踪入口不能被覆盖。
当前会话必须主动读取；新安装的独立子 Agent 必须沿实际入口验证，不把“文件存在”等同“流程已加载”。

每次任务由 Agent 执行 verify-install，刷新继承的排除规则。新增 worktree 后按相同流程安装，
规则、模式和地图不自动跨工作区复制；已有长期授权可由 Agent 在核实适用范围后沿用，无需重复问人。
Git 条件配置只影响安装所在的工作区；共享 info/exclude、全局配置和 `.gitignore` 均不改。
不同 worktree 可以分别安装，但同一仓库的安装/卸载串行执行，避免同时写共享本地配置。

**独立安装验收任务（给子 Agent 的最小任务包）**

```text
角色：Installation Verifier，只读，不修改、不提交、不部署，不继承安装者对话或结论。
目标目录：<绝对路径>
用户确认的任何授权：Deployment Mode=<Production-direct 或 Local-first>；Agent Document Mode=<indexed 或 isolated>。未选择时使用 Local-first 与 isolated 安全默认。
从实际项目入口开始读取原规则、本地 Bootstrap 规范与 skill，引用对应文件作为依据。
核对模式、原项目限制、技术自查结果和 Git 差异；仅授权条件索引允许进入 Git。
用“修改登录错误提示”的合成任务说明定位节点、Task Branch、测试、Review、Merge Queue 和部署去向；无生产目标时按记录的 Git Push Mode 同步或保留本地，且不发布生产；有目标时只在获授权且 Deployment Check 通过后部署；
再判断“只修改 NODE:X 却必须改 NODE:Y”时应如何处理。没有实际业务节点时只能作假设，不声称业务已实现。
输出 PASS 或 REQUEST_CHANGES，加原因、读取证据和可验证修改要求；不执行真实开发或发布。
```

这是安装验证，不是开发任务的代码 Review；后者仍只使用既有五类评审包，不混用读取范围。
宿主不能隔离上下文/启动子 Agent 时说明能力不足，保留可恢复状态。父 Agent 不得代签 PASS。
本流程不额外要求 Claude Code 专属客户端测试；使用当前项目 Agent 的子 Agent 工具即可。

**退场（由 Agent 执行）**

收到退出请求后，执行 `python .project-bootstrap/bootstrap.py deinit .` 展示范围。
备份用户需要保留的本地规则，获删除确认后加 `--yes` 执行；核对任务改动与原规则保留。
只移除本次拥有的入口/索引区块、专属目录和 Git 条件配置，复用的已存在索引保留。
已提交索引的删除作为普通 Git 差异处理，不改历史、不删除原文档。Standard 不使用 deinit。
工具无法阻止人为 `git add -f`，Agent 必须检查自己的暂存内容且不得强制添加 Bootstrap。

**文档入口**

Local-only 使用 `.project-bootstrap/docs/usage.md`；Standard 使用 `docs/project/usage.md`。
两者均来自根目录 MANUAL.md。完整接口规则见 [接口规范](docs/interface-spec.md)，
工具参数与限制见 [工具链契约](docs/toolchain.md)。不把这份安装说明当作人类手册。

下一步（1 分钟）：确认当前目标项目与原规则，然后由 Agent 执行第 1 步。
