# 四种公共闭环控制器与可验证经验接口

本轮完成四种实际软件生命周期、独立复核和一条固定 MuJoCo 原生开发集成。源码、旧红例、完整分母、公开观测、真实提交及 RAW 保留。本轮新增学习权重、GPU训练、真实机器人和化学终点均为0；既有合成学习实验仍保留其原范围。完整科研论文验收继续 **MAJOR_OPEN**。

## 方法与统一接口

控制器输入仅为已到达的公开历史、语言时间合同、ACK与不可抢占预约。原 B 事件身份不可替换。四种策略执行强批处理、反馈许可的 HSM retry、只重规划未提交动作的 EDF、单前缀提交的区间 MPC。公共 ledger 区分意图、提交、接受和 ACK；独立传感器进一步区分物理效果 onset 与后续确认。无效/重复传输不可重置预算，已经提交的命令不能撤销。

共同约束为A≤2、C≤2、总请求≤4；候选≤1000/decision、≤10000/epoch；每个策略决策在公开时刻后付费20ms才能提交新计划，旧计划在此期间仍可执行。资源或已提交请求变化会使尚未提交的计算结果过期；保留真实请求和已支付计算，再进行合法重规划。该20ms是虚拟计费，物理仿真继续；host计算本身不推进物理时钟，不是实时LLM保障。

事件差区间为[l_j−u_i,u_j−l_i]。整段包含在合同窗口内才认证TRUE，完全不交才为FALSE，部分跨界或缺失为UNKNOWN。公开已知模型细化与采样判据不能替代独立RAW裁判，也不提供未知动力学真实支持或连续保持证明。第一段短暂低速未确认时保留失败候选，之后检查首个真正确认的停止；原B仍不可重选。

## 完整 CPU 结果

| 方法 | 固定软件条件的时间认证 | 决策次数 | 候选计费 | A提交次数 |
|---|---:|---:|---:|---:|
| strong_batch | 16/16 | 1–1 | 282–370 | 2–2 |
| guarded_hsm_retry | 16/16 | 1–4 | 286–901 | 1–2 |
| event_resource_edf | 16/16 | 3–4 | 284–1197 | 2–2 |
| joint_interval_mpc | 16/16 | 8–15 | 1548–3131 | 2–2 |

主软件分母64＝8个已见配置×4实际控制器×2标量软件故障分支；每方法16。31行为检查、12压力trace、8旧公开packet回放分别列出。第三独立复核重跑同一门槛并完成11个额外回归，root/independent的所有非host-time事实一致；两次复核不成为128条新实验。无故障分支的时间成功不自动满足原裁判另外的“实际drop与恢复”诊断。

强batch解决全部软件配置，HSM在允许反馈的部分配置减少未提交冗余；EDF和MPC执行不同重规划生命周期，但本矩阵不证明agentic优势。八配置均已见，不能称heldout或OOD。

独立修复验收关闭一token绑定多server identity、actor入口非法对象回调、计算到提交间资源变化、B仅速度而未查控制力矩、短暂停止与缺样确认等问题。旧v1红例保留。公共Packet旧构造器仍以trusted primitive adapter为前提；本组件不是hostile Python sandbox。

[完整CPU源码/所有结果包](public_stateful_cpu_component_v2.tar.gz) · [解包核对](CPU_COMPONENT_BUNDLE_VALIDATION.json) · [独立审查](independent_review/PUBLIC_REVIEW.json) · [实际64点工作量图](figures/stateful_workload_v2.svg) · [逐行CSV](figures/SOFTWARE_WORKLOAD.csv)

## 单例原生集成

固定A→C、B预约450ms、C deadline2.8s、HSM和first-A-drop。新原生开发1条，1200实际mj_step与1201RAW；原plant、XML和裁判均字节不变。独立RAW裁判joint=TRUE。原B、停止onset、200ms确认、B维护、资源、故障与有效恢复分别查验；生产者退出码与内部DONE不作独立成功。

241 captures、239 delivered packets和1201 actor PublicFrames分别计数。每次20ms决策对应2个继续推进的native ticks；没有状态重写或reset。此例A/C实际queue wait均为0，外部B与C的450ms服务期间物理继续推进；不能借用旧开发例的69tick排队。1300ms公开powered-after-service反馈后，1320ms提交第二A；该时刻与初始fallback相同，支持反馈生命周期而非反馈必要性。独立命令重积分属于诊断，单独记epoch与samples，不增加主开发分母。该固定实例不提供方法总体成功率、未知任务泛化或物理化学结论。

[原生完整包](native_integration/complete_native_development_bundle.tar.gz) · [前瞻源与协议](native_integration/SOURCE_RELEASE.json) · [执行前独立审查](independent_review/native_bridge_review/SOURCE_REVIEW.json) · [独立RAW验收](independent_review/native_raw/NATIVE_RAW_AUDIT.json)

## 经验表和训练准入

VerifiedReplay保留原4cal/16test和8条DEVELOPMENT_SEEN记录，共28metadata，并非28个新机器人测试。测试primary T/F/U=8/2/6，strict0/16；完整timed+hold成功示范0/20。852图像→下一提交候选中832因策略图像交付时间没有日志而UNKNOWN，20尾帧无未来动作而REJECTED。不能用已应用动作或事后效果冒充图像之后的提交标签。

34CPU检查、28episode/852candidate schema与跨字段检查通过。学生张量未materialize，DP/offline-RL/OPD入训行0。公开的是元数据/代码，不是完整原生机器人RGB训练集。规则轨迹不是神经教师；没有学生rollout的expert轨迹合并不是OPD。后续可以明确LEGACY_SEEN_TRAIN，但保留原role且不再称untouchedheldout。

[元数据接口完整小包](verified_replay_metadata_component.tar.gz) · [19成员重开](VERIFIED_REPLAY_BUNDLE_VALIDATION.json) · [准入摘要](learning_data_design/PUBLIC_SUMMARY.json) · [DP/RL/OPD各自门槛](learning_data_design/LEARNING_OBJECTIVES_AND_GATES_cn.md)

解压元数据小包并把[公开重放入口](check_public_metadata.py)放在同级后，可运行`python3 -B check_public_metadata.py`核对18绑定成员、28记录/852候选schema和因果准入。此入口不读取私有RAW或图片，不重新生成物理标签，也不重新执行私有dispatch→metadata变换；公开元数据逻辑重放和原物理证据复算分开。

## 后续场景与论文门槛

[完整实验设计](research_design/NEXT_EXPERIMENT_DESIGN_cn.md)接续原C5颜色/流量、标量thermal-runtime及既有C22学习证据，设计六类目标：接触支撑交接、负载停转、定量加液、样品热暴露、共享资源并行和多episode适应。新的剂量/双温度模型尚未验收，真实设备/化学终点接口未取得。

先检查旧严格保持与复合稳定释放合同的共同可满足性。若用新“独立支撑前保持”语义，必须另发新合同和前瞻采集，旧0/16不能回写。完整合格且有观察交付因果的数据存在后，才进行DP/失败数据RL/学生状态OPD；同预算保留公开计时器、HSM、辨识+MPC、DAgger，以及首次/第2/3/5/10次与清空上下文对照。

下一32条为四控制器×八已见配置的配对机制验证；必须另冻结源码/协议、通过单例独立RAW与新源审查后才能执行。本增量没有运行那32条。顶会方法结论仍须证明有效经验吸收和任务空间留出收益；时间组件、软件检查或工作量图都不能替代这些验收。
