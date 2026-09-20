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

下一步（1 分钟）：离线打开 `artifacts/synthetic-map.html`，点击「草稿管理」查看共享能力。
