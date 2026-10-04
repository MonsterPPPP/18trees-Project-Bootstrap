# 可选低成本 CLI 子 Agent v1

主 Agent → acpx → 本机 DSH 原生 ACP。此能力可跳过，失败不阻塞常规 Bootstrap 或无关任务。
人只需在项目 Agent 对话框说“启用低成本子 Agent”或“跳过”；安装与诊断由 Agent 完成。

**安装 Agent 的入口**

在原项目规则冲突检查通过后，首次无机器选择记录时询问是否启用。明确回答后把
`--low-cost-agent enable|skip` 传给现有 `bootstrap.py init`。用户未回复时不选择、不安装，
报告 choice-required 并继续常规 Bootstrap；下一次安装会话仍需得到答复。
先用 `agent setup --cwd <目标>` 读取已有机器选择；已启用或跳过不重复询问。
本仓库是源码，不能对它运行 init；开发者仅执行下面的 agent setup。

```text
python <Bootstrap工具目录>/bootstrap.py agent setup --cwd <项目绝对路径> --choice enable --install
python <Bootstrap工具目录>/bootstrap.py agent setup --cwd <当前项目绝对路径>
python <Bootstrap工具目录>/bootstrap.py agent run --cwd <当前项目绝对路径> --file <最小任务包>
python <Bootstrap工具目录>/bootstrap.py agent run --cwd <当前项目绝对路径> --session <相关任务名称> --file -
```

工具目录为 Local-only 的 `.project-bootstrap` 或 Standard 的 `.bootstrap`；源码开发使用仓库外层。
`--file -` 用 stdin 传递任务，避免 shell 插值和长度限制。不得传递凭据或完整主会话。
返回 JSON 包含简短 text、ok、exitCode、stopReason；只有任务响应与提交 ID 对应、退出码 0、
`end_turn` 且无失败工具事件才算协议层完成。主 Agent 仍核对任务预期和产物。部分文本、取消、工具失败或错误不是成功。
权限请求默认拒绝，任务失败不重试，主 Agent 接手；此 v1 默认只读，不为写任务扩大权限。
本机 DSH 的提权参数使用原生沙箱模式名（例如 `workspace-write`），不是其他 Agent 的 `require_escalated`。
只有合成权限验证可按 DSH 原生拒绝后的流程发出一次请求，且客户端必须拒绝；正常委派不得把提权当成默认重试。

**机器复用与诊断**

复用 PATH 上的 DSH、Node 和 acpx；Windows npm 启动脚本解析到真实 Node + JS 参数数组，
不拼接命令字符串、不改执行策略。无法识别自定义包装器时报告入口未解析，由 Agent 核对原生安装
及当前官方说明后修复 PATH/安装位置；不猜命令、不升级 DSH。缺失 acpx 且启用并允许安装时仅补装 acpx。
Node 要满足当前 acpx 的 engine 要求；入口、版本或握手失败必须诊断，不声称所有版本都支持。

机器配置使用 acpx 原生 `~/.acpx/config.json` 的 `agents.bootstrap-dsh.argv`，保留其他配置和认证。
同目录 `bootstrap-dsh.json` 仅记录选择、版本、入口、状态、握手能力及烟测结果；
`bootstrap-dsh-read-only.yml` 是最后加载的 DSH 原生权限 patch。它们不入项目 Git，不保存凭据或日志。
配置冲突不覆盖无主的既有注册或手改 patch；项目同名覆盖也报错。正常调用不读全套上游文档。
新项目始终使用本次 `--cwd`；握手不创建模型请求。正常复用仅检查版本/入口、配置变化和握手，
不再安装或重跑付费烟测。DSH 配置/认证文件元信息变化、版本变化或上次失败后重新检查能力与烟测。
旧 Local-only 安装继续可核对和重复初始化，不静默补装或改写入口；新能力工具/规则只随新安装分发。
旧项目可由 Agent 使用外部源码的 agent 命令及本说明，项目入口升级仍按既有明确修改/迁移流程执行。

首次用 acpx 官方 runtime 初始化并读取真实协议能力、创建无 prompt 的会话、取消空闲工作并关闭，
再由 acpx CLI 发出“无工具，仅返回 BOOTSTRAP_DSH_OK”的小任务。ACP authenticate 成功只说明协议
认证完成；DSH 的模型认证由其原生凭据机制提供，只有真实烟测成功才标为 ready。
unavailable 会保存可续跑状态。缺凭据时让用户在 DSH 自有凭据入口完成认证，再执行 setup；
不打印 settings、config show、完整 startup 错误或会话日志，其中可能包含秘密。
不自动创建凭据、付费订阅或放宽权限。再次显式 `--choice enable|skip` 可改变机器选择。
普通项目初始化完成状态仍由 Installation Verifier 决定；可选能力状态单独报告。

**简短委派规则**

优先考虑边界清楚、上下文少、容易验收的简单任务；交接、等待、验收和返工总成本接近直接完成时主 Agent 直接做。
这是偏好，不评分、不要求比例、不解释每次决定。只给必要上下文、范围、预期与验收；
默认子 Agent 返回简短结果、产物位置、验证和阻塞，详细日志按需查看。
相关连续任务可用命名会话，无关任务用 exec。主 Agent 保留目标判断与最终验收责任，按风险核验；
明显失败及时接手，不默认反复重试或递归委派，不宣称未经测量的节省比例。

ACP 能力声明不授予任务权限，也不是 OS 沙箱。DSH 的原生 read-only + ask 及 acpx deny 策略
用于收窄权限，不保证任意插件、网络或同用户进程隔离；cwd 不是完整安全边界。
项目规则和原任务授权始终优先；敏感上下文、额外网络或插件能力需要主 Agent 按原授权判断。
上游 Skill 仅用于命令参考，不覆盖本项目软性委派与权限规则。

**权威入口（按需查阅）**

- [ACP 与索引](https://agentclientprotocol.com/llms.txt)
- [acpx 安装与当前 Agent Skill 安装说明](https://acpx.sh/install.html)：目前 Codex 用 `acpx --skill install acpx --agent codex --scope user`；其他宿主按该页选择或仅引用。
- [结构化自定义 Agent](https://acpx.sh/custom-agents.html)、[权限](https://acpx.sh/permissions.html)、[CLI 与状态](https://acpx.sh/CLI.html)
- [DSH CLI](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)、[原生 ACP](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/acp/acp/README.md)

**本机验证路径**

在项目外创建两个合成 Git 目录，以 skip 初始化一个，以 enable 初始化另一个；重复初始化和第三个
目录应复用机器选择、正确 cwd、无重复安装或付费烟测。执行固定响应任务后检查 ok / end_turn 和预期。
在合成目录发出受权限限制的写入请求，核对文件不存在、返回失败/拒绝；不要用用户文件做权限测试。
使用 acpx 命名会话的 `cancel` 对活动任务取消，核对未按成功验收，再 `sessions close`。
临时不可用入口/模型、权限不足及取消应分别保留非成功证据；未实测的项目明确标为未验证。
单元测试仅证明工具行为，不能替代真实 DSH 连接、模型结果与权限/取消验证。

下一步（1 分钟）：由主 Agent 执行 setup，查看 ready / skipped / unavailable 与续跑信息。
