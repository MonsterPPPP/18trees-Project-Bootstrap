# 给 Coding Agent 的安装说明

用户已在目标项目的对话框提供本仓库链接并要求安装时，由你执行全流程。
默认 **Local-only + Local-first**，不询问默认参数、不要求人复制命令。不维护客户端专属安装流程。

1. **确认目标与边界。** 保持目标项目的绝对路径，读取原 AGENTS.md、CLAUDE.md 与适用的嵌套规则；记录 `git status --porcelain`、工作树 diff 与 staged diff。目标须是已有 Git 工作区根目录；没有 Git 时说明缺少条件，不擅自建仓库。保留未提交任务，不 stash、不 reset、不修改已跟踪规则。规则冲突只问一个具体问题。
2. **在目标项目之外准备来源和依赖。** 从用户提供的 URL 克隆 Bootstrap 到项目外的本机缓存，或复用已核实的源码副本；记录来源 URL 和 commit。不要将源码、上游 skill、运行环境或依赖锁文件写入目标项目。使用已有 Python 3.12+、Node.js 22+ 与 archify；缺 Python 包时在外部缓存建立 venv，并用其 Python 安装 Bootstrap requirements.txt。缺 archify 时将 `https://github.com/tt-a1i/archify` 克隆到外部缓存，用 `--archify` 显式指定。Python/Node 缺失或安装权限不足时如实说明，不擅改系统配置。
3. **执行初始化。** 从完整源码副本运行下列命令；使用绝对路径，部署模式只有用户明确授权才能选择 Production-direct。Standard 只有用户明确要求规范随项目提交时才选择。遇到旧版安装，先备份本地编辑、说明卸载范围并获确认，然后用原安装工具 deinit，再安装并恢复本地规则；不静默迁移。
4. **理解真实项目。** 当前会话主动读取安装的协作入口和 skill；读取现有代码、测试、README 和已落盘产品决策，将真实产品、功能、能力、技术层整理进本地 manifest。metadata 路径相对目标项目根目录，不是相对隐藏目录。未实现能力保持 planned；证据不足只问必要问题，不虚构实现。更新本地 overview 与必要的验证/部署入口；在本地 rules.md 记录源码来源及 commit、可复用 Python 与 archify 的绝对路径，供新会话复用，然后生成并校验地图。
5. **验证并交付。** 执行 verify-install；比较安装前后的 tracked / staged diff 不变，普通 status 不增加 Bootstrap。原有未跟踪薄入口在安装期间会被本地排除，卸载恢复可见性；除此之外原任务状态保持。不得为了验证去暂存真实用户改动。核实当前会话已读取规则；能启动客户端新会话时再验证自动加载，不能时明确区分文件检查与会话验收。返回使用说明与地图的绝对路径链接，以及一句可直接对你说的下一步。

**执行命令（仅供 Agent；替换尖括号中的绝对路径）**

```text
<外部环境Python> <Bootstrap源码>/bootstrap.py init <目标项目> --name <产品名称> --archify <外部archify目录>
<外部环境Python> <目标项目>/.project-bootstrap/bootstrap.py map <目标项目>/.project-bootstrap/project.manifest.json --output <目标项目>/.project-bootstrap/docs/map.html --archify <外部archify目录>
<外部环境Python> <目标项目>/.project-bootstrap/bootstrap.py verify-install <目标项目>
```

用 `python -m venv <外部缓存>/venv` 准备隔离环境；Windows 的 Python 在 `venv/Scripts/python.exe`，
其他平台在 `venv/bin/python`。用该 Python 执行 `-m pip install -r <Bootstrap源码>/requirements.txt`。
普通操作只依赖 Git、Python、jsonschema、Node 和外部 archify；已有地图可完全离线查看。
不要设置系统级执行策略或全局 Git 配置；不要运行来源未核实的远程一键脚本。

**接入与持续使用**

所有客户端读取同一份 `.project-bootstrap/AGENTS.md` 和 `skills/project-interface/SKILL.md`。
Codex 的薄入口 `AGENTS.override.md` 先要求读取原 AGENTS.md；Claude Code 的 `CLAUDE.local.md` 引入统一入口。
不修改已有受跟踪的 AGENTS.md / CLAUDE.md。薄入口已跟踪、有链接或已有安装区块不完整时停止并说明。
未跟踪薄入口的原内容保留，仅追加自己的标记区块。新会话是否自动读取须以客户端实际行为确认。
当前会话立即主动读取；无需让人重新贴长规范。其他 Agent 使用同一份入口说明，未经验证不宣称自动加载。

每次任务由 Agent 执行 verify-install，刷新继承的排除规则。新增 worktree 后按相同流程安装，
规则、模式和地图不自动跨工作区复制；已有长期授权可由 Agent 在核实适用范围后沿用，无需重复问人。
Git 条件配置只影响安装所在的工作区；共享 info/exclude、全局配置和 `.gitignore` 均不改。
不同 worktree 可以分别安装，但同一仓库的安装/卸载串行执行，避免同时写共享本地配置。

**退场（由 Agent 执行）**

收到退出请求后，执行 `python .project-bootstrap/bootstrap.py deinit .` 展示范围。
备份用户需要保留的本地规则，获删除确认后加 `--yes` 执行；核对任务改动与原规则保留。
只移除本次入口区块、专属目录和 Git 条件配置。Standard 不使用 deinit。
工具无法阻止人为 `git add -f`，Agent 必须检查自己的暂存内容且不得强制添加 Bootstrap。

**文档入口**

Local-only 使用 `.project-bootstrap/docs/usage.md`；Standard 使用 `docs/project/usage.md`。
两者均来自根目录 MANUAL.md。完整接口规则见 [接口规范](docs/interface-spec.md)，
工具参数与限制见 [工具链契约](docs/toolchain.md)。不把这份安装说明当作人类手册。

下一步（1 分钟）：确认当前目标项目与原规则，然后由 Agent 执行第 1 步。
