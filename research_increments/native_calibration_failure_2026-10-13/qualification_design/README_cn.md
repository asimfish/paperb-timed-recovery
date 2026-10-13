# 单参数夹持资格设计：冻结 source，与运行结论分离

本目录保存 mass1.2 / FIFO0 的一条完整瓶体技能资格设计。原四条校准中的两条重载运输失败全部保留；本设计不回写失败轨迹，不改变机械计分门槛，不删重载，不拟合校准包络，也不作为16条主测试的一部分。

假设是增大夹持力储备可能改善运输稳定性。唯一 actor 参数变化为双指 hand stiffness800→1600，damping40、关节目标、arm、瓶体质量/惯量、摩擦、FIFO及原13427条完整技能指令不变。保持原技能时长，不能通过放慢 transport 挤占未来H18/18.5、最短技能17秒合同空间。它是一个前瞻资格假设，单次通过仍不是统计因果证明或方法胜出。

候选先按原800配置完成warmup1200和matched30-tick原baseline PASS，再在task之前公开安装1600。不能只改USD authored或在restore之前改cfg。active PhysX读回双指K800→1600，其他7arm K、全部D/maxForce须exact相同；同时只把同一个K镜像到implicit hand actuator缓存。native time/callback不推进，fresh PhysX状态张量与cached scene-data张量分别比较before/after指纹，禁止task内物体或关节状态setter。任务结束再次读回K/D/maxForce，独立RAW审计须验证全指令、FIFO、epoch、质量/惯量、原机械条件及独立稳定release。

`summary.json`、`protocol.json`与`READBACK_DESIGN.json`给出前瞻角色、准入和读回契约。分母为1条qualification；未来主矩阵16条另列。contact/release/duration的EARLY或PASS不是本资格的主指标。源中保留原计分器与所有门槛，资格必须满足完整执行、原机械任务、接触与独立稳定释放以及安装/全程参数验收。

`source_frozen/`为原117个冻结文件的精确副本，`EXECUTION_RELEASE.json`为source closure。压缩归档可下载，`ARCHIVE_VALIDATION.json`逐member重开验sha。外部IsaacLab/IsaacSim与USD资产依赖以原pin记录，资产及完整环境没有在本归档中重分发；本包不能当作无需这些依赖的独立仿真器。

8项CPU假接口/静态lineage预检通过，native episode=0，不能替代运行时读回或机械审计。GPU24GiB空闲门槛及UUID/minor/DRM、单GPU一owned worker/锁保持不变；资源拒绝不是物理episode，真实启动后的失败保留。实际执行、原始日志与独立审计由另一个结果组件发布，本目录不承诺资格已通过。

若此资格被独立验收，仍需另立冻结协议运行全部四条新校准，再独立审核、冻结校准包络，然后运行16条新测试。不能把本资格或旧失败挑选成校准样本，也不能追改旧源或事后调门槛。
