# 四方法规格：同信息、同预算，强基线保留否证能力

四臂ID沿用研究草案；名称借鉴MATTERIX的HSM角色，但此为机械接口下的通用候选，不是其代码、机器人或化学实验复现。本目录不运行正式32条或拟合模型。

| 方法 | 规划及闭环机制 | 公平性要求 | 当前实现边界 |
|---|---|---|---|
| sameinfo_calibrated_batch_joint | 在第一公共B及共同model/history refinement可用后联合规划整个资源/图程序。使用同calibrated error盒；原名义center可另作明确ablation，不能代替强batch。合法blind A冗余对unknown none/drop覆盖；提交后不根据效果修改原事件或已发送指令。 | 同prior、同candidate/action预算、可用同精细公共估计。不能把batch定义为不看clock或不许冗余的弱对照。 | 初次public联合计划与center排序；正式immutable程序dispatcher待集成。 |
| sameinfo_robust_hsm | WAIT_B→PUBLIC_ESTIMATE→TEMPORAL_RESOURCE_GUARD→ISSUE→VERIFY/RECOVER。图guard使用物理onset预测盒，继承deadline，允许并发动力学和预先冗余。fresh postACK仍powered才支持观察式retry；反馈不及时且窗口紧时允许与其他方法相同blind redundancy。 | 同事件估计与prior；ACK≠success，confirmation≠onset；不为凸显agent取消预测/资源/预执行能力。 | 初次joint-safe earliest选择、公共失败诊断函数；完整HSM状态转移/剩余budget未集成。 |
| sameinfo_edf_event_replanner | 从public graph推导ready nodes及继承deadline，按latest-safe-effect/dispatch约束排序；预估nonpreemptive B、A、C calendar，再仅重排未发送意图。公共packet/ACK改变才更新计划。 | EDF应使用model delay/同anchor，不是按裸service ACK时间排序。已接受reservation不可撤销；不能读取实际fault或后验referee。 | 初次依赖ready EDF选择；完整rolling ledger/cancellation待集成。 |
| sameinfo_joint_interval_mpc | 每次有效public更新对剩余时域求联合interval/图/资源/action约束，含none/drop条件分支与future ACK→physical onset。只执行可撤销范围内的前段；公共feedback收缩分支后replan。 | 同预算；budget限制造成的搜索失败不能称全局物理不可达。persistent drop/未知模型需保留UNKNOWN；不把empirical盒称真实support。 | 共用bounded initial候选与joint objective选择；并非完整MPC或全policy全局最优。 |

共享预测把请求、service start、ACK和physical stop onset分开。原始B身份不可重建为counterfactual fullpower事件；model-derived refined bracket必须保留coarse原身份、输入包、prior、forward residual和条件性。A feedback能在收到新公共power之后收缩none/drop分支，不能人为固定60ms不确定性以制造MPC/query优势。

初次adapter候选域是earliest-feasible-A-prefix→C或C→两A，非所有合法program的全枚举。resource availability、deadline盒和graph三个谓词分别保存。若没有候选，输出`NO_FEASIBLE_PLAN_IN_BOUNDED_PUBLIC_SEARCH`，不声称物理或信息论infeasibility；要label不可达必须独立all-policy分析或明确诊断假设下的证明。

旧草案Bslot1.5、D2.8/3.1等有6/8资源不可达警告，仍保留并阻止其直接作为32可达矩阵。prospective_v2的Bslot.65、g.04、eps.15是另一agent的新版本设计/开发见证，不是把旧失败变成成功。其8配置已用于development可见；之后同配置×4臂只能叫固定配对机制比较，不能叫从未见过holdout或learned OOD。

共享public known-model估计和两A blind redundancy使强batch在新8个development见证中已能满足全部条件（见scenario agent独立组件；本目录无新native采集）。本目录的32条是4臂×8 synthetic初次CPU决策，不能与正式32native测试或8物理见证混计。

正式行为应记录每个decision的输入包/ACK/calendar、原coarse及refinement provenance、候选和预测调用计数、动作issued/pending、拒绝/异常、host wall及2tick charged timeline；四方法不能import Plant、private roster、referee或native getter。全面同信息强基线能解决该family时，结论是**本family不支持query或agentic算法必要性**。任何学习、跨episode context、吸收恢复经验或OPD收益都需另立未被此简单family解决的、预声明且可达的任务与验收。

当前初始only adapter的ABI拒绝边界是：任何已ACK反馈或已accepted的nonexternal A/C reservation均返回pending且不产生新program。即使ACK列表为空，已排队的A/C也不能重新获得完整动作预算。该guard只避免初始program重复提交；它不是正式remaining-budget ledger，也未完成上述闭环生命周期。修前重复提交反例与source/receipt保留供复核。
