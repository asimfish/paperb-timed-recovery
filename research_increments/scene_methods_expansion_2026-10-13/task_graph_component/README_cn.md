# 原生 MuJoCo 任务图与原参照保护组件

本轮已实际执行 4 个机械合同实例 ×3 个控制的 12 条主轨迹，另有 2 条独立哨兵轨迹。每条受控轨迹在同一 native epoch 连续积分 10 s、1001 个 10 ms 原始采样点；14,014 个受控样本全部保留。单独的 full-power 原参照诊断积分含 1001 样本，预检的 100 步原生方程 probe 不是任务 episode。命令重积分和导出均不新增实验轨迹。

场景复用已验证的 contact-free 双转子 MuJoCo 资产和串行 selective 通道／独立 global relay。它不是原 A/B/C 场景、化学反应、C6 搅拌或新学习实验。GPU 未使用，原 A-r7 24 GiB 准入阈值未改变。物理时钟在声明的通信与服务时延期间推进，host 规划计算期间暂停，因此不能支持真实世界推理时延结论。

四个合同分别为并行停止、A 物理停止先于 B、B 先于 A、A 停止时 B 继续通电与运动到稍后的有效停止窗口。新依赖要求两个独立停止事件的最小间隔为 300 ms；额外 B 维护合同同时查看实际驱动和测得转速。仅改变时间窗口不能称任务空间变化，本轮的反向依赖与持续过程约束确实改变联合目标，但没有训练后任务泛化结论。

固定动力学为 A/B 惯量 0.002、阻尼 0.006；actor 只得到旧公开校准模型集、任务图、服务合同和延迟 300 ms 的公开 position/velocity/powered packets。没有 hidden fault 或 private inertia 输入。三控制包括保留旧 A→B 优先形式的 independent-window 强基线、graph-aware event 强调度，以及新增原参照 guard 的相同图规划。旧形式忽略新增 graph edges/维护条件是明确消融；它不是旧多 episode retained-history controller 的完整复现。

| 控制 | 主 joint TRUE / FALSE / UNKNOWN | 原锚点违例 episode / event | 图依赖合格 | 必需 B 维护合格 |
|---|---:|---:|---:|---:|
| legacy_order_scheduler | 0 / 4 / 0 | 4 / 4 | 3 / 4（含无依赖实例） | 0 / 1 |
| graph_event_scheduler | 1 / 3 / 0 | 3 / 4 | 4 / 4（含无依赖实例） | 1 / 1 |
| reference_guarded_graph_scheduler | 4 / 0 / 0 | 0 / 0 | 4 / 4（含无依赖实例） | 1 / 1 |

所有主轨迹的 A/B 单独时间窗口都合格；原参照与联合目标揭示额外失败。无 guard 的早停改变实际 shaft-angle 2 rad 起点：从原 0.44–0.45 s 延后至 0.47–0.48 s，不能重新定义这个起点来记成功。global relay 的并行实例同时改动 A/B 两个原参照。反向依赖下旧 A→B 形式违反图合同；B 维护实例的旧形式在 1.4 s 停掉 B 电源，虽其惯性停止时刻落入窗口，仍违反通电/运动持续合同。guard 在已验证校准假设下保存原起点并满足四个组件合同。

停止事件要求此前有 moving sample；abs(velocity)≤0.1 后至少持续 200 ms 的采样端点跨度，即 10 ms 下至少 21 个阳性样本。发生区间取最后 moving 与首个 low 样本的 bracket，确认时间另记。逐点维护不能保证点与点之间持续满足。full-power 原参照由相同初始状态、MJCF 和已加载物理参数独立积分；这是明确的 benchmark counterfactual，actor 不读取审计 oracle。

可达性哨兵真实执行 reference-guarded 并行计划，原合同通过；循环哨兵要求 A→B 与 B→A 均至少相隔 300 ms，联合矛盾为 0≥600 ms，图控制拒绝派发，但仍保存完整 10 s no-op 物理轨迹并计为失败。两个哨兵单列分母，不混入主 12 条，成功哨兵与主实例是固定场景重复检查，不新增统计独立任务实例。

13 个源码/输入在执行前冻结于 EXECUTION_RELEASE.json。SELF_AUDIT.json 从 persisted commands 重新积分每条原轨迹和原参照，并从原始 state 独立计算事件/合同；14 条全部 state error=0，命令 FIFO、应用时间、公开反馈边界及完整网格通过。第三审计的结论以单独回执为准，不能把自身复算等同外部验收。

MAIN_SUMMARY.json 提供各项 TRUE/FALSE/UNKNOWN、主 4 实例/12 轨迹、2 哨兵、1 原参照积分、14 native epochs、26 确认停止和 2 缺失停止计数。代表 case-04 的三组完整原始 CSV 位于 representative_raw；绘图应标注 raw-derived mechanical rotor speed，不能伪装为 RGB 视频。

native_task_graph_bundle.tar.gz 包含所有 14 条受控轨迹、失败、2 哨兵、完整原参照 CSV、冻结 code 和 source_snapshot，不包含 pyc/第三方库/凭据。ARCHIVE_VALIDATION.json 重开归档逐成员核对 SHA256，导出不增加 episode。源目录是 /data/liyufeng/paperb_task_graph_expansion_20261013_v1；冻结 source 不再编辑，公共网页由 root 独立发布。

该结果是固定、已知、无噪声机械 fixture 的机制诊断，没有 statistical generalization、学习、真实机器人、化学收益或普遍安全保证。所有失败均保留，没有追加 case 搜索更好的结果。
