# 长期规则

在对话中告诉 Agent 需要长期保留的决定，由它记录在这里；规则不能只存在于聊天。
涉及 Agent 行为的规则也可直接写入 AGENTS.md。只保留当前有效规则，不堆积聊天记录。

| 项目 | 内容 |
|---|---|
| 规则 | 一句可执行要求 |
| 适用范围 | Product / Feature / Capability 或 NODE:X |
| 原因与证据 | 为什么需要；对应项目决策或代码证据 |
| 验证方法 | 可观察的成功标准 |
| 更新条件 | 何时重新审视；由谁决定 |

新增规则不得默默放宽 Strict Node Boundary。工程细节沿用
[ponytail](https://github.com/DietrichGebert/ponytail)，不创建平行编码规范。
输出沿用 [i-have-adhd](https://github.com/ayghri/i-have-adhd)，地图沿用
[archify](https://github.com/tt-a1i/archify)；完整约束见 [接口规范](../../.bootstrap/interface-spec.md)。

**Deployment Check · 项目自定义**

部署模式只读取根目录 `AGENTS.md` 的 `Deployment Mode`，不在这里维护第二份模式值。
由 Agent 根据项目技术栈和已授权决定填写下表；尚未填写不等于检查通过。Bootstrap 不提供假成功命令或统一 CI/CD。

| 项目 | 本项目命令 / 入口与通过标准 |
|---|---|
| 必要测试 | 待定义：命令、覆盖范围与通过标准 |
| Build | 待定义：构建命令、产物与成功标准 |
| 阻断检查与已有部署要求 | 待定义：全部阻断项、既有发布条件与各项通过标准 |
| Production 执行 | 待定义：目标环境、部署命令 / 流水线、待部署版本及结果验证；需满足 AGENTS.md 的授权模式 |
| Local / Preview | 待定义：启动命令、可查看入口与可访问验证方式 |

每次 Production Deployment 前，对实际待部署版本记录命令 / 检查结果与是否存在阻断项。
必要测试通过、Build 成功、无阻断失败且满足项目已有部署要求，才算 Deployment Check 通过。
模式已是 Production-direct 时不要再次询问是否部署；有失败或配置缺失时处理具体阻碍，不能跳过检查。

下一步（1 分钟）：告诉 Agent 你期望如何验收当前任务，由它补充验证入口。
