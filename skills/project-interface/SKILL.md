---
name: project-interface
description: 在具有 project.manifest.json 的项目中按语义节点修改，执行严格节点边界、Gateway Flow 与项目 Deployment Mode，并判断任务结束时的地图同步。
---

先确定角色：
- Review Subagent：仅使用五类评审包，不自行读取代码库或 Coder 会话，直接执行 Gateway Flow Reviewer 契约。
- Installation Verifier：独立只读沿目标项目真实入口读取原规则、Bootstrap 规范与 skill，核对生效部署/文档模式、Git 边界和技术证据，
  用合成任务及 Strict Node Boundary 反例判断流程；只返回 PASS / REQUEST_CHANGES，不修改、提交或部署。执行接口规范中的安装验收契约，不跑下方编码流程。
- 安装 Agent：遵循源仓库 INSTALL.md 的生产目标发现、安全默认、必要授权、写入前冲突检查、安装和独立验收；不冒用以上两个角色替自己签字。

其他角色识别当前安装：Local-only 读取 `.project-bootstrap/AGENTS.md` 与 `.project-bootstrap/interface-spec.md`；
Standard 读取根 AGENTS.md 与 .bootstrap/interface-spec.md。原项目和嵌套规则继续适用，不静默覆盖。
Local-only 的文档、manifest、工具位于 .project-bootstrap/；下文 Standard 路径按该配置入口定位。
metadata 始终相对于目标项目根目录。人类只通过对话框操作，Agent 执行命令并返回可查看入口。

工程组合为 Ponytail + [Stop That Shit](https://github.com/lennney/stop-that-shit) + Semantic Boundary。
最小充分修改不等于最少代码；必要调用方、迁移与测试需完整完成，禁止无需求复杂度、范围膨胀、
未来假设与重复验证 / Agent 调用。Reviewer 在既有 gate 中按 STS 五项（Scope Creep、无需求复杂度、
违反明确边界、重复验证/Agent 调用、未来假设机制）判断，不优化或修改代码。完整定义见 Engineering Protocol。

Local-only 正文及产物只放 .project-bootstrap/；isolated 不改原文档，indexed 唯一可提交内容是用户授权的条件索引。
索引必须在本地规则不存在时忽略，不触发下载/安装、不要求协作者补齐；原文和未提交内容保持。
每次任务按模式核对：Local-only 执行 `python .project-bootstrap/bootstrap.py verify-install .` 刷新排除并验证安装；Standard 执行 `python .bootstrap/bootstrap.py validate project.manifest.json --map docs/project/map.html`。使用安装记录中的外部 Python，不假定系统默认 Python 含依赖。
新建 worktree 后由 Agent 按源仓库 INSTALL.md 接入，验证前不声称已继承；不要求人执行安装命令。
首次安装先识别生产目标；无目标默认 Local-first，有目标时向人展示并明确询问 Production-direct 授权。文档模式默认 isolated；只有人提出 indexed 时才检查具体索引范围并取得明确授权。
选择工具只问发现后确实需要的授权；无工具时在对话中询问。重复安装沿用已记录的选择。正文默认 Local-only，Standard 必须另外明确要求，安装源码与依赖放项目外。
写入前读取实际生效旧规则及引用流程；不兼容就零写入终止，列出来源、冲突及待裁决事项，等用户决定后重查。
允许索引不允许改写旧规则；indexed 在 Task Branch 只追加带标记区块，不批量改嵌套文件。
技术检查后必须自动启动 Installation Verifier，PASS 前只能报告文件已落地；父 Agent 自查不能代替独立验收。
退出请求先预览 deinit，备份必要内容，获确认后加 --yes；保留原规则和实际任务改动。
旧版安装先备份和确认卸载，不静默迁移。Local-only 改变 Git 可见性，不改变 Gateway / Deployment 授权。


1. 从 `project.manifest.json` 定位 Product、Feature / User Flow、Capability；追踪 contains、precedes、depends_on、data_flow 与 metadata，再读代码核实证据。HTML 只是 Codebase → Manifest → HTML 链的输出。
2. 按 [ponytail](https://github.com/DietrichGebert/ponytail) 选择最少语义节点、最小影响的正确修改。明确「只修改 NODE:X」是硬边界，不自动包含子节点或依赖；边界外只读。若必须修改其他节点，停止并说明原因，等人重新定义边界，不通过修改 metadata 扩权。
3. 人类输出遵循 [i-have-adhd](https://github.com/ayghri/i-have-adhd) 与 AGENTS.md：行动置顶、每组至多 5 项、每轮进度与具体时间、结果可见、结尾一个 2 分钟内行动。长期规则写入 AGENTS.md 或 `docs/project/rules.md`；人类文档不复述代码。
4. 有效任务结束后按接口规范判断 Semantic / Structural Change。新增功能、能力、服务、数据流、链路变化、拆分合并、系统边界、新外部依赖进入核心流程才同步；语义未变的样式、重构、Bug、算法或实现替换不更新。禁止按 commit 或文件实时同步。
5. 需要同步时先核实代码，再编辑 manifest，运行 `python .bootstrap/bootstrap.py validate project.manifest.json`、`python .bootstrap/bootstrap.py map project.manifest.json --output docs/project/map.html`、`python .bootstrap/bootstrap.py validate project.manifest.json --map docs/project/map.html`。生成依赖外部 [archify](https://github.com/tt-a1i/archify)，CLI 缺失时说明安装或 `--archify` 路径，不伪造地图成功。

地图以 Product / Feature Workflow 为首页，四层明确分开，metadata 默认折叠。
CLI 校验不证明语义证据正确，也不自动强制节点实现边界；这两项由 Agent 核实。

**可选低成本 CLI 子 Agent**

机器选择与能力状态用 `python .bootstrap/bootstrap.py agent setup --cwd .` 读取；首次未选择才询问启用/跳过，已回答不重复问。入口与续跑说明见 `.bootstrap/low-cost-agent.md`。
优先考虑边界清楚、上下文少、容易核验的简单只读工作；交接、等待、验收与返工成本接近直接完成时直接处理。无评分、固定比例或强制委派。
最小任务包包含范围、必要上下文、预期与验收；要求简短结果、产物位置、验证和阻塞，不回灌全部推理/事件。相关任务可复用会话，无关任务用新会话。
主 Agent 保留最终验收，按风险核验；明显失败及时接手，不默认重试或递归委派。不可用不阻塞无关工作，不宣称未经测量的节省。
权限不超过原授权；不全量批准、不放宽 DSH 沙箱，不把 ACP 声明或 cwd 当成 OS 隔离。上游 acpx Skill 按需参考，本项目规则优先。

**Gateway Flow 角色路由**

手工任务 worktree、合成项目和验收产物先核对仓库根、实际路径及 Git 忽略结果，只放仓库内已忽略目录（优先 `.work/`）。无安全位置时用当前工作树任务分支；无法安全切换就报告阻塞，不在仓库外建兄弟目录，不擅改 Local-only 项目 `.gitignore`。
先读取当前协作入口 Git Completion Mode：Auto 必须继续到提交/PR/合并/同步/清理，不在 Review PASS 后结束或重复请求已有授权；Manual 提交并开 PR 后等人合并；Unselected 不授予完整交付，旧安装只沿用旧授权。
先提交自己的任务改动，Review 绑定该 head；不得暂存用户其他修改。确实无法访问选中 remote 或执行 PR 操作时 Auto 完成本地队列合并及安全工作树同步，明确远端未同步；保留待远端交付分支。审批、检查、冲突、队列等待不属于远端不可用，不能本地合并兜底；保护查询失败也不能单独触发兜底。Manual 无可用远端时只留本地提交。恢复远端后重新同步检查，从任务分支交付 PR，不直接 push main。
宿主 Agent 只读核对实际 PR 目标分支、有效保护/Ruleset、head、审批、检查、冲突、队列和权限。查询失败记“未核对”，不能误报无保护；仅保护 API 不可读不停止交付，按可获得的 PR 门禁与平台操作继续判断，必要门禁无法确认或平台拒绝合并则保留 PR 并说明原因。
Auto 等待必需审批时保存 PR 链接、head、分支和具体要求，保持 Auto，报告“等待必需审批”，不报告交付完成；子 Agent PASS 不替代远端审批。恢复时重新核对 head、最新主分支和门禁，不能无条件套用旧 head 的 PASS；主分支前移使旧集成结果失效。任务实现未变的无冲突同步可沿用 Review；实现改变或冲突适配重新测试、Review、入队。
Manual 或有效 require human merge 始终等人最终合并，不启用自动合并；Auto 的审批满足后继续自动交付。只有已有平台队列/自动合并能保障最新主分支集成检查与全部有效门禁时才使用，否则下次 Agent 恢复时继续，不承诺持续监测。
既有 require human merge、更严格原规则和生产约束优先。每次最终回复写已提交/PR/本地合并/远端合并/同步/分支清理的实际状态，未完成说明阻塞和续跑入口；不要以 Review PASS 代替交付完成。
交付收尾先保存必要结论，核对提交、PR、目录归属和未提交内容；用 `git worktree remove` 注销不用的工作树，删除本任务合成目录，再核对 `git worktree list` 与路径。只清理已确认归属的内容；等待合并或审批时仅保留续跑必要的仓库内目录并说明原因。
安装 Agent 必须在技术与独立安装验收后发送标准回执，用 report-install 保存既有 installation-check.md，区块外一次记录保护状态、有效要求和未核对项，展示配置、能力可用状态和后续行为；只有真实独立 PASS 才称基础初始化成功。没有保护是正常状态，日常成功回执不重复提醒；实际阻碍首次出现、变化或需要用户行动时才说明具体要求。

读取 `.bootstrap/interface-spec.md` 中完整的《Git Workflow（Gateway Flow）》与 Review Subagent 契约。
按收到的角色工作；不得把 Reviewer 角色当成编码任务，也不能把 Coder 自审视为独立 Review。

1. Coding Agent：先从最新 main 创建 `feat/<task>`、`fix/<task>`、`refactor/<task>` 或 `chore/<task>`；一分支一任务，按 ponytail 最小实现，禁止直接修改或 push main。实现、测试和必要的地图/文档同步完成后，自动启动 Review Subagent，无需人触发。
2. 评审交接：启动全新、不继承会话的 Reviewer，只交付原始任务与验收、Semantic Node 与边界、当前 Diff（base/head）、对应测试结果、ponytail 与 Bootstrap 规范。不得夹带 Coder 推理或结论；Reviewer 证据不足时要求补足 Diff 上下文或测试结果。
3. Review Agent：只读检查需求、Strict Node Boundary、最小实现、不必要复杂度/重构/依赖、测试风险、回归和必要的语义同步；只按契约输出 PASS 或 REQUEST_CHANGES，加原因与修改要求，不修改或合并。REQUEST_CHANGES 返回 Coder 修改、测试，再用新上下文 Review；硬边界受阻停止，连续三次修复失败检查假设。
4. Merge Queue：Ready = 开发完成 + 本分支测试通过 + 当前 head Review PASS，先 Ready 先入队。默认自动串行合并；队首同步最新 main、检查冲突、重跑 Integration Checks，检查后 main 前移则重新验证。旧 PASS 不无条件授权 Merge；冲突/集成失败移出队列，交原 Coder 适配、测试、重新 Review、按新 Ready 顺序入队。前序任务未处理完时后续分支等待，不抢先解决未确定冲突；Reviewer 不参与修复。
5. Human：下达任务与边界；Manual 或有效 `require human merge` 时，PASS 后进入 WAIT_FOR_HUMAN_MERGE，不自动合并，也不免除最新 main 检查。Auto 等待远端必需审批保留模式，满足后继续；人的平台审批不由独立 Review 替代。由托管队列或一个协调 Agent 执行最终集成，交付后删除 Task Branch。main 必须遵守项目流程，是否启用远端保护由项目决定，无保护仍按 Bootstrap 门禁交付；缺独立评审、队列能力或必要权限时保留分支并报告，不能伪造服务端状态。

适配与冲突修复也服从 Strict Node Boundary，不自动包含子节点/依赖，不以改 metadata 扩权。
本 skill 是行为契约，不自动安装 CI、配置服务端保护或创建常驻队列服务。
Reviewer 输出使用规范中的机器间判定格式；其他角色继续使用面向人的行动优先格式。

**Deployment 阶段**

1. 非 Reviewer 角色主动读取当前协作配置入口的 `Deployment Mode` 与 `docs/project/rules.md` 的 Deployment Check；不重复询问模式，不擅自修改。无生产目标时默认 Local-first；Production-direct 必须由用户针对已识别目标明确授权，不得推断。
2. 先完成开发与验证，再按 `Development Complete → Testing / Deployment Check → Deployment Policy → Local / Preview / Production` 推进。Gateway Flow 不变；Production 必须完成 Review / Merge，Production-direct 不能绕过 `require human merge` 或从未合并分支发布。
3. Local-first：按 Git Completion Mode 与 Git Push Mode 完成授权范围内的交付；有本地预览入口时可提供查看。不得自动部署 Production；只有明确的单次生产请求才继续，且仍须通过 Deployment Check。单次生产请求不修改长期模式。
4. Production-direct：初始化的一次长期授权替代每次部署前确认；后续任务对待部署版本执行必要测试、成功 Build、全部阻断检查与项目已有部署要求，全部通过即自动部署 Production，不再次询问是否部署。不强制统一 CI/CD，不把缺失、未执行或失败的检查当作通过。
5. 配置、运行入口、权限或检查有具体阻碍时如实说明并处理；不伪造预览或部署成功。显式模式变更写回 AGENTS.md。Local-first 下若合并会触发自动生产发布，先按项目流程阻止该发布，不能分离则保留分支并报告；自动 Merge 不是生产授权。

Reviewer 仅从评审包检查上述规则与实际变更是否一致，不启动环境或部署。

下一步（1 分钟）：请人描述当前目标，由 Agent 定位节点与验证入口。
