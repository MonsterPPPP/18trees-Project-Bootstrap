# 使用手册

```powershell
python bootstrap.py init ../my-project --bootstrap-mode Standard --deployment-mode Local-first
```

**初始化（约 3 分钟，依赖下载另计）**

1. 准备 Python 3.12+、Node.js 22+，在 Bootstrap 源仓库运行 `python -m pip install -r requirements.txt`。
2. 若没有 archify，克隆到项目外：`git clone https://github.com/tt-a1i/archify ../archify`；PowerShell 设置 `$env:ARCHIFY_HOME='../archify'`。
3. 为新项目运行 `git init -b main ../my-project`；已有合作项目直接使用其 Git 根目录。
4. 在 Bootstrap 源仓库选择下面一条初始化命令。
5. 在目标项目打开 `docs/project/map.html`，让 Agent 读取 `AGENTS.md`，填写 `docs/project/overview.md` 的产品目标。

| 使用场景 | 初始化命令（在 Bootstrap 源仓库执行） |
|---|---|
| 自己的新项目，规范随项目提交 | `python bootstrap.py init ../my-project --bootstrap-mode Standard --deployment-mode Local-first` |
| 带进合作 / 他人项目，仅本地使用 | `python bootstrap.py init ../my-project --bootstrap-mode Local-only --deployment-mode Local-first` |
| 已决定长期授权自动生产部署 | 将所选命令末尾改成 `--deployment-mode Production-direct` |

不传模式时，交互终端依次提问，回车默认 Standard、Local-first；非交互使用同样默认值。
**Local-only 管 Git 可见性，Local-first 管部署去向**，可以一起使用。
Production-direct 是一次长期授权，不再每次询问部署，但仍必须通过 Deployment Check。
在 `docs/project/rules.md` 填写必要测试、Build、阻断条件、已有部署要求和 Local / Preview 入口。

目标已有 AGENTS.md、CLAUDE.md 或其他 Bootstrap 专用路径时会报冲突，不覆盖、不自动合并。
Local-only 不能隐藏已跟踪文件，不能以 `git rm --cached` 处理冲突；先请项目负责人确定可用位置，
或用独立、无占用的工作区。Standard 按任务分支 + Review + Merge 提交；Local-only 不提交 Bootstrap。
Local-only 重复初始化会保留本地编辑，不重复询问、不升级文件。

**日常协作（下达任务约 1 分钟）**

1. 在目标项目启动 Agent，让它读取本地 AGENTS.md 与项目 skill。
2. 用语义描述任务：`修改 Auth / Login 的错误提示，让用户知道可以重试。只修改 NODE:login-message。`（节点 ID 用项目地图里的真实值。）
3. 等 Agent 完成任务分支上的修改、测试与独立 Review；PASS 后默认进 Merge Queue，基于最新 main 检查后合并并删除任务分支。
4. 需要亲自合并时，在任务里加 `require human merge`；Agent 在 PASS 后等待你合并。
5. 查看 Local / Preview 入口；Production-direct 则在 Review / Merge 和全部 Deployment Check 通过后自动发布。

Local-first 提供本地入口后停止；要发布生产，明确说「将当前版本部署到生产」——检查依然不能省略，
单次请求也不会改变长期模式。需要长期改模式时明确说「将 Deployment Mode 改为 Production-direct」，
由 Agent 写回 AGENTS.md；不要用重复 init 切换。

STS 阻止顺手扩展范围、无需求复杂度、违反明确边界、重复验证 / Agent 调用和未来假设机制。
「修改错误提示」不会顺便重构 Auth Service；但必要调用方、迁移和测试仍要做全，不能以少写代码省略。
Reviewer 只报 PASS / REQUEST_CHANGES，不改代码。失败由 Coder 修复，再测试和评审。

需要人介入：必须扩大严格节点边界、选择 `require human merge`、Local-first 明确请求生产发布，
或缺少项目入口 / 检查定义 / 必要权限。已给的长期授权不重复确认。
Local-only 下 Agent 会将规则、地图和报告保留在专用目录；任务提交只含实际任务内容，禁止 `git add -f` Bootstrap。

**Local-only 退场（约 1 分钟，在目标项目执行）**

1. 运行 `python .bootstrap/bootstrap.py deinit .` 预览清理范围。
2. 把需要保留的本地规则、地图或笔记备份到项目外。
3. 确认删除后运行 `python .bootstrap/bootstrap.py deinit . --yes`。
4. 运行 `git status --short`，确认没有 Bootstrap 残留。

清理会删除本地 Bootstrap 的全部后续编辑和生成物，并移除自己的 Git exclude 区块；
原有文件、原有目录、其他 exclude 条目和已完成任务提交保留。Standard 不适用此命令。
如果产物曾被强制跟踪或目录被换成链接，命令停止并说明位置；不要强行删除。

下一步（1 分钟）：在上表选择 Standard 或 Local-only，再执行对应初始化命令。
