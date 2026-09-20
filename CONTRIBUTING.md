# 贡献指南

## 先读什么

1. [docs/interface-spec.md](docs/interface-spec.md) —— 接口规范。改动前必须知道它定义了哪些语义。
2. [AGENTS.md](AGENTS.md) —— 本仓库自己的协作约定与 Gateway Flow。
3. [docs/verification.md](docs/verification.md) —— 已有的验收范围与**明确未验证的边界**。

## 开发流程

本仓库吃自己的狗粮：按 [AGENTS.md](AGENTS.md) 里定义的 **Gateway Flow** 开发。

从最新 `main` 创建 `feat/<task>`、`fix/<task>`、`refactor/<task>` 或 `chore/<task>`。
完成实现与测试后启动独立 Review；PASS 后按 Ready 顺序进入 Merge Queue，每次基于最新 `main` 重新验证。禁止直接修改或 push `main`。

## 硬性约束

### 1. 示例必须是合成数据

本仓库只交付规范、模板、skill 与工具链。**不实现业务、不包含真实项目数据、不复制私有项目内容。**
`examples/` 里的 manifest 是合成的四层规划，README 里的"登录失败提示"是合成任务——这类内容都不能变成真实业务实现。

### 2. 上游正文不入库

实现幅度用 [ponytail](https://github.com/DietrichGebert/ponytail)，停止条件用 [Stop That Shit](https://github.com/lennney/stop-that-shit)，交互用 [i-have-adhd](https://github.com/ayghri/i-have-adhd)，可视化用 [archify](https://github.com/tt-a1i/archify)。

**只链接引用，不复制上游正文。** 上游变了，引用仍然有效；复制了就会过期。

### 3. 不新增竞争性编码规范

本仓库不定义代码风格、测试规范或目录约定——那些由目标项目自己决定，或由 ponytail / Stop That Shit 覆盖。新增规范前先确认它不是已有上游规则的重复。

### 4. 不改坏"不污染目标项目"这条底线

任何改动都不能让 Bootstrap 文件进入目标项目的 Git 提交。具体检查：

- 安装前后 tracked / staged diff 不变，普通 `git status` 不增加 Bootstrap 条目
- 不改共享 `info/exclude`、不改全局 Git 配置、不改 `.gitignore`
- 薄入口对已有文件只追加自己的标记区块

### 5. 测试必须通过

```bash
python -m unittest discover -s tests -v
```

新增或修改工具链行为必须补测试。测试真实调用 archify；缺依赖时会失败而不是跳过——这是有意的。

## 改变语义或结构时

改了 `interface-spec.md` 的语义、`bootstrap.py` 的行为、或 `templates/` 里写入目标项目的内容，**必须在 [docs/verification.md](docs/verification.md) 追加一节验收记录**，包含：

- 本轮改了什么、为什么
- 实际验证了什么、用什么证据
- **明确写出哪些没验证**

最后一条是这个项目最重要的习惯。已有记录里的写法可以照抄，例如：

> Claude Code 侧此前三次尝试因超时 / Connection error 未完成，用户明确决定绕过——**这不是"通过"，是"未测"**。

把未验证的事写成通过，比没有验收记录更糟。

## 提交信息

```
规范：新增 XXX（附对应验收记录）
工具：修正 XXX（附回归测试）
模板：XXX 变更（附初始化文件数对比）
文档：README 补充 XXX
```

语义化小步提交。一个 PR 只做一件事。

## 提交 PR

描述里写清楚：

1. **改了什么、为什么**
2. **对应 interface-spec 的哪一节**
3. **验证证据**：跑了什么、结果是什么
4. **没验证的部分**（如果有）
