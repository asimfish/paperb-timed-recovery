# Paper B：时间约束与可验证恢复

研究网页由本 GitHub 仓库发布：**https://asimfish.github.io/paperb-timed-recovery/**。

这个仓库存放研究网页、机制图、选定实验报告和 ICML 增量稿。完整研究代码保留在原研究仓库；本仓库没有上传原生轨迹、服务器配置或凭据。

[当前方法与实现边界](CURRENT_METHOD_cn.md) · [完整方案](full-design.html) · [最新实验](research_increments/public_response_identification_2026-10-12/README_cn.md)

目前核心学习设计是“物理时间合同＋可验证恢复经验＋共享历史条件 Diffusion Policy＋学生状态回标／DAgger”。RL 和多专家蒸馏是条件扩展。最新机械控制实验仍可由确定性强基线解释，尚未证明新方案的 VLA 学习或真实化学收益。

## 维护与复现

GitHub Pages 从 `docs/paperb-site` 分支的根目录发布；更新该分支后自动构建。源工件和发布副本的 SHA-256 绑定在 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)。HTML 的证据链接已适配项目目录，选定报告中的本地服务器入口以通用描述替换；原实验工件未改写。

本地预览：

```bash
python3 -m http.server 8000
```

打开 `http://localhost:8000/`。运行静态工件与链接检查：

```bash
python3 check_site.py
```

使用 `python3 check_site.py --base-url https://asimfish.github.io/paperb-timed-recovery/` 核对线上网页和全部所选工件。网站发布验收与科学方法验收分别记录。
