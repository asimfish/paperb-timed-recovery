这份两页 ICML 组件稿围绕同信息、同预算的原事件定时控制与经验准入。`source/paired32_component.tex.in` 是结果绑定前的源结构，正式 PDF 在实际 paired32 RAW 独立验收和 root 报告完成后生成。

已原样复制官方 ICML 2026 style（SHA `7cdcf90f6a59c5219e7f15c88f7ed09fcaf598dad91e6cdddc4dc3cb0e397a95`），并复制 7 个 base evidence receipts。软件 64、单例 primary1/diagnostic1、未来 paired32 primary32/diagnostic32、旧 metadata28/852/34 gate/入训0 分开呈现。

结果将由 root 的 `results/PUBLIC_SUMMARY.json`、`results/ALL32_RESULTS.csv` 和矢量 `figures/native_paired32_summary.pdf` 在独立审计绑定后生成；分母固定每方法 8，保留失败、拒绝和 UNKNOWN。最终稿保留 strong-batch 平局、已见配置、D 同时改变 Aupper/Cwindow、ACK 不代表 stop，以及 20 ms 虚拟计费不等于 LLM 墙钟的边界。

构建合同在 `BUILD_INPUT_CONTRACT.json`。完成后进行两遍 LaTeX、2 页检查、逐页视觉审查、源码归档重开逐成员 hash 验证，再交 root 独立复核。没有执行新的物理、GPU 或训练任务，也没有修改旧封存目录、新 67 source、native cases 或 auditor 文件。
