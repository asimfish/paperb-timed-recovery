已完成1条12秒CPU原生三转子开发预检：1200steps/1201RAW，MuJoCo3.3.7，15源预冻结；另1次command-driven独立重积分1201samples的state/time误差为0。只有开发parallel case，formal32/calibration/fit/weights/GPU/LLM均0。第三方审计待完成，不能称论文方法性能。

实际B事件发生于[.44,.45]s，actor只从lagged公共packet在.55s获得[.40,.45]s原ledger。A stop事务ACK.85s未切drive，随后公共观测触发retry ACK1.07s有效切drive。C request1.06s实际等待共享资源至1.75s开始服务，ACK2.20s关闭drive，等待期间原生物理照常推进。B预约在1.75s真实将torque从.06切至.045。RAW A停止[2.61,2.62]s、C停止[3.75,3.76]s，均21个正样本、200ms确认；原事件、开发时间窗、真实故障/恢复、资源容量、B采样维持均TRUE。图无边的TRUE是vacuous，不是任务图OOD通过。

这些是机械原生state/action事件，不是RGB/VLA、真机、化学终点、连续维持或权重学习。控制输入只有公开capture/arrival packet、事务ACK、预约和未拟合的开发nominal prior；ACK不含successflag，referee RAW ledger不会给actor。host计算不推进plant，但每次决策收费2个原生ticks；不能宣称模型真实实时性。

正式32草案目前被公开资源可达性分析阻塞：原B预约start1.50s与C450ms非抢占服务造成ACK/物理stop可达支撑间隙，指定D2.8/3.1下6/8条件不能有正witness。详情在PUBLIC_RESOURCE_REACHABILITY_WARNING.json；不是跑heldout/fit得到。草案和已冻结development源均未改。要先发布prospective新版并独立核对每个原合同的正witness，再冻结正式协议。一个开发TRUE不能掩盖该阻塞。

全部原件、15源snapshot、动作/ACK、公共capture/delivery/actor inputs、私有效果和独立计分完整归档；重开逐成员SHA验收见ARCHIVE_VALIDATION.json。不要挑选成功样本作为新场景扩展结果。
