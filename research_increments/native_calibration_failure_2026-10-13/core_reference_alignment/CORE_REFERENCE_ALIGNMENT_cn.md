# Paper B 核心参照对齐：MATTERIX 与 Auto-Engineering

本轮为只读来源核对与研究对齐，没有启动模型、GPU、仿真或机器人。只读使用作者指定的本地 PDF、实际微信 Markdown、Nature 官方主页面及既有项目对照记录；没有重新下载代码/资产或重跑旧复现。完整论文创新性仍待实验验证。

## 已有工作与此次补充

2026-10-11 的 robot_rsi_matterix_review 已建立 MATTERIX 原/现版本、源码/资产和 R0–R6 复现矩阵；auto_engineering_source_review 已核对作者给定微信实际正文并形成四 harness 与两类账本设计；chemical_auto_engineering_design 已展开十组实验与共享 DP/学生状态回标路线。不能把这次阅读写成这些比较第一次完成，也不能把当时的运行缺口更新成今天所有环境都不可用。

此次核对附件 SHA256 与旧 intake 相同，重点补齐章节级证据和最终稿引用，以及最新机械组件能够支持的范围。旧材料均保持原样。论文版代码/资产已取得的状态是既有准备证据，不等于 MATTERIX 完整热/反应工作流复现。SafeLab/A-r7 原生操纵和本轮双转子不是 MATTERIX 官方完整工作流的替代证明。

## MATTERIX：已经有的系统机制

正式引用为 Darvish et al., **MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation**, Nature Computational Science **6**, 67–82 (**2026**), DOI **10.1038/s43588-025-00924-4**。在线发布日期是 2025-12-31；文章卷期年份为 2026，不能只因 DOI 中含 025 就把正式引用写成 2025。作者附件共 19 页，其中主文 printed pp.67–82，余页为 reporting summary。Nature 官方页面核对标题、作者、卷页、在线日期及 DOI；正文细节来自作者提供 PDF，而不是订阅页的 abstract。[Nature 官方记录](https://www.nature.com/articles/s43588-025-00924-4)

1. **多尺度环境与可组合接口。** Fig.1/printed p.69、环境部分 pp.70/77–78 包含 USD 资产、机器人、液体/颗粒、感知与设备语义，以及多机器人/液体处理平台。p.78 明说异构 agents 可并发执行，为调度和实验规划提供环境。因此“搭化学 twin”“多 robot 并行”“复用技能组合任务”均已有先例。
2. **物理与语义进程。** printed p.72、Methods p.78 将物理、连续语义和逻辑状态组合，用事件、过程、前置条件及机器人/设备动作推进。加热、传热、液体处理、近似反应已在框架范围；p.72 还明确包含 waiting primitive 和学习策略的部署入口。不能说原框架不建模时间或设备过程。
3. **热过程与化学终点的区别。** printed p.75 的示例中 heater 在 1010.6 s 关闭，反应继续至 1639.9 s。这已经明确展示关电与样品反应结束的区别；该区别不能成为本项目首创原理。Methods p.78 用能量平衡与近似温度依赖动力学，p.79 明确这些反应估计是半定量；不能把模拟浓度或动作完成 flag 当实验产物质量真值。
4. **系统与工作流验证。** printed p.79 的 System and workflow verification 检查化合物、浓度及反应前提，作为调试和训练反馈。它已经是 verification 机制。我们拟增加独立、校准、可重放的物理事件区间与时间合同审计；这是一项测量/实验协议要求，不证明原机制不可能表达期限。
5. **层级 workflow 与学习。** pp.72/79–80 把 motion planning、IK、grasp、等待及 RL/IL 作为叶技能，HSM tree 提供多层组合。p.79 描述 PPO 和 curriculum，p.80 描述感知、真实设备同步与力反馈安全停止。因此“控制＋学习技能＋执行反馈”的系统组合已有基础。
6. **迁移、局限与未来。** pp.75–76 有真机 pick/place、pouring、FR3+OT-2；p.76 讨论 HSM 恢复/contingency limitations，并建议更灵活结构；p.77 讨论在线 surrogate 校准、LLM 生成 HSM/data pipeline 和实验规划，属于未来方向，不可当作已完成 RSI/共享策略吸收实验。

可合理复用的是资产/场景描述、设备语义接口、HSM/primitive 调用、公共感知/机器人状态转换和执行日志。必须另行校准控制/测量时间，并建立 actor 输入 allowlist、物理有效终点、独立 score、版本与失败准入；论文中有接口设计不意味着本地拿到的归档已包含全部实现。旧复现矩阵已记录版本与语义实现缺口，本轮不再查下载。

## Auto-Engineering：已经有的工程闭环

指定 Markdown 是罗博脉动 RoboVibe 2026-09-10 的微信报道/中文转写；文中指向 General Robotics 2026-09-09 的公司博客 Introducing Auto Engineering for Robotics。旧 v2 已获取该官方博客；本轮按授权只重读指定 Markdown，未访问公司服务或博客，不声称新一次主站核验。它是公司技术说明与演示，不能作为经过同行评审的 matched benchmark 结果。[作者指定微信来源](https://mp.weixin.qq.com/s/FUCHQWYSuGxegN2mXVCLJA)

四 harness 与迁移/复用是来源已有结构：§3 接入机器人、接口、坐标/标定与预检；§4 将世界/求解器作为可改的工程变量，并耦合 MuJoCo 与 Warp/DFSPH；§5.1 优先组合现有感知、抓取和规划，§5.2 对移动烧杯使用合成 BC＋DAgger，§5.3 对搅拌采 GELLO 示范并微调视觉策略，§5.4 由人类视频重建仿真并训练；§6 部署诊断感知、标定和实际控制频率；§7 保留并复用代码、模型、技能、标定以及失败/修复知识。故自动选构建路径、失败驱动再采集、工程工件复利、学生分布回标都不能因换成我们的名称就宣称新机制。

文中四小时、后续 10–15 分钟、143 mm→5.7 mm 或约 500 Hz→29.7 Hz 都是报道的案例指标，不是本地实验、相同任务对照或 actor 吸收效果。工程墙钟、控制频率与物理事件期限应分别计量。报道里的 reactive pouring 使用状态表示和末端动作；不能用其状态输入上界直接对比 RGB/语言 VLA。文中没有确定某个 GPT 型号是必需组件。

可复用的接口思想是 robot ingestion/health check、world evidence、skill creation 的多路线选择、deployment diagnostics，以及带适用条件和版本的工程工件账本 K。这与轨迹经验 D、上下文 M、actor 参数 θ 必须分开：修复 control cadence、替换 tracker 或 twin 参数可提升任务结果，但不能据此认定 θ 学习或冻结全部参数的 ICL。

## 本项目的对应范围

| 项目主张 | 核心参照已覆盖 | 我们需要证明的候选增量 | 最新证据边界 |
|---|---|---|---|
| 化学 twin/流程 | MATTERIX 已有多尺度、近似动力学、HSM/技能和 sim-to-real | 原 C5/C6/C13 紧期限、独立真实终点、过程漂移和观测权限 | 本轮双转子不能证明；完整化学仍开放 |
| 独立合同验证 | MATTERIX 已有 task/workflow verification 与安全反馈；Auto-Engineering 有预检/验证 | 分离派发/有效事件/确认/到达，用校准区间审计原合同及未知 | 机械与调度组件已验证接口；化学/真实时钟未覆盖 |
| 原参照恢复 | MATTERIX 讨论恢复局限，Auto-Engineering 保留部署故障修复 | 已发生外部事件不能重置；恢复仍满足原 deadline 与其他过程 | 当前 twin-rotor 是 full-power counterfactual reference preservation，不是已发生化学事件 ledger recovery |
| agentic 自改进 | Auto-Engineering 的四 harness、构建路线选择、工件复用已存在 | 经验选择/准入的具体机制和在完整成本下的收益 | 当前规则组件没有 agent 构建或学习收益 |
| 一个共享策略吸收经验 | MATTERIX 的 reusable learned skills 与 Auto-Engineering 的 BC/DAgger/visuomotor adaptation 已存在 | 同强 teacher/同预算，学生状态回标和共享历史策略在独立留出联合合同上有收益 | 共享 DP、RL/OPD 权重尚无本轮完成证据 |
| 并发/任务空间 | MATTERIX 已有异构 agents、任意层级 workflow 和调度环境 | 图变更与资源约束下的 measured event correctness；训练后新组合泛化 | 4图×3规则=12主机械轨迹，只支持合同/强规则机制检查 |

最新独立审计的 12 条主轨迹中三规则 joint 为 0/4、1/4、4/4；2 哨兵和 1 原参照诊断积分分列。所有单独 A/B 时间项通过，但图依赖、B 采样维护和 counterfactual reference 造成联合失败。这说明为什么需要完整合同和强基线，不是“新VLA胜过核心参照”。7,172 个格点条件是合成数学校验，也不能增加 physical episode 数。A-r7 随机/插值计时矩阵状态由 root 的实际收据更新，本对齐不触发或重复运行。

## 最小公平对照与实验

首先保留一个 **MATTERIX-inspired HSM＋IK/MP＋waiting＋workflow verification** 适配基线，并明确不是尚未运行的官方版本复现；另用同信息独立校准的事件/资源/MPC 强调度。它们拥有与方法相同的传感、控制、合法时钟、校准和反馈，private semantic state 只能另列 oracle。C13 原 M1 与公开时钟部署是不同轨道。

再比较冻结 actor 的工程 agent/harness 与更新 actor 的学习：先统一外部栈 K/感知/twin，再在同 DP 骨干、数据/优化/compute 下做成功示范与准入恢复、合法时间与 history、offline expert imitation 与学生状态 DAgger。若只是监督聚合，用 DAgger 名称；OPD 需要明确的教师分布/目标与学生访问状态覆盖，不能仅串联多个训练阶段。

建议最小顺序是：E1 同场景同合同 HSM/强调度与候选方法，独立事件计分；E2 一个可安全标定的过程故障，检验原外部事件 ledger 的有效恢复与 safe abort，不将 reset 当恢复；E3 在共同冻结外部栈上做 θ 更新×M 保留的 2×2 归因，测试时不调用 expert；E4 同 teacher/同标签和新 native steps 的 offline imitation vs student-state aggregation；E5 工程冷启动/工件复用及其完整历史成本单列。每个实验先冻结完整实例、轨道、原始终点、预算和失败/未知规则，再采集。

实验不能只设置弱 open-loop timer；不能以 full simulator compounds/pose 给 teacher 或 HSM 而让学生只能看 RGB 后声称算法优势；不能把不同物体/任务的报道部署时长相减作为科研增益。保留所有拒绝、失败、超时、安全停止和校准/诊断成本，以完整独立实例/实例簇计分。模型等待必须真实推进物理过程；当前 CPU paused-clock fixture 不证明这一点。

可以提出的研究问题是：**在核心参照提供的 twin 与工程闭环之上，独立合同约束下仍有效的恢复经验，能否在同信息强调度与 matched DAgger 对照下，转化成一个共享策略的留出收益？** 这仍是假设；只有完整实现与对照后才能成为方法论文贡献。
