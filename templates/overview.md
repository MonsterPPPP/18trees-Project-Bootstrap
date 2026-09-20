# 从用户目标开始

先在 Agent 对话框说明目标；需要查看时让 Agent 打开 [项目地图](map.html)。
操作示例见 [使用说明](usage.md)，人无需运行安装或地图命令。
初始化节点是规划状态；请先补充产品目标，再实现功能。

| 需要说明 | 填写内容 |
|---|---|
| 产品目标 | 用户是谁；最需要完成什么任务 |
| 操作入口 | 启动命令或可点击入口；预期看到什么 |
| 完成标准 | 用户可观察的结果与验证方式 |
| 当前限制 | 尚未实现的能力、已知约束 |

提出修改时使用「修改 Auth / Session Management，让用户……」这样的语义表达。
仅允许单节点时明确说「只修改 NODE:X」。技术定位由 Agent 负责，文件、类、函数放进 metadata。
四层固定为 Product → Feature / User Flow → Capability → System / Technical Layer；人主要操作前三层。
完整规则见 [协作接口](../../.bootstrap/interface-spec.md) 与 [长期规则](rules.md)。
Codebase → Semantic Project Manifest → HTML Project Map；HTML 不是编辑入口或真相源。
任务完成后只在语义或结构改变时同步，不为内部实现调整更新地图。

进度写法：「5 步中的第 3 步已完成；现在可以……」。本文只写理解与操作所需的信息，不复述代码。

下一步（1 分钟）：对 Agent 说出产品目标，由它补充本页。
