# Project Bootstrap

```powershell
python bootstrap.py init ../my-project --name "我的产品" --archify /path/to/archify
```

用 Product、Feature、Capability 与 Agent 协作。初始化后打开目标项目的
`docs/project/map.html`，首页是 **Product / Feature Workflow**，不是文件树。
本仓库只提供规范与工具链；示例全部为合成规划，不包含业务实现。

**首次使用（约 3 分钟，下载时间另计）**

1. 安装 Python 3.12+ 与 Node.js 22+。
2. 在本仓库运行 `python -m pip install -r requirements.txt`。
3. 将 [archify](https://github.com/tt-a1i/archify) 安装到仓库外，例如 `git clone https://github.com/tt-a1i/archify ../archify`。
4. 执行 `python bootstrap.py init ../my-project --name "我的产品" --archify ../archify`。
5. 打开 `../my-project/docs/project/map.html`。

已有本地 archify 时可直接复用。生成器也会查找 `ARCHIFY_HOME`、`CODEX_HOME/skills/archify`
与当前目录 / 用户目录下的 `.agents/skills/archify`、`.claude/skills/archify`、`.codex/skills/archify`。
`--archify` 优先；指定错误路径会报错，不偷偷切换到其他安装。
已验证 archify 2.15.0；升级后应重跑测试。

**初始化完成后**

| 入口 | 用途 |
|---|---|
| `AGENTS.md`、`CLAUDE.md` | Codex / Claude Code 协作规则与导入入口 |
| `docs/project/overview.md`、`rules.md` | 给人的操作文档与长期规则 |
| `project.manifest.json`、`docs/project/map.html` | 语义投影与离线可视化 |
| `.agents/skills/project-interface/`、`.claude/skills/project-interface/` | 相同项目 skill，供两个 Agent 加载 |
| `.bootstrap/` | 可独立运行的校验与地图生成器、schema、接口规范 |

新目录自动生成 `planned` 产品与待定义流程，不推测业务已实现。
初始化相同内容可重复执行，第二次新增 0 个文件；已有不同内容时预检失败，保留原文件，
不自动追加或合并 AGENTS.md。项目已修改后请在空目录初始化并人工合并需要的内容；`init` 不是升级器。
上游三个 skill 只引用链接，不自动下载或复制其正文；目标项目安装的是本 Bootstrap 的接口 skill。
在新会话中让 Codex 或 Claude Code 加载项目 skill；本项目验证了文件格式、位置与内容一致性，未自动启动两个客户端执行行为评测。

**目标项目内维护地图（约 1 分钟）**

```powershell
python .bootstrap/bootstrap.py validate project.manifest.json
python .bootstrap/bootstrap.py map project.manifest.json --output docs/project/map.html --archify /path/to/archify
python .bootstrap/bootstrap.py validate project.manifest.json --map docs/project/map.html
```

只在有效任务结束且出现语义或结构变化后更新 manifest；样式、内部重构、Bug 修复、
算法优化与能力边界未变的实现替换不触发同步。具体判定见 [接口规范](docs/interface-spec.md)。
人说「只修改 NODE:X」时，Agent 必须守住该节点边界；CLI 不声称能自动证明代码所有权。

**验证工具链（约 10 秒）**

```powershell
python -m unittest discover -s tests -v
python bootstrap.py map examples/synthetic.manifest.json --output artifacts/synthetic-map.html
python bootstrap.py validate examples/synthetic.manifest.json --map artifacts/synthetic-map.html
```

若 archify 不在自动查找目录，先设置环境变量：PowerShell 使用 `$env:ARCHIFY_HOME='/path/to/archify'`，
POSIX shell 使用 `export ARCHIFY_HOME=/path/to/archify`。测试会真实调用 archify；缺失依赖时失败而非跳过全链路。

| 阅读入口 | 内容 |
|---|---|
| [接口规范](docs/interface-spec.md) | 交互、四层地图、真相链、修改与同步协议 |
| [工具契约](docs/toolchain.md) | schema、冲突策略、离线封装与校验边界 |
| [合成 manifest](examples/synthetic.manifest.json) | 四层、共享 Capability、依赖与数据流 |
| [验收记录](docs/verification.md) | 可复现命令与验证范围 |

交互基于 [i-have-adhd](https://github.com/ayghri/i-have-adhd)，工程基于
[ponytail](https://github.com/DietrichGebert/ponytail)，可视化基于
[archify](https://github.com/tt-a1i/archify)。不新增竞争性的编码规范。

下一步（1 分钟）：打开生成的地图，选一个 Feature，用一句话描述希望改变的用户结果。
