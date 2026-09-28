# 给 Coding Agent 的安装说明

用户已在目标项目的对话框提供本仓库链接并要求安装时，由你执行全流程。
Bootstrap 正文仍默认 Local-only；两项安装决定必须由用户主动选择。人不操作 CLI。

1. **只读识别目标与规则入口。** 记录目标 Git 根目录、status、工作树和 staged diff，读取原核心/覆盖/嵌套规则及它们引用的相关流程。向用户展示 indexed 会追加索引的路径（根 AGENTS.md、CLAUDE.md、已有 .claude/CLAUDE.md）；不存在时用本地薄入口，不扩大到所有子目录。
2. **唤起选择工具，必须等到两项答案。** 问①“只同步仓库，不自动部署生产”或“检查通过后自动部署生产”；对应 Local-first / Production-direct。问②“允许在现有 Agent 文档添加条件索引”或“不允许，使用本地入口”；对应 indexed / isolated。明确前者仅索引可入 Git、正文仍本地，生产选项是长期授权且不跳过检查。推荐/预选、超时都不是确认；没有选择工具时逐项对话询问。已完成安装不重复问，有记录的适用选择可复用。
3. **冲突检查，不兼容就终止本次安装。** 核对 Git/Review/Merge、部署授权与发布流水线、语义边界、文件修改范围及子 Agent 限制；逐项列出原规则位置、Bootstrap 要求、冲突原因、待决策事项。此时目标项目零写入，诊断留在对话或项目外。等人调整选择、明确授权修订具体规则或取消后，重新检查。允许索引不能当作修改旧规则的授权；更严格但兼容要求保留，例如 require human merge。
4. **检查通过后安装与理解项目。** 源码和环境准备在目标项目之外，复用已有 Python 3.12+、Node.js 22+、jsonschema 和 archify，不改业务依赖或全局设置。indexed 先按 Gateway Flow 建任务分支。显式传两项选择安装；读取规范与 skill，按代码证据整理四层语义、manifest、地图与必要测试/部署入口。无业务实现就保持 planned。将选择、已读规则、兼容决定、来源 URL/commit、工具路径和技术自查结果写入本地 docs/installation-check.md（Standard 为 docs/project/installation-check.md）。
5. **技术自查 + 独立子 Agent 验收。** 校验安装和地图、原任务改动、索引差异与本地隔离。随后自动启动独立干净上下文的 Installation Verifier，只给目标目录、用户两项选择和下方验收任务，不给“已通过”的结论。它只读检查并返回 PASS / REQUEST_CHANGES。缺能力、启动失败或未 PASS 只能报告“文件已落地，初始化验收未完成”；PASS 后记录其原始结果及任务引用，再交付使用说明与地图。仅有测试通过或模型口头自认不算验收完成。

用户选择只决定后续任务如何交付，安装本身不发布生产，也不能直接 push main。
若索引文件混有人的未提交修改，只能分离自己的区块按 Gateway Flow 提交；无法分离则保留待处理，不能一并暂存。
Standard 只有用户另外明确要求完整规范入库时才选；保持原无覆盖布局，原文件不同仍报冲突，不能强行接管。
旧版安装不能静默升级；要改变入口方式，先备份本地规则，经清理确认后卸载再安装。v2 原本地安装仍可核对和卸载。

**执行命令（仅供 Agent；替换尖括号中的绝对路径）**

```text
<外部环境Python> <Bootstrap源码>/bootstrap.py init <目标项目> --name <产品名称> --archify <外部archify目录> --deployment-mode <用户选择的Local-first或Production-direct> --agent-doc-mode <用户选择的isolated或indexed>
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
用户已确认：Deployment Mode=<值>；Agent Document Mode=<值>。
从实际项目入口开始读取原规则、本地 Bootstrap 规范与 skill，引用对应文件作为依据。
核对模式、原项目限制、技术自查结果和 Git 差异；仅授权条件索引允许进入 Git。
用“修改登录错误提示”的合成任务说明定位节点、Task Branch、测试、Review、Merge Queue 和部署去向；
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
