# 四控制器、八已见配置、32条原生配对机制验证

本增量实际运行32条MuJoCo原生轨迹，四方法各8条。独立RAW/时钟/公开输入/资源/命令/恢复全部验收通过，T/F/U=32/0/0。另32次独立实际命令重积分全部state/time误差0；它们是诊断，不使主分母变成64。单例开发也不加入32。

## 方法与场景

强batch、反馈HSM、事件/资源EDF、联合区间MPC共享相同公开历史、原B事件、名义模型、none/first-A-drop假设、最多A2/C2/总4请求、候选1000/decision及10000/epoch。已提交/接受动作不可取消或退款；只重规划未提交意图。公开已收到的功率反馈与物理停止/确认独立，ACK不算完成。每个20ms策略决策推迟提交，同时物理继续2ticks；host计算自身不推进物理，虚拟charge不是真实LLM墙钟。

八配置交叉A→C/C→A、B设备占用50/450ms和D2.8/3.1s。D同时改变A窗口上界和C目标：A∈[1.8s,D]，C∈D±150ms，最小依赖间隔40ms。原B真实首次角度2跨越不可重选；stop onset与200ms/21点确认分别计时，B维护6s是采样判据，不是连续或化学安全证明。

八配置已开发见过。32是固定配对机制验证，0随机seeds，不能作为IID总体成功率/CI、heldout或OOD。参数已知且无噪声，没有未知模型真实支持保证；公共模型可细化同一个原B事件，粗50ms不是不可约信息下界。

## 全部32结果与成本

| 控制器 | T / F / U（每8条） | 实际决策次数 | 候选计费 | 最大实际预约等待 |
|---|---:|---:|---:|---:|
| strong_batch | 8 / 0 / 0 | 1–1 | 282–370 | 0.0ms |
| guarded_hsm_retry | 8 / 0 / 0 | 1–4 | 286–901 | 0.0ms |
| event_resource_edf | 8 / 0 / 0 | 3–4 | 284–1197 | 20.0ms |
| joint_interval_mpc | 8 / 0 / 0 | 8–15 | 1548–3131 | 10.0ms |

**四方法平局，强batch已解决全部8格。**全部实际A2/C1。batch8决策/2528候选、HSM19/4350、EDF27/5382、MPC92/18392；本族额外反馈/重规划没有提高成功数或减少动作数量。C时间误差及选择偏好仍有差别，但不能由此声称agentic优势。EDF/MPC各4例真实非零等待，最大20/10ms；batch/HSM均0。不能借用旧开发例69tick队列。

主轨迹共38,400步骤、38,432RAW、7,712captures、7,648delivered packets、38,432actor frames；诊断另38,400步骤/38,432samples。实际有限模型下的0重积分误差不是异机、硬件或化学保证。没有新增GPU训练、VLA/RL/OPD权重、机器人硬件或独立化学终点。

[全部32行CSV](results/ALL32_RESULTS.csv) · [完整独立审计](independent_raw_audit/PAIRED_RAW_AUDIT.json) · [范围与成本](results/PUBLIC_SUMMARY.json) · [逐例队列与计费](independent_raw_audit/CASE_USAGE.csv) · [实际区间与决策图](figures/native_paired32_summary.svg)

## 执行前后证据

67producer源和11裁判源分别在执行前冻结。前置为旧固定单例的独立RAW及1诊断通过；其public receipt与fullaudit同时绑定，新source review和root admission指向相同版本。startup/setup异常保留与异源resume漏洞的旧红例及最终12CPU/独立4回归保留。所有32计划项进入分母，零异常不代表可以省略失败保留机制。

paired SETUP未导出数值nq getter，维度来自源guard、三轴RAW及独立重积分，不能编造安装读回。RAW_SCHEMA中继承的NATIVE_DEV_RESULT表述与实际TERMINAL有差别，独立审计已按真实17输出验证并披露。source不追溯改写。

[完整695成员原件包](complete_native_paired32_bundle.tar.gz)约5.45MB，包含67源、11审计源、32案例完整记录、逐case审计/诊断claim、唯一matrix快照、准入与来源绑定。[归档验收](BUNDLE_VALIDATION.json)逐成员重新读取SHA，0SDK/weights/link/traversal/duplicate/凭据签名发现。独立审计绑定原采集路径；没有声称整个物理审计已在异机自动重跑。

## 学习与论文的下一门槛

这组实验验收四种真实控制器实现，并给出强规则对照平局。当前不支持agentic必要性、经验吸收或神经策略优势。后续应复用已完成的VerifiedReplay接口，先解决完整timed+hold示范0/20和观察交付缺失，再收集新的合格数据、训练共享策略，与同信息强规则/辨识+MPC/DAgger比较；新任务图/目标/依赖另作前瞻留出。旧C5、thermal及C22学习结果保留原范围，不拿本组机器人代理或规则修复代替真实化学/策略吸收。
