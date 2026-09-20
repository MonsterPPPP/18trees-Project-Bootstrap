# 工具链契约

运行 `python bootstrap.py --help` 查看初始化、校验和地图生成入口。
运行依赖只有 Python、`jsonschema` 和生成时调用的外部 Node.js / archify；浏览已有 HTML 不需要这些环境。

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

`init` 仅从 Bootstrap 源仓库执行。目标项目自带的 `.bootstrap/bootstrap.py` 用于 `map` 和 `validate`。
初始化先构建候选文件并预检所有目标路径，再调用 archify，最后用独占创建写入。
相同字节跳过，不同字节、目录占用、父路径不是目录、symlink / junction 均报错；
不提供 `--force`，不覆盖已有文件。若写入失败，只清理本次新建文件，可能保留空目录。
这不是多进程事务系统；请勿同时对同一目标目录初始化。

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

下一步（1 分钟）：运行 `python bootstrap.py validate examples/synthetic.manifest.json`。
