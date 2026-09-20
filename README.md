# Project Bootstrap

在目标项目的 Coding Agent 对话框发送：

> 请根据这个仓库，在当前项目初始化 Project Bootstrap：〈本仓库 GitHub 链接〉。仅本地生效，不把 Bootstrap 文件带进 Git；保留项目已有规则，完成后告诉我怎么使用。

然后继续对 Agent 说：

> 告诉我这个项目能做什么，并打开项目地图。

> 修改登录失败提示，让用户知道如何重试。

**[人类使用手册](MANUAL.md)** · **[Agent 安装说明](INSTALL.md)**

人只描述目标；Agent 负责安装、理解项目、修改、测试、独立 Review 和按队列合并。
默认 Local-only + Local-first：Bootstrap 留在本机，生产发布需要明确授权。
地图从 Product / Feature Workflow 开始，技术路径留给 Agent 定位。

**给接到安装请求的 Agent**：先读 [INSTALL.md](INSTALL.md)，在用户指定的目标项目执行。
本仓库是规范与工具链来源，不要把整个仓库克隆到目标项目内，不要修改其业务依赖或已有规则。

工程使用 [Ponytail](https://github.com/DietrichGebert/ponytail) 与
[Stop That Shit](https://github.com/lennney/stop-that-shit)，交互使用
[i-have-adhd](https://github.com/ayghri/i-have-adhd)，地图使用
[archify](https://github.com/tt-a1i/archify)。上游正文只链接引用。

工具维护说明见 [工具链契约](docs/toolchain.md)，验收证据见 [验证记录](docs/verification.md)。

下一步（1 分钟）：把本仓库链接和上面的安装请求发给目标项目 Agent。
