# 全16条冻结机器人时间测试

全新四条校准先独立准入并冻结经验min/max，再执行本16条测试；测试结果不用于调整源、eps、K或包络。全16都保留在分母，每方法4条固定实例。IsaacLab/PhysX原生仿真，非真机、非化学终点、非学习VLA。

| 方法 | 时间+机械 primary | 原机械任务 | strict sampled hold | primary+hold |
|---|---:|---:|---:|---:|
| nominal_prior | 0/4 | 4/4 | 0/4 | 0/4 |
| public_delay_prior | 0/4 | 4/4 | 0/4 | 0/4 |
| calibrated_interval | 4/4 | 4/4 | 0/4 | 0/4 |
| joint_exact_grid | 4/4 | 4/4 | 0/4 | 0/4 |

校准中点与精确联合网格在当前四个固定实例的primary计数相同；本矩阵未证明精确求解的额外物理收益。

contact与复合稳定release的onset由RAW独立提取、confirmation另记。相对事件gap不等价连续夹持；所有张开后至复合释放前的负双侧点保留，strict hold是独立同16分母指标。9DOF K/D/force仅前、后、末三时点完整读回，非逐tick参数遥测。动作仅插入3359/7439重复位置目标hold，不加速/覆盖物理状态。FIFO只对位置目标施加0/12ticks延迟，不是整个通信或LLM推理。

四格mass×FIFO是固定配对条件，D与H分别随mass/delay绑定，没有独立factor因果估计、随机seeds、统计CI或泛化成功率。校准盒是经验范围，任何测试落盒外的事实仍保留在逐行summary。预算只记录owned进程墙时上界。

RAW、实际控制安装preimages、质量/惯量、FIFO、事件、机械与保守分数均由执行前冻结的独立审计源复算。测试任务样本224,132，校准53,732另计。总体primary TRUE/FALSE/UNKNOWN为8/2/6；只有两条release明确LATE，其余先验非通过多为INDETERMINATE，不能称确定物理失败。新增学习权重0、真机0、独立化学终点0；完整科研验收仍MAJOR_OPEN。

图的每点来自同一冻结case，横线是保守误差区间，空心代表区间未完整落入±25ms。CSV、独立完整audit与source/calibration SHA一同公开；不是仅发布成功轨迹。
