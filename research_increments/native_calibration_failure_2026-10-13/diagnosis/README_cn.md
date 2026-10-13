# 重载运输失败：观察诊断与前瞻资格假设

这里只读既有四条原生校准：0.12 / 0.18 kg × 0 / 50 ms FIFO。四条都完整执行；轻载两条原机械任务通过，重载两条未完成运输和独立稳定释放。53,732 个任务样本全部保留，没有新增机器人 episode、重新积分或模型训练。

首次缺双侧有效接触早于相对位移超过 30 mm 和 tilt 超过 14.32°。在缺接触之前已经存在渐进滑移，不能据此把“丢接触”当作全部滑移的起点：

| 条件 | 首次缺双侧有效接触的 source tick | 相对漂移 >30 mm | tilt >14.32° |
|---|---:|---:|---:|
| 0.12 kg，FIFO 0 / 50 ms | 均未发生 | 均未发生 | 均未发生 |
| 0.18 kg，FIFO 0 ms | 5422 | 5763 | 5801 |
| 0.18 kg，FIFO 50 ms | 5899 | 6144 | 6214 |

同 FIFO 条件按实际应用的源指令对齐，轻重载 TCP 最大差分别仅 0.0378 / 0.0379 mm，arm joint 最大差 0.00279 / 0.00280°。运输中两组绝对 arm 跟随误差都存在，但重载新增差远小于瓶体的 30–250 mm 相对漂移。因此，新增 payload 导致 arm 跟随偏差并不是当前证据优先支持的主因。

原源码配置 hand stiffness = 800 N/m、damping = 40 Ns/m，闭合目标 24 mm。闭合后实际 finger 比目标高约 3.83 mm；记录的接触 impulse 除以实际 dt 约为每侧 3.0 N，主要沿 contact normal。重载滑落时 jaw 从约 55.6 mm 缩到 51 mm，再到约 48 mm，接触记录随之减少。这支持检查夹持力储备或接触几何稳定性的假设。

**旧四条没有 active gain / 实际 force limit / 有效摩擦对的读回，因此不能称“实测 controller stiffness800”或“已证明摩擦不足”。** `USD_AUTHORED_READ_ONLY.json` 与 `MATERIAL_BINDINGS_READ_ONLY.json` 仅是离线 USD 组合检查：所查看的实际瓶盖碰撞路径绑定约 0.95 的材料，资产中另一约 0.05 的材料不能直接当作这些接触的摩擦系数；finger 未解析到显式 physics material。真实 PhysX 材料数组仍需新资格记录读回。现有 contact report 没有 friction anchors，不能据此恢复总切向摩擦力。

原生 RGB 在 lift 末两质量外观接近；transport 末重载手部已无瓶体，瓶体位于转盘/台面附近。比较图使用原 JPEG，没有修改其中的物体。时间、epoch、原 JPEG 与原 native RGB SHA 在 `FRAME_PROVENANCE.json` 中绑定。

下一步前瞻假设只改一个 actor 参数：双指 hand stiffness800 →1600；保持 damping40、关节目标、arm、质量、摩擦、FIFO、全技能时序与原机械门槛不变。它是一条 mass1.2/FIFO0 完整技能资格轨迹，不是测试集成绩或根因证明。

候选先按原800配置完成全部场景 warmup 与 matched30-tick 原 baseline PASS，然后在 task 前公开安装新控制参数。active PhysX K/D/maxForce before/after/end 读回，其他7arm K、全部 damping/force limit exact不变；另核查 native time/callback没有推进、fresh physics-view 与 cached scene-data 状态指纹各自一致。所有 failure 继续保留。若资格成功，仍要独立新协议完整四条校准后才能拟合，不能重用本资格结果或删除旧重载失败。

固定原 source 时长避免把 transport 放慢而挤占 H18 / 最短技能17秒的合同空间。当前还没有独立验收通过的资格结果；状态仍是观察诊断，无已证实修复。

主要证据：`DIAGNOSIS.json`、四条逐样本 CSV、`payload_failure_curves.svg/pdf/png`、原生 RGB 比较图和 provenance。`diagnose_payload.py` 只读取 frozen raw，输出指标不是新的机械计分器；原机械结论仍由原 scorer 与独立 auditor 提供。

接触数据字段语义参照 NVIDIA [Contact Reports](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/extensions/runtime/source/omni.physx/docs/dev_guide/contact_reports.html)；冲量除以记录的实际 dt 是时段平均量，不是摩擦裕量证明。
