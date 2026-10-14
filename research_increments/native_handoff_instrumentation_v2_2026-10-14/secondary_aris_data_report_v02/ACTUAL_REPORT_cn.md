# ARIS 实际单例：次级CPU读取与getter机制描述

Case：`dev_seen_handoff_instrumentation_002_aris`，DEVELOPMENT_SEEN，完整分母**1**。原生作业由另一分支执行；本root取消重复。本报告没有新原生运行、GPU作业、训练或权重更新，不是第三独立裁判。真实epoch仍为`paperb_handoff_instrumentation_v1:<case>:<protocol>`；没有改名或倒填新时钟。

原processor父source在新outcome前冻结；本次secondary scope在已知terminal COMPLETE、RAW计数及独立审计event整dict metadata不一致后重绑定。首版只改case/execution/protocol三常量、输入pins和scope文档，物理getters/validator不变；实际读出177个depth形状红。旧16source及actual红完整保留，未覆盖。SDK camera.py明示depth为(H,W,1)，producer直接保存这一单channel numpy形状。v02只修exact(height,width,1)浮点ABI，不squeeze或接受错误axis、多channel、整数、NaN、负深度或负无穷。

新focus8项CPU检查实际通过，旧CPU30逐字继承而未重跑。v02第二次NumPy1.26.0/Pillow CPU读取同一case获得`PASS_SECONDARY_COMPLETE_DATA_READBACK`、0 findings。两次reader reads不是两个trial。旧source及红件的hash/size逐字复核，物理/FIFO、source、clock、运动与时间阈值均不变。

| 实际原件/观测 | 结果 |
|---|---|
| physical snapshots | 28,016：TASK_BEGIN1 + PRE_WRITE14,007 + POST_STEP14,007 + TASK_END1 |
| states/dispatch | 各14,007；PRE/POST与state时钟及实际pose精确对应 |
| actual submit/apply | 各13,995；12 tick flush，末端pending0；不是proposal或ACK |
| RGB/depth | task append176 + initial1 = capture_index177；177个实际JPEG SHA/decode及depth NPZ读回 |
| depth ABI | 每个原shape[400,640,1]、float32保存；全部finite，未impute/squeeze |
| mass getter | 所有28,016为0.13500000536441803 kg |
| scene gravity/flags | 所有28,016为[0,0,-9.8100004196167] m/s²；gravity-disabled0、simulation-disabled0 |
| PRE composer | instantaneous/permanent各14,007 inactive，保存的body-frame force与torque输入为0 |
| actual COM linear speed | `get_velocities` WORLD COM，14,007 POST样本，最大0.3161562525850229 m/s |
| active backend边界 | kinematic/完整constraint inventory仍UNKNOWN；没有已验证contact force balance/卸载 |

速度图直接绘制真实getter的线/角速度，未用旧pose finite-difference proxy。质量、gravity、flags和PRE输入一起保存在完整28,016行CSV；inactive composer只证明该输入buffer没写力，不证明机器人接触力、所有外力或独立承重。USD authored/composed状态不是全部active backend约束。

原保存事件的grasp onset3599/confirmation3601、stable-release onset8039/confirmation8046，以及missing bilateral ticks8028..8038（11点）逐字保留，均来源于原RAW score/event文件。旧timing子项为PASS，但`joint_with_sampled_hold=False`、scientific/training admission=False；本次不把机械姿态、低速度或图片作为承重成功证据。独立event metadata-schema比较的问题由root另一新reader版本处理，本secondary不充当其第三独立验证。

当前独立load-bearing始终**UNKNOWN**，旧sampled hold **FALSE**。这些真实记录不是成功示范；新入训、学习验收或化学终点均0。`ACTUAL_GETTER_MECHANISM.json`内对旧2D reader期待的文字是inherited red契约背景，v02实际depth期待以SOURCE_RELEASE和DEPTH_ABI_EVIDENCE为准。

科学图`figures/actual_velocity_release_mechanism.{svg,pdf,png}`展示全轨迹、释放附近的实际速度/11个缺接触样本、以及PRE输入；标题明确DEVELOPMENT_SEEN、oldholdFALSE、independentloadUNKNOWN、非成功学习示范。

视频只使用原`video_frames.json`所列168个真实JPEG，逐一确认属于capture_index且SHA匹配。原序列经实测为6Hz；CPU libx264编码，video零点对应native14.133334070444107s（task elapsed9.000000469386578s）。每capture的native/task时间、JPEG identity和实测video PTS映射保留，最大误差0.0000017849547866433113s。第169个编码display frame是最后原JPEG重复显示，不是新capture；无AI补帧、运动插值或重新render。video不作为物理事件计时来源。poster是原JPEG逐字复制，像素未编辑。

相机均OFFLINE_CAPTURE、policy_delivery=None；JPEG编码后SHA已验证，native rawrgb SHA无法由有损JPEG反算。depth byteSHA是此次CPU读取生成，producer没有既有depth byteSHA可比。影像是实际原生仿真相机记录，不称现实机器人或化学实验视频。

所有新report/source/CSV/figure/video按SHA与byte size封存，archive逐member重开；不修改原case、旧reader/红件、public repo、manuscript或其他sealed目录。先前ffmpeg4.4不支持concat的option关键字造成的媒体生成错误也保留；v02以已验证6Hz序列编码，未放宽任何物理、时间或图形判分阈值。
