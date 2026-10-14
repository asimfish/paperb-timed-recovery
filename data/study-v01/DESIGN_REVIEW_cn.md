# Paper B 系统研究设计独立审阅 v1

审阅时间：2026-10-14。审阅者 `/root/study_matrix_review`；任务是只读审阅已有 Paper B 并提出可执行的研究层级。本增量新增 native、GPU、重积分、训练、网页发布均为 0。本文不是一次新的实验验收；旧封存与负结果不改。主研究总矩阵由 root 维护，本目录的 CSV 是独立建议及依赖检查。

## 1. 当前能支持的故事与真正待检验的问题

当前最清楚的研究问题是：**在原始物理时间合同与失败身份不变、同一合法信息和数据预算下，残余事件账本能否使一个共享策略比同信息 TimeDP + 学生状态监督更好地吸收失败校正与已执行恢复经验？**

主张的新增机制是使用历史事实的归纳偏置，最近强对照是 B3，不是无时间 DP。S/F/R 类型、因果前缀与独立物理终点建立监督的适用边界；它们本身不能证明策略变强。若 B3 能解释全部收益，不能把完整流水线、额外教师或规则包装重新命名为新学习算法。

已完成证据彼此分开：paired32 中四种确定性控制各 8/8 已见机械配置通过主谓词，未证明 agentic 必要性；clock54 为实际 CPU 负载的原生/墙钟分离；ARIS symbolic matrix 的 69,120 行不是独立任务，显式规则记忆 100% 强于所测学习历史；ARIS 单例基础读回通过但 strict hold FALSE、load UNKNOWN。M0/M1 共两次尝试，完整采集一次、force gate 通过零次、成功训练准入零次。M1 原值被丢弃，负标量原因不可恢复。lossless 0.4 的 81 CPU 检查支持证据保留接口，尚无 native 验证。

最新 10 页 ICML 格式稿与网页是研究材料交付，**不是完整科学验收**。本轮新的 VLA 方法权重与受测 heldout 学习优势为 0；项目较早的合成模型权重不能被抹掉或改称本方法成果。

## 2. 五层门禁与一条可并行工程分支

| 层级 | 要回答的问题 | 通过后允许的结论 | 当前范围 |
|---|---|---|---|
| G0 测量与可行性 | 原值、符号、单位、受力覆盖、原生时钟及所需物理终点是否可独立复算？合同本身是否有可行 witness？ | 某个冻结物理/时间谓词可测；不是策略优越 | M1 base trace 可用，force UNKNOWN；新采集协议待审 |
| G1 因果数据与执行 | 真实学生看到什么、发出什么、何时 APPLIED、教师何时接管？每个 target 属于哪个 actor/attempt/type？ | 可用于具体用途的合格训练池 | v04 CPU 接口存在，混合 actor 接管与实际学生数据仍缺 |
| G2 匹配学习 | 相同数据、祖先权重、前缀信息、计算与执行 harness 下，M 是否优于 B3？ | 条件性的参数学习/机制证据 | 21 learned 等效 runs、324 eval 均未执行 |
| G3 未见任务与适应 | 新 goal/dependency/retry 组合中，ctx 与 θ 各自贡献多少？改善能否离线教师后保持？ | 预声明任务分布内的泛化或适应结论 | 两图仅 pilot；confirmatory 新任务池与预算待定 |
| G4 真实装置与化学 | 连续物理操作、设备日志、独立物理及化学终点是否一致？ | 对明确装置/反应与合同的结论 | 实际 hardware/chemistry 测量尚无 |

另允许 **OFFLINE_BEHAVIOR_RECONSTRUCTION** 与 G0 受力诊断并行：只用基础 RAW 已通过的 ARIS 或 M1 单例，重建 image→APPLIED action chunk 的数据/训练通路。无需把全部模型源码或梯度检查等到 force qualification；但该数据没有 force/full-task-success 标签，**不属于科学合同的 S512/S1024 合格池**。若确实训练产生权重，登记为工程重构权重，不称新算法优势、成功经验吸收或 heldout 任务泛化。

这个工程分支最小有价值的验收是：

- 用原始 request id、APPLIED 顺序、epoch 和 native timestamp 重算 capture 与未来动作 chunk 的对应；FIFO 尾部不能填造 action，缺少 slot 必须 mask。APPLIED 只证明控制已应用，不证明物理成功。
- 离线 RGB catalogue 不改称当时学生 delivery；采用显式 OFFLINE_CAPTURE 语义。传感器图像与控制异步间隔保留，不把同一帧重复当新观测。
- 时间/动作归一化只从指定 fit 块估计，拒绝未来 audit、force 结果或未来控制进入输入；固定 timer-input mask 的 B0/B1工程探针只检查接口。
- 从新初始化参数开始，确认有限 loss、非零梯度、实际 optimizer step 与参数 digest 改变；同一小 fit 子集上的 memorization 是通路检查。仅 loss 降低仍不能证 action 执行有效。
- 单例前后 blocked segment 的 reconstruction 可以描述误差与分布变化，不随机切帧宣称 heldout episode。horizon/history 跨分块边界的样本应 purge；这仍不是任务泛化。
- CPU/microGPU 预算单独冻结，声明 source、seed、step/样本数、实际 wall 和产生的 weights；不得悄悄扣/加到 42 GPUh 科学学习合同。

## 3. 两个必须在训练前关闭的公平性漏洞

### D01：相同信息必须是相同有效有限前缀

M/B3 得到同一类传感器并不自动等于同信息。若 M 的 ledger 总结整段历史，而 B3 只见最后几帧/有限 token，M 已获得额外可用记忆。**硬门禁应是逐 decision 的 `same_public_prefix_digest`、同样的有效 history 长度和裁剪边界、同 packets/masks/capture-delivery 时间以及同 G**。ledger 只能由 B3 也实际收到的有限前缀导出，不可用额外后台累积状态、私有 verifier 或后到 audit。

ledger 不可从裁剪掉的旧 anchor 继续携带值，除非该 anchor 作为公共持久 event packet 明确同时交付给 B3。两臂需要相同 reserved ledger 输入维度、长度/attention mask 与 backbone；B3 只把这些 derived slots 置零。零特征与 UNKNOWN 使用不同 mask，不能让 B3 输入的 UNKNOWN 变成实数 0。prefix 随机或打乱反例仅作诊断，不替换强 B3。

root 已通过协作消息采纳本项为新组织合同硬门禁；实际训练/输入逐 pair 检查尚未执行，不称已通过。

### D02：8 次 validation 与 21 runs 的 checkpoint 选择冲突

旧 root v02 合同同时写 validation≤8 总尝试、7 arms×3 seeds=21 learned-run equivalents，并按 validation 结果选择 checkpoint。至少每 run 做一次 validation 已需 21 次；若重复 checkpoints，冲突更大。不能把 8 当成每 run 预算却仍宣称总 430 尝试。

建议冻结各 run 的最终 10,000 adaptation update checkpoint；共同祖先 5,000 updates，总量 15,000。8 validation attempts 仅用于采集/任务资格，**不按各 run 验证试跑择优**。wall/GPU cap 下未完成统一步数记 INCOMPLETE，不以早 checkpoint 替代正式比较。若未来确要选择 checkpoint，另立 source/version 与足够的诚实 validation 总预算。

root 消息已明确采纳为新 STUDY_PLAN v1 决策 D02，且要求保留旧 v02 字段不改。本文记录的是“冲突、建议与本轮采纳”，不是宣称旧合同早已实施此修订，也不直接写 root 所有的主矩阵。

## 4. 数据与预算：算术正确仍需 manifest

共同祖先 U0 必须是固定 train-only S512。M/B3 最终用 S512/F256/R256，S-only 用 S1024，AF/AR 用 S768 加对应 256。每臂祖先与后续适应的 unique union≤1024 **state/target pairs，不是 episodes**。源共享池 S1024/F256/R256 共 1536 pairs，与 ≤1536 teacher queries 的数值相同也不代表一个 query 对一个独立 pair；多步 chunk 可产生多个 pair，计数规则须固定。

需补的 manifest 字段：pair id、causal input digest、target digest、target execution-time slots/mask、teacher query id/payload、真实 actor、student visitation proof、原 attempt/root ancestry、graph/split、S/F/R用途、来源和 admission receipt。当前 dedup key 含 original_attempt_id，因此来自不同 attempt 的数值相同 input/target 可被计为不同记录；可以合法按采集记录去重，但不能误称独立语义样本。应同时报告 record-level 去重与内容重复率，horizon 重叠不贡献独立统计单位。相同 F/R pair 不能跨类型/臂重复算两份配额。

F 是实际固定 collector 学生访问状态的新教师 target；不是把 failed action 贴成成功。R 的 teacher takeover 是特权 BC，不能当学生 visit 或已执行 OPD。原失败与后续局部恢复分开计分；若完整任务 UNKNOWN，R 至多按其已经独立验证的局部用途使用。S 合格 shortage 在96训练 attempts /1536 queries /16每attempt cap内必须 DATA_NOT_READY，不能增加选择性成功采集。

collector 的 θ0 版本/seed 及 3 个训练 seed 的祖先关系需要明示：共享同一个 collector 不等于三组各有独立数据；相同池是控制变量。若三组祖先分别训练，应核实每组都只用同一个 U0，记录实际共享与等效计费。

324 evaluation arithmetic 可复核：5主臂×12 cells×3 seeds=180；3消融×12×3=108；θ0×12×3=36。M/B3 的核心 contrast 只占其中72次；其余不能当额外 M/B3 独立样本。加96 collection、8资格 validation、2 preflight=430。若新增工程或 G0 native，独立计入其协议分母，不塞进 430 或清空 M0/M1 原两次。

## 5. 时间、教师查询与安全拒绝的可辨识性

0/150/450ms queue 档只检验声明的原生应用延迟，不能代表实际 GPT/agent 推理 wall。需逐次记录 capture、delivery、decision、submit、APPLIED、effect、query start/end 两种时间，并确认等待期间实际 physics 继续推进。一次同步 teacher query 如果冻结 physics，可作为明确的离线标注；不支持真实时限下 online agent 成功。

训练中 query 返回时状态已变化时，label 仍绑定 query 发起的历史状态和合法 target 时刻；不能把过期动作当当前 correction。评估 teacher=0，禁止跨会话检索；当前 episode 的合法 finite prefix 保留。多 query 的总 wall、token/请求数、环境等待和 teacher takeover 成本报告为真实采集成本，同样 query cap 不保证同耗时。

全臂 veto 或 UNKNOWN 高不能解释为“零违规所以方法更安全”。主分母保留 all attempts；分别给 complete TRUE/FALSE/UNKNOWN、measurement-invalid、crash、veto、local recovery 和可避免 unsafe violations。若多数 UNKNOWN 来自未合格测量，先回 G0；若强 oracle 在 train-only 可行性 witness 也失败，回任务设计。不得看到 H01/H02 结果后调阈值再称 untouched test。

本计划一半 cells 是不可逆 hard-catch negative control，因此 pooled complete TRUE 的理论上界为 50%，15pp pooled 提升相当于 recoverable strata 的30pp。所有 hard-negative original failure 都必须保持；其正确安全处置应另计，避免把必然 deadline miss 与可避免 unsafe actuation混成同一个“违规不增”。主 pooled 结果不删除 hard negatives，但报告两种 strata。

## 6. Split、pilot 与 confirmatory 统计

真正 heldout 单位是整张 goal/dependency/retry 图及其 parent attempt 家族。F/R窗口、同次episode的reset后代、source图像和teacher标签不得跨 split。任务 source、语义 graph digest、条件/目标/阈值/故障注入版本需执行前冻结。当前12 graph source仍为 null，所以“规划了 heldout”不等于“已经搭建并执行未见任务”。只改光照/seed 是 state-space perturbation，不是 task-space evidence。

公开写 H01/H02 结构用于预声明不破坏 heldout；用它们结果调可行窗口、harness 或数据配额则破坏。任务资格可在 train-only 相同基本操作的 witness 上建立；如果必须执行某个 heldout 图来修设备/协议，记录其被开发暴露并另立新的 untouched confirmatory 图池，不能事后换名。

现主 M/B3 每臂36个 attempt outcomes，但共享12世界cells、仅2图，3 seeds是训练随机性而不是36独立任务。图像、RAW行、15237步、69,120 repeated eval行都不能当功效 N。按 world cell 聚类的 bootstrap仅对本 pilot 条件描述，不能为未知任务分布给可靠 graph-level 泛化CI。

15pp 是 go/no-go 而非显著性门槛。即使假定36独立pairs，净6修复/0损害与净7修复/1损害同为约16.7pp，但 exact paired-sign two-sided 值分别0.03125与0.0703125；实际共享graph/cell结构还限制这种检验。这里仅是算术示例，不是已测 p 值或推荐把当前 runs 当 iid。

confirmatory study 需在 pilot 后另冻结 primary M−B3 contrast、最小有意义差 δ、unknown/violation非劣边界、独立图/世界实例数量和总资源。用pilot的 discordance与graph异质性做功效设计，而不是再加相同帧或相同两图。仅作独立paired Bernoulli规划示例：δ=.15、discordance q=.30 时，normal近似 N≈(1.96+.84)^2(q−δ²)/δ²≈97 independent pairs；这忽略graph聚类与多因素，不是当前执行预算或97个图的要求。不得把本建议统计计算转为实验已验收。

## 7. 核心实验矩阵与结果转向边界

见 `CORE_EXPERIMENTS.csv`。13行包含 raw/force/clock 门禁、因果 actor、并行工程重构、共享池、核心学习、计时器、数据消融、原失败负对照、任务泛化、context/θ和硬件化学。每行有独立单位、门槛、预算与 source proof，不主张为了数量扩张更多无价值实验。多行可重用同一次正式评估，不能相加再次计数。

若 M 未胜 B3：保留效应与不确定性，撤回 ledger独立学习优势；数据聚合可能解释收益。若 B2 一样好：支持外部调度而非 agentic参数机制。若显式记忆一样好：支持context管理。若关闭教师/跨会话context后gain消失：不支持参数吸收。若全臂 UNKNOWN/veto：研究测量/可行性，而不是拿失败学习输出排名。

负结果可以形成“时间合同与恢复数据何时产生错误学习证据”的实证故事，但需真实、合格、跨实例的规则/策略对照和可复算 effect；仅CPU接口测试、单例原值丢失与格式完整论文不足以认定顶会方法论文已完成。不得在不显著后不断加RL/OPD直到有赢家，再回填原主张。真正后续RL或distributional OPD必须另立目标、分布、估计器、预算和独立确认。

本审阅的交付证明为输入摘要和文件hash闭合，不是科学成果认证。原封存均只读，M0/M1、强batch平局、UNKNOWN和所有失败分母不变。
