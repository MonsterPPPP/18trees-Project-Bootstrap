# 工具链契约

运行 `python bootstrap.py --help` 查看初始化、校验和地图生成入口。
常规运行依赖只有 Python、`jsonschema` 和生成时调用的外部 Node.js / archify；浏览已有 HTML 不需要这些环境。可选低成本能力另复用 acpx 与本机 DSH。

**Manifest v1**

1. `nodes`：稳定 `NODE:X`、固定层级、名称、语义摘要、planned / implemented 状态与独立 metadata。
2. `relationships`：相邻层 contains、Feature 顺序 precedes、同层能力或系统依赖 depends_on、能力或系统数据流 data_flow。
3. `workflows`：稳定 `FLOW:X`、Product 引用与有序 Feature 节点；每个 Feature 至少进入一个流程。
4. `metadata.references`：仓库相对 path、类或函数 symbols、evidence 说明；绝对路径和上级目录跳转被拒绝。
5. 已实现节点必须有证据，已实现的前三层还需有下一层已实现节点；空项目允许规划节点或只有产品的空流程。

JSON Schema 使用 Draft 2020-12；`schema/semantic-project.schema.json` 为结构约束源。
脚本另检查 ID 唯一、端点存在、层级合法、产品可达性、流程所属产品、顺序边完整与重复关系。
Workflow 是有序且不重复节点的一次用户旅程；有重试循环时分别描述重试旅程，不在同一 steps 中重复节点。
多个 Product 与共享 Capability 均支持；依赖与数据流可以构成真实业务循环，不擅自拒绝。

**初始化与文件安全**

人通过项目 Agent 安装，执行流程见 [INSTALL.md](../INSTALL.md)。CLI 是 Agent 的内部工具。
init 仅在完整 Bootstrap 源仓库执行；目标内副本支持 map、validate、verify-install 与 deinit。
目标就是当前 Bootstrap 源仓库时不运行 `init`；保留源仓库的 Standard 规则，直接按 Gateway Flow 维护规范、模板与工具链。
普通目标正文默认 Local-only；无生产目标时 CLI 默认 Local-first，文档接入默认 isolated。Production-direct、indexed 与 Standard 必须由宿主 Agent 在取得明确授权后传入。
CLI 不识别生产 URL、不调用选择工具，也不证明授权来源；安装 Agent 负责目标发现与冲突检查。

初始化会检测目标 Git 根目录与现有 remote；普通目标不在其他仓库内时没有 Git 就执行 `git init`。
Agent 必须分别传入/询问 `--git-remote-setup` 与 `--git-push-mode`；交互 CLI 也会逐项询问。推送选择默认 Local-only，已有 remote 不自动构成推送授权。
远端可选 existing、create（GitHub CLI）、url、local；多 remote 时必须指定名称。新仓库默认 private，创建只加 remote，不暂存、提交或 push。
GitHub CLI 不可用/未认证且没有 URL 时仍允许本地安装，配置记为 Remote-pending；Remote-auto 在远端可用前暂停同步。项目 AGENTS.md 记录 Git Remote Setup、Git Push Mode 与获准使用的 Git Remote Name，部署模式仍单独配置。多个 remote 时必须记录用户选中的名称。缺失项目名时交互询问；非交互 CLI 要求 `--name`。

Local-only 正文安装在 .project-bootstrap/。isolated 使用两个本地薄入口；indexed 向存在的 AGENTS.md、CLAUDE.md、.claude/CLAUDE.md 追加条件索引，缺对应核心文档则使用薄入口。
核心文档不被整体替换；tracked 核心文档仅索引可见可提交，其他产物仍排除。覆盖入口冲突先停止，不擅改其他规则。
索引只追加到 UTF-8（可带 BOM）文档，原字节和换行保留；其他编码先停止交用户决定，不混写或自动转换。
索引使用普通条件文字，不用无条件 @ 导入；没有本地规则就忽略，不给其他协作者安装或授权。
新状态 version 3 记录 agent_doc_mode、entry_existed、indexed_entries、reused_entries，区块模板为固定内容，不从状态接受任意待删除文本。
v2 状态继续按原 isolated 模式检查/卸载，不补写或静默迁移。已提交相同索引复用；Git checkout 导致 CRLF 时按实际区块字节核对和移除。
Standard 保留既有路径，另增加 docs/project/usage.md；两种模式的手册均直接复制 MANUAL.md。
重复本地安装执行 verify-install，不覆盖编辑；Standard 相同内容跳过、不同内容报冲突。
旧版 Local-only 要先备份并经确认卸载，不自动迁移；源码保留旧版 deinit 路径。

Git includeIf 根据当前实际 Git directory 绑定自有 config/exclude 文件，不影响其他 worktree。
自有 exclude 复制有效 core.excludesFile 的规则（未配置时使用 Git 默认 XDG 路径），再添加 Bootstrap 范围；
verify-install 重新读取继承规则并刷新，保留原全局配置、共享 info/exclude 和项目 .gitignore。
排除刷新失败恢复刷新前内容。不能覆盖更高优先级的 Git 配置或项目否定 ignore 规则，发现可见性失败即报错。
配置与薄入口先写同目录临时文件，再原子替换，部分写入不会截断原文件。
安装失败删除本次文件和区块，恢复原入口；原未提交任务与索引不变。
移动工作区会使绑定失效，verify-install 报错；移回原位置后卸载，再在新位置安装。
Git directory 含 glob 或引号/换行等不能安全绑定的字符时拒绝；不通过模糊匹配扩大作用范围。
同一仓库的安装与卸载串行执行；不声称提供并发事务或防人为强制添加机制。

verify-install <目标> 核对本地状态、薄入口、模式、Git 排除和 manifest/map 一致性。
它只做技术自查，不证明规则无冲突或独立验收通过。安装 CLI 输出文件落地、等待验收，不报告初始化完成。
安装 Agent 按 INSTALL.md 完成写入前语义冲突检查和写入后只读 Installation Verifier；两者是 Agent 行为协议，不是脚本自动推理。
诊断冲突时目标项目零写入；无子 Agent、失败或未 PASS 保留未完成状态，不伪造结果。新增 worktree 也需接入并验收。
map 的本地输出限制在 .project-bootstrap/docs/；后续生成物同样不能散落到任务目录。
deinit <目标> 仅预览，确认后 --yes 删除专属目录、本次拥有的入口/索引区块与条件配置；保留原文、既有复用索引和其他配置。
已跟踪索引删除产生普通 Git 差异，不改索引区之外的用户编辑、Git 暂存区或提交历史。
除授权的 indexed 核心文档外，检测到跟踪/暂存本地产物、symlink / junction 或清理区块损坏时先停止；不修改索引或遍历外部目录。

部署配置：Standard 位于根 AGENTS.md，Local-only 位于 .project-bootstrap/AGENTS.md。
重复 init 不用于模式切换；用户明确改变授权时由 Agent 写回配置，原项目限制不能被默认值放宽。

地图生成先在临时文件中完成 archify 交付与一致性验证，再原子替换指定 HTML。
无效 manifest、缺失 renderer 或 archify 诊断失败不会替换旧地图。
极长节点名称可能触发 archify 排版诊断，生成器会明确报错；调整语义名称或在生成器中修正排版，不能忽略失败。

**离线地图与 archify**

生成器将每个 Product / Feature Workflow 转换为 archify 的 workflow spec，
真实执行 `deliver --quality showcase --json`，必须通过 9/9 检查、零错误和零警告。
每页最多 3 个流程节点；长流程分页共享端点，全部顺序保留。完整四层和所有关系在页面下方可点击卡片中展开，
关系显示语义名称，metadata 默认折叠。流程箭头表示顺序，具体关系 label 在对应节点卡片保留。

archify 2.15.0 原始 viewer 有可选 Google Fonts 链接。Bootstrap 在惰性 JSON 数据中保存
未改动的原始 HTML 与 SHA-256 交付收据；挂载 iframe 前，仅从显示副本移除 Google Fonts / gstatic link。
字体使用系统回退，不下载字体。外层 CSP 禁止网络连接与外部样式，iframe 使用 sandbox。
因此原始 archify 收据仍对应原始字节，Bootstrap 页面另做浏览器离线验收，不能混称同一份产物。
HTML 包含内联样式、脚本、SVG 和数据，打开无需本地服务、CDN 或网络请求。
上游渲染代码生成在 HTML 中，不把上游 skill 正文或源码包复制进仓库。

**一致性校验的能力边界**

`validate --map` 对比内嵌 manifest、派生 workflow spec、原始 archify HTML 的 SHA-256 / 字节数、
交付收据和整个可见页面的确定性重新构建。仅改可见标题或保留旧地图也会失败；JSON 对象键顺序不会造成误报。
收据没有签名，这些检查用于识别失同步或意外修改，不是防恶意篡改证明。
工具不扫描真实代码来推断语义，也不证明 metadata 路径存在或行为正确。
按 [接口规范](interface-spec.md) 阅读代码是 Agent 的责任。

**本机浏览器验收（约 20 秒）**

```powershell
python -m pip install playwright
python tests/browser_check.py artifacts/synthetic-map.html --browser /path/to/chrome-or-edge
```

Playwright 仅为可选验收依赖，运行时不需要。脚本使用已有 Chromium / Chrome / Edge，
不下载浏览器；在离线 context 中检查请求、脚本异常、首页入口、四层、metadata、流程切换与横向溢出，
并输出四个桌面尺寸的亮暗截图。整页语义索引允许纵向滚动，不宣称整个索引适合一屏。
截图必须人工查看，自动收据不会代替视觉判断。

**可选低成本 CLI 子 Agent v1**

初始化的可选能力为主 Agent → acpx → 本机 DSH 原生 ACP，详见源码的 `docs/low-cost-agent.md`，
安装后为工具目录中的 `low-cost-agent.md`。此说明、工具和简短规则随既有两种布局分发。
首次没有机器选择时由宿主询问启用/跳过，未回复不启用；已回答复用机器记录。
常规初始化不依赖此能力成功。机器进度使用 acpx 自有目录，公开项目入口不含密钥、个人路径或会话日志。
先真实握手与能力核对，再付费无工具烟测；复用只做低成本可用性检查，变化或失败才深入诊断。
缺凭据保存 unavailable 并给出最小续跑步骤，不虚构已调通，不重复安装、读取全套资料或默认重试。
主 Agent 优先考虑边界清楚、上下文少、容易验收的简单任务；成本接近直接完成则直接处理。
这是软性偏好，无评分服务、委派比例或强制路由。最小上下文交接、简短结果；主 Agent 保留最终验收。
默认只读，DSH 原生权限与 acpx 拒绝策略不放宽原任务授权；ACP 声明和 cwd 不是 OS 沙箱。
不引入 OpenClaw/protoAgent 框架，不复制上游 Skill 正文；详细资料按需引用，以本项目授权规则优先。

下一步（1 分钟）：运行 `python bootstrap.py validate examples/synthetic.manifest.json`。
