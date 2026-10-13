更正：此前把旧四条校准描述为“没有任何 active 控制参数读回”，这一表述过宽。逐条读取原始 setup/boundary_state.json，并绑定冻结的 PhysX getter 源码后，可确认四条旧轨迹在 1200 步 warmup 结束时，均导出了九关节的实际 K、D 和力上限；手指读回值是 K=800、D=40。阶段 manifest 同时记录物理时刻，native_clock 记录了这 1200 次推进。旧 boundary 本身没有独立 epoch 或 callback 计数字段，本报告把关联证据和直接字段分开列出。

旧数据仍缺少 matched 30 步之后、任务开始安装前后及任务结束的专门完整参数快照。30 步比较文件中的 drive_state_equal 只是保存的比较结论，不能补成可独立复算的完整参数数组，也不能由 warmup 一个端点推出任务期间逐步参数不变。

资格实验与新 20 条源代码中 original_failed_cohort_active_readback_available=False 的原文保持封存，但这里明确登记为 metadata overstatement；不会把它事后解释成仅指“三个专门快照”，来掩盖原文的宽泛错误。所有旧 source、RAW、审计封存、评分、失败结果、预算和分母均保持不变：旧校准仍是适格 2/4、整体拒绝拟合；新资格与新四校准的既有判定也不因这次资料更正改变。
