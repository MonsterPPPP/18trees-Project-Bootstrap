# 验收记录

运行 `python -m unittest discover -s tests -v` 复现工具链验收，预计 10 秒。

2026-09-20：5 步中的第 5 步已完成。环境为 Windows、Python 3.12.7、Node.js 24.12.0、
jsonschema 4.23.0、archify 2.15.0，浏览器使用本机 Edge / Chromium。

| 验收项 | 结果与证据 |
|---|---|
| 最小测试 | 9/9 通过；真实调用 archify，覆盖临时目录全链路、幂等、冲突预检、链接目录拒绝、失败保留旧图、非法 manifest、长流程、不可信文本与地图失同步 |
| 新项目初始化 | 新建 13 个文件；重复执行新增 0 个文件，既有字节与修改时间不变；两份项目 skill 内容相同 |
| 结构与地图一致性 | 空项目与完整四层合成示例均通过；原始 archify workflow 为 9/9 showcase，零错误、零警告 |
| 浏览器离线验收 | 两种地图均在 1440×900、1600×1000、1920×1080、2048×1320 通过；零网络请求、零脚本异常、无横向溢出；首页入口、四层、metadata 折叠与展开正常 |
| Skill 与视觉检查 | 项目 skill 通过 quick_validate；已查看合成地图最小尺寸亮色与最大尺寸暗色截图，文字、节点与连线可读 |

**本地复现（约 30 秒）**

1. 设置 `ARCHIFY_HOME` 为已安装的 archify 目录。
2. 运行 `python -m unittest discover -s tests -v`。
3. 运行 `python bootstrap.py map examples/synthetic.manifest.json --output artifacts/synthetic-map.html`。
4. 运行 `python bootstrap.py validate examples/synthetic.manifest.json --map artifacts/synthetic-map.html`。
5. 安装可选 Playwright 后运行 `python tests/browser_check.py artifacts/synthetic-map.html --browser /path/to/chrome-or-edge`。

本次生成的入口为 `artifacts/synthetic-map.html` 与 `artifacts/fresh-project/docs/project/map.html`。
截图与浏览器 JSON 收据位于 `artifacts/browser/`、`artifacts/browser-fresh/`。
这些可再生成产物被 Git 忽略，提交中只保留合成 manifest、生成器和可复现测试。

**合成示例交付收据**

| 对象 | SHA-256 |
|---|---|
| archify workflow spec，714 bytes | `1555917802069376c11ac8c9b58721c23faf89d56761c191523cd11527c82171` |
| 原始 archify HTML，624571 bytes | `84bc72753045087dfd79da0c7622a959f419585be9ccd1d056da736a328c2b0a` |
| Bootstrap 自包含 HTML | `137049cf6a75053d076fd252d7620d107dbcab45d75b4ef527610920878d68b7` |

图类型：workflow；原始产物验证：9/9 showcase；Bootstrap 视觉检查：passed。
本记录只对应本次生成字节；修改 manifest、模板或 archify 版本后应重新生成与验收。

**验证边界**

archify 原生 `visual-check` 在本机 Edge 提前退出，未得到成功收据；上述浏览器结论来自
`tests/browser_check.py` 的独立 Playwright 检查，未将原生失败描述为成功。
项目 skill 已检查格式与安装位置，但未启动 Codex / Claude Code 做客户端行为评测。
Strict Node Boundary、代码证据和语义同步判断仍由 Agent 执行，工具不自动证明这些语义事实。
阅读完整四层索引需要纵向滚动；验收未宣称整页索引可放入一屏。

**Gateway Flow 追加验收**

2026-09-20：规范、AGENTS.md 模板与现有项目 skill 增加 Gateway Flow；没有新增工具、
自动化脚本、依赖或业务实现。初始化文件数仍为 13，原有地图生成与同步协议不变。

| 验收项 | 实际结果 |
|---|---|
| 规范完整性 | 接口规范和 AGENTS.md 模板均包含 10 节：分支、独立 Review、Ready 顺序、最新 main 验证、冲突回路、角色、人工开关与 main 保护 |
| 新项目安装 | 在全新 TemporaryDirectory 内执行 CLI 初始化；逐字节比较安装的 AGENTS.md、接口规范与两份 skill，均等于仓库源文件；核对十节与关键 gate；地图一致性通过 |
| 幂等与回归 | 相同 CLI 再执行新增 0 个文件；`python -m unittest discover -s tests -v` 为 9/9；项目 skill 的 quick_validate 通过 |
| 合成 Review A | 不继承会话的独立 Subagent，输入仅含五类评审资料；单节点说明修正得到 PASS，修改要求为无 |
| 合成 Review B | 另一个干净上下文收到额外修改重试实现的 Diff，得到 REQUEST_CHANGES；指出 Strict Node Boundary 越界，要求移除越界改动、补充验证命令并重新评审 |

两次契约演练使用合成任务、Diff 与测试记录作为输入，不代表运行了业务代码测试；
Reviewer 未收到预期判定或 Coder 结论，仅只读规范并给出决定。
样例说明参见 [接口规范](interface-spec.md) 的 Review Subagent 独立执行契约。
本次没有远端仓库配置，不能验证服务端分支保护或托管 Merge Queue；规范不声称初始化会配置这些服务。
首次初始化演练使用的较长示例名触发 archify 既有宽度校验；改用「合成验收」后通过，未改动渲染器。

**Deployment 追加验收**

2026-09-20：在现有初始化命令加入 Deployment Mode 选择，不新增工具、依赖、CI/CD 或业务实现。
根 AGENTS.md 保存唯一模式值，`docs/project/rules.md` 保存项目自定义 Deployment Check。

| 验收项 | 实际结果 |
|---|---|
| 默认与显式 CLI | 全新临时目录的无选项、显式 Local-first、显式 Production-direct 均成功；生成 AGENTS.md 与对应模式的完整模板一致，地图校验通过 |
| 交互选择 | 经 CLI main 的 TTY 分支，用模拟终端输入验证回车 / 1 → Local-first、2 → Production-direct；无效输入与 EOF 拒绝写入 |
| 长期配置与冲突 | 重复初始化保留已有模式且不再提问，含 Production-direct；传另一模式报冲突，原有文件字节与修改时间不变；非法 CLI 选项不创建目录 |
| 规范与 Gateway Flow | 完整 4 节、两种流程、长期授权、不跳过检查、阶段分离与人工合并边界已进入规范 / 模板 / skill；未改变既有 Gateway Flow gate |
| 回归与安装 | 11/11 测试通过，skill 格式校验通过；两种合成项目的 AGENTS.md、长期规则、完整规范和两份 skill 均核对来源，地图一致 |

复现：`python -m unittest discover -s tests -v`，约 15 秒。
本次本地样例为 `artifacts/deployment-local/AGENTS.md` 与 `artifacts/deployment-production/AGENTS.md`；
均为合成验证项目，不含真实生产目标或部署凭据。仅验证配置安装与规范，不宣称执行了真实部署。
已有地图渲染代码与页面模板未修改，未重复浏览器视觉验收。

**STS + Local-only + 使用手册追加验收**

2026-09-20：三个需求一起验证。`python -m unittest discover -s tests -v` 为 15/15 通过，
项目 skill 格式检查通过。新增测试覆盖 Git 可见性、卸载数据安全与共享工作区拒绝边界。

| 验收项 | 证据 |
|---|---|
| STS 规范 | 已读取上游 README / SKILL，仅链接接入；规范与 AGENTS.md 模板的指定引文逐字相等，结构包含 Engineering Protocol 下的 Ponytail / STS，登录提示例与五项 Reviewer 检查齐全 |
| 初始化 | Standard 13 文件；Local-only 14 文件（含本地安装记录）；最终版在单工作区合成仓库初始化、manifest / map 校验与卸载通过，Git status / diff 干净，无 `.gitignore` 修改 |
| 任务边界 | 登录提示任务的 `git add .`、提交和 main 差异均只含 `login-message.txt`；生命周期测试同样验证最终实现仅暂存和提交任务文件 |
| 手册全链路 | 按实际 CLI 初始化 → 以 NODE:login-message 下达严格边界任务 → 测试 → 干净上下文 Review PASS → 最新 main 集成检查 → Merge → 删除任务分支 → 预览 deinit → `--yes` 清理完成 |
| 退场与失败 | 清理后仅剩 `.git` 与真实任务文本，exclude 恢复原字节；单测另验证后追加 exclude/原有空目录保留、重复初始化保留本地编辑、已跟踪冲突/链接拒绝、项目否定 ignore 规则导致初始化回滚 |

合成手册任务只修改文本，不实现登录业务。其独立 Review 只接收原始任务、边界、Diff、测试结果与规范，
结论为 PASS，修改要求为无。原始 head 为 `20d7938652636d8f61eb2abe96583402eb632498`，
合成仓库保留在 `artifacts/manual-walkthrough`；已卸载 Bootstrap，真实合成任务提交仍保留。
Standard 示例保留在 `artifacts/manual-standard` 的文件快照，已移除其 linked worktree 注册。
初次手册演练使用同仓库的两个 worktree，独立 Review 发现共享 exclude 会隐藏 Standard 未提交文件；
最终版改为写入前拒绝多个 worktree。回归检查先 Standard 初始化、再尝试另一工作区的 Local-only，
确认明确报错、exclude 不变、Standard status 不变且全部 13 个文件仍可普通暂存。
移除合成 linked worktree 后，用最终版重走同一仓库的 Local-only 初始化、校验、预览与卸载，
exclude 原字节和已评审任务提交均保留，项目只剩 `.git` 与 `login-message.txt`。
另验证安装后误加 worktree 时仍可 deinit，以恢复共享排除文件。

本次只新增初始化/清理能力，不改变 Gateway Flow 或 Deployment 的授权语义；
已有地图渲染器与页面未变，不重复视觉测试；无生产部署。Git exclude 是本地可见性机制，不是强制提交拦截器。

下一步（1 分钟）：打开 [中文使用手册](../MANUAL.md)，选择适合当前项目的初始化命令。


**Agent 对话入口追加验收（2026-09-20）**

本节对应 Agent-first 更新；前述 13/14 文件和单 worktree 限制属于旧版记录。
新版 Local-only 使用 .project-bootstrap/ 与两个薄入口，Standard 增加 usage.md。

| 验收项 | 本轮证据 |
|---|---|
| 工具链 | 20 项 unittest 通过；覆盖原 AGENTS/CLAUDE、现有文档/manifest、未提交任务、薄入口原文及后来编辑保留；skill 格式校验通过 |
| 隔离与恢复 | 两个 worktree 分别安装、卸载，第三个 Standard 工作区的状态与暂存可见性保留；继承排除规则刷新；安装失败恢复文件与 Git 配置；拒绝跟踪文件/链接；旧版只显式卸载、不自动迁移 |
| Codex 新会话 | 真实 codex exec 新会话读取原 AGENTS 标记 ORIGINAL_CODEX_CEDAR 和本地 BOOTSTRAP_LOCAL_MAPLE，正确报告 Local-only、Local-first 与 Source of Truth；只读执行，exit 0 |
| Claude Code 新会话 | 未通过环境验收：首次等待 180 秒无结果，关闭非必要 hooks/MCP 后 120 秒仍超时，日志反复 Connection error；本机合成传输检查也在 60 秒内未完成。已停止第三次后的重试，不声称规则加载成功 |
| 人类入口 | 真实 Codex 新会话只接收本地源码 URL 与一句安装请求，完成安装、规则读取、项目语义整理、地图校验和使用说明交付；MANUAL.md 同源安装为 usage.md |

一句话演练使用合成文档空项目，无真实业务实现；因源码无 GitHub remote，用本地 file URL 验证 Agent 接收仓库入口的流程，未声称验证 GitHub 网络下载。
最初受限沙箱缺少必要文件权限，Agent 正确报告失败且无残留；按本任务现有权限完成的会话输出 turn.completed。
演练工具等待超时后核对原始事件，确认 Agent 已交付最终结果；另独立核对 verify-install、安装前后 diff/status 与预览/执行卸载。
卸载后只剩原 .git、AGENTS.md、README.md、task.txt，原 dirty task 与 Git 配置恢复。

Claude Code 当前登录状态为已登录，但这不能证明模型连接或新会话可用。
可疑假设是该环境的原生 CLI 能完成非交互启动；需先恢复客户端会话能力，再补规则加载验收。
独立 Review 指出的部分写入截断风险已改为同目录临时文件写完后原子替换；
新增模拟部分写入后 OSError 的测试，验证配置、原入口、任务 diff/status 和残留全部恢复。
孤立 END 标记也在写入前拒绝，并验证无副作用。
本轮没有修改客户端全局配置、凭据或系统执行策略，没有生产发布。
CLI 与模板静态检查不能替代该项行为验收；此项通过前不宣称计划全部验收完成。

下一步（1 分钟）：打开 README 核对安装入口；客户端行为缺口见上表。
