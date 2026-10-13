已完成两页 ICML preprint 组件稿 `PAIRED32_COMPONENT_NOTE.pdf`，源文件是 `source/paired32_component.tex`。正式数据来自实际 32 条独立 RAW audit 及 root 的 canonical CSV/summary，0 placeholder。

四方法各 8/8 joint TRUE，strong batch 平局保留。实际决策/候选范围分别为 batch 1/282–370、HSM 1–4/286–901、EDF 3–4/284–1197、MPC 8–15/1548–3131。A2/C1 全部一致，A/C queue maxima 0/0/20/10 ms；虚拟计费是 20 ms/decision，不是 LLM 墙钟。

32 主实验的 38,432 RAW/38,400 steps 与 32 次诊断重积分的同样样本/步数分开；单例 primary1/diagnostic1、软件64检查、旧 metadata28/852/34检查/入训0 均另列。8 个配置已见，D 同时改变 Aupper/Cwindow，不做随机种子、IID、heldout、OOD 或 agentic 优势推断。稿件没有 VLA、真实化学或权重学习结果主张。

官方 style 字节与原件一致，SHA `7cdcf90f6a59c5219e7f15c88f7ed09fcaf598dad91e6cdddc4dc3cb0e397a95`。两遍最终 LaTeX 无 undefined citation、无 overfull box；两页均完成视觉检查。正文/页边距未压缩，表格 9 pt，紧凑矢量图 8.5–9 pt，全部 32 个 interval 与 decision 点保留。原 root 图 PDF/SVG/PNG 的实际字节同时留在 inputs 和源码包，root figure 目录未改。

源码归档用于重编译完成稿：在解包目录建立 `build/`，从 `source/` 执行两遍 `pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../build paired32_component.tex`。绘图代码 `build_print_figure.py` 从包内实际 ALL32 CSV 生成 print 图；完整数据绑定生成器 `build_component_note.py` 的工程级运行还需要原项目的封存 source/ROSTER 与 root audit/report 路径。归档以完成的 canonical TeX 重编译，不包含草案模板或 build 中间产物。

`BUILD_VALIDATION.json`、`SOURCE_BUNDLE_VALIDATION.json` 和 `FINAL_MANUSCRIPT_RECEIPT.json` 记录 PDF、数据、style、图和代码哈希，以及归档重开逐成员检验。root 将进一步独立视觉/事实复核。原 67 source、604 封存目录、native cases、auditor 与原报告均未修改；本稿未执行 native、GPU 或 fit。
