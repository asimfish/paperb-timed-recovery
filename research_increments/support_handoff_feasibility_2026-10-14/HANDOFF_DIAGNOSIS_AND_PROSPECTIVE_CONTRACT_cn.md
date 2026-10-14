# 旧夹持负结果与下一支持交接合同

本记录只分析既有、已见的20条原生仿真轨迹（4校准、16测试）。原角色、时钟、物理事件和分数保留；本轮没有新的物理 episode、GPU 运行、权重更新或大帧复制。这里的候选区间属于固定技能的机制诊断，不是修改旧失败标签的依据。

## 诊断结论

全部20条、277,864个任务样本通过原 states/contact/contract/NPZ SHA 与位姿数组精确检查，使用原 SDK 的 NumPy 1.26.0 离线解码。每条在原稳定释放之前都有“目标 weigh_pan 的有效接触＋双侧有效手指接触＋8个样本几何稳定”的重叠区间，跨度约1.03–2.62秒。这表明原技能在几何层面提供了先支撑再张开的候选机会，尚不能证明独立承重，也不能证明所有策略都可行。

原严格夹持20/20仍为 FALSE，每条在张开后、复合稳定释放 onset 之前有11个缺失双侧有效接触的样本。该检查的终点是“无手指接触、足够张开且稳定”的复合释放事件，因此候选交接事件和该终点不是同一事件。不能把 contact→release 的事件间隔说成连续夹持，也不能把新交接目标套回旧数据，把0/20改为成功。

代表 `test_m090_d12_joint_exact_grid` 的原合同 SHA 为 `fac0c7056f24663b1f8e878098a0c5861992206621831eaea8f9e07f5993b471`，14,007行 RAW。候选区间覆盖 ticks7404..8027（624个采样点，2.5958秒）；原 strict 缺失 ticks8028..8038，原稳定释放 onset tick8039，confirmation tick8046。位姿差分速度代理最大约0.01499 m/s；“8点最大位移≤2mm”不能证明任意指定的低速度或载荷稳定。

`CASE_INDEX.csv` 列出全部20条原 contract/state/contact/NPZ SHA、样本数、原角色、原严格标签和候选区间。许多滑动窗只属于同一条 episode，不增加分母。4条校准与16条测试也没有重新合并为新的独立评测。

## 当前证据为何仍是 UNKNOWN

目标支撑接触与双侧接触来自独立 RAW 接触回调，排除了背景桌面被当作目标托盘。但原日志没有足够的物理读回来判定负载是否已转移：

| 需要区分的量 | 旧日志可用信息 | 当前结论 |
|---|---|---|
| 目标物体是否接触指定托盘 | 原碰撞体身份及非零有效 impulse | 可确认采样接触；不证明独立承重 |
| 真实物体运动 | 原 object pose；可算位姿差分代理 | actual linear/angular velocity 和可靠 acceleration 未记录 |
| 有效重力与外部约束 | 配置/控制源码可见部分信息 | 缺物体有效 gravity、gravity-disable、kinematic、attachment/constraint 的一致读回 |
| 目标支撑对物体的力 | point impulse、friction anchor 原向量 | 作用对象、正负号、单位、坐标系、dt 与聚合/重复计数语义未独立验证 |
| 机器人是否卸载 | 手指接触与几何稳定 | 缺目标/机器人/其他接触的独立载荷分解及 force balance |

point impulse 与 friction anchor 分开保存；本分析没有把二者相加后除以 dt，也没有把第三分量解释成已校验的牛顿力。机器人 `gravity()` 补偿或配置中的默认 gravity 不能替代物体有效重力读回。静止也可能来自机器人夹持、约束、无重力或其他外力。因此20/20独立 load-bearing 状态为 UNKNOWN，新增 full-support/DP-success 准入为0。

## 下一合同必须分开四种事件

建议在新数据上定义独立的 `support_touch`、`verified_load_ready`、`finger_release` 与 `stable_supported_release`。这里是合同草案，不是已冻结阈值或新结果。

1. `support_touch` 是目标物体与指定支撑的有效接触，不带承重承诺。
2. `verified_load_ready` 要求目标支撑、机器人卸载、实际运动、有效重力和力平衡的证据同时满足新合同，并经历指定 native-time dwell。双侧有效夹持可在这段交接前仍存在，但竖直负载必须已由支撑承担到合同约定比例。
3. `finger_release` 是已确认 grasp 后，左右手指均无有效接触的物理事件。actual applied open 与这个事件分别记录；queued/submitted open 不等于发生释放。
4. `stable_supported_release` 要求释放后在原目标支撑上继续满足运动、位置、载荷及独立稳定性合同，另有 onset 和 confirmation。

完整新交接目标应包含“原抓持持续到 load-ready confirmation，再张开，再稳定释放”，而不是要求双侧接触持续到一个定义上已经无手指接触的终点。旧严格合同的负结果独立保留。新的公开负载门槛、运动门槛、dwell、时间窗口与恢复预算须在新执行前冻结，不能根据这20条已见轨迹的成败选择。

若向上单位向量为 n，可用已验证的 force-on-object 测量建立条件约束：目标支撑向上分量达到合同的负载比例，机器人向上分量低于卸载门槛，且所有外力与 m(a−g) 的力平衡残差在校准界内。实际所需比例、误差界、运动上界均须来自新公开合同及独立 sensor 校准；原 impulse 分量不满足这些前提。g为0或物体被 kinematic/attachment 固定时，不能把相应静止事件称为重力负载交接。

事件判定采用三值：证据齐全且所有条件在误差界内为 TRUE；证据齐全且确定违反为 FALSE；缺字段、未验证单位/符号、边界不确定或 callback 缺失为 UNKNOWN。确认时间不能代替 onset。跨 epoch 不相减，缺失和拒绝仍留在完整任务分母；独立日志证明的是离散采样合同，不能宣称采样间连续物理真值。

确认应按真实时间跨度实现：N个均匀读回覆盖 (N−1)dt。例如机器人 dt=1/240秒时，200ms需49个读回；48个只有约195.83ms。21点/200ms适用于dt=10ms的转子组件，不能直接搬到机器人。旧8点几何窗只覆盖7个采样间隔，保持其旧语义。

## 下一次最小采集与教师接口

新 collector 应首先只增加已核实 getter，保持原场景、控制和安装参数。在新独立目录冻结 source、RAW schema、安装读回、资源上限与独立审查后，由 root 执行最多一条 instrumentation episode，700秒 cap；本分析不启动该执行。若 getter 仍不足，保留 UNKNOWN 并交具体缺项，不重跑旧 GPU 轨迹来改标签。

最小私有 verifier RAW 包括同 epoch 的 pre/post-step 时钟、真实物体 position/orientation、linear/angular velocity、质量/COM/惯量与 gravity/kinematic/约束状态，指定支撑与手指及其他外力来源的 force-on-object 原量与规范化证据，以及 contact callback 完整性。安装前/后/末端读回不是逐 tick 测量，若只提供端点则按端点范围报告。原始 SDK 量和转换后的量都保存，并用独立静载/动态已知输入验证符号、单位、dt 和聚合。

公开 actor/teacher 输入另有白名单和交付通道：contract、可部署 RGB/proprioception、被允许的公开 load sensor 或 verifier packet，包含 capture、arrival、delivery、decision、submission、acceptance、application；私有物体 pose、referee 结果与故障标签不能混入学生输入。若教师特权读取私有状态用于标签，记录为 teacher-only，并与学生输入分开。新增反馈需给同反馈强规则基线，不能只给所提方法。

RGB 原采集点在 post-step，合法动作标签应对应之后的 submission/未来 chunk，并明确 FIFO applied 与 effect。旧20条 policy-image delivery 缺失保留 UNKNOWN；未来可显式冻结 `OFFLINE_CAPTURE` 的因果采样协议，不能倒称旧策略实际读过该 RGB。每个失败、恢复和 reset 保留原事件/episode 身份、预算和资源账本。

先取得可独立验证的完整新示范，再开放对应目标的 DP-success 数据；旧轨迹可按原角色显式作为 legacy-seen、partial-mechanical-prior 或失败研究数据，不能伪装为未来 untouched heldout。后续恢复经验、学生访问状态标签和权重保留实验仍需真正的新采集与学习。本诊断没有神经 expert、OPD 或参数吸收结果。

## 数据可达性与版本记录

本次实际读取并核对全部20条原 RAW，根目录为 `/data/liyufeng/paperb_grip_qualified_joint_timing_20261013_v1/cases/`。旧私有 `TEST_AUDIT.json` 与 `PACKAGE_MANIFEST.json` 元数据路径当前不可见，因此采用 NAS 已封存、同 SHA 副本，路径及 digest 在 `SOURCE_ORIGIN.json`。这不是重新生成旧审计或修改旧说明。

已知私有 gzip archive 当前可 stat，大小1,431,681,218字节；此前验证的 SHA 为 `981a43522fdefad6fcfab97a7e37286b0bb28c835b46711fca03ed4990738a5c`。本次没有重新完整哈希该 archive，stat不能替代完整包验证。旧 RAW 仍是私有证据，不是已公开训练数据集或完整场景再执行包。

代表 V1 代码与输出保留。V1 的 tilt/goal 只在候选窗首点检查；V2 对同一8点窗口逐点检查，阈值不变，源码在全20离线 decode 前 pin。旧实验结果在本研究之前已经可见，这不是盲测。V1/V2代表候选区间相同，旧分数未修改。
