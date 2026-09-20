# Bootstrap 开发约定

先阅读 `docs/interface-spec.md`，再按语义修改规范或工具链。

本仓库只交付规范、模板、skill 与工具链；示例必须是合成数据，不实现业务。
工程遵循 [ponytail](https://github.com/DietrichGebert/ponytail)，交互遵循
[i-have-adhd](https://github.com/ayghri/i-have-adhd)，地图采用
[archify](https://github.com/tt-a1i/archify)。上游正文不入库。

长期规则写入本文件或规范文档。完成有效任务后判断是否存在语义或结构变化；
不按文件或 commit 自动同步地图。明确的 `只修改 NODE:X` 是硬边界。
小步语义化提交；运行 `python -m unittest discover -s tests -v` 验证工具链。

下一步（1 分钟）：打开 `docs/interface-spec.md` 确认修改对应的语义范围。
