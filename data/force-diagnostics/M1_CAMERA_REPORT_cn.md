# M1 已记录操作片段：二级相机编码报告

这是结果后的相机展示编码，使用原前瞻 f8a 读器 RED 审计中已接受的 base camera 分项；不是新的前瞻独立审计，也不构成完整 force RAW 验收。原 force RED、strict sampled hold FALSE、训练准入0、新权重0保持不变。

案例 dev_seen_force_channel_diagnostics_002 的全case原生采集已完整结束，任务RAW共14,007步。视频仅显示其中保存的操作窗口：168个真实JPEG帧，task指令索引2160..8840，实际同epoch SDK原生时钟14.133334070444107..41.96666885539889秒，保存帧跨度27.833334784954786秒。全部177个RGBD captures还包含额外phase-boundary记录；它们没有被全部放入本视频。

视频6Hz、640×400、168帧、展示时长28秒。168个源JPEG及video_frames/capture_index两份metadata再次匹配原425-member RAW摘要清单和相机审计记录；ffprobe完整解码验证168帧。无插帧、假帧、旧ARIS拼接或人工追加末尾重复帧。Poster精确复制source ordinal0 JPEG，未加文字或编辑。JPEG有损，无法反向验证pre-JPEG raw RGB摘要。

MP4 PTS只表示回放展示时钟，不能作为物理作用时钟、host wall或相机曝光时钟认证。源native clock为包含warmup/transient原点的同epoch绝对SDK时间。没有学生实际图像交付、真实硬件、LLM控制或化学成功声明。

首次force拒绝native时刻20.12500104960054秒没有相等clock的视频帧。最近前帧为task3560/sourceordinal35/native19.96666770800948秒（差−0.15833334159106016秒）；最近后帧为task3600/sourceordinal36/native20.133334383368492秒（差+0.008333333767950535秒）。这些只是最近已保存的相机画面，不是exact同刻受力快照，也不能补回被丢弃的force标量。

编码器不读取force数值、大force RAW或vendor SDK，不重跑native/GPU/physics。累计M0/M1尝试仍为2，本编码新增尝试0。SOURCE.zip只发布有界二级编码器源码和协议，复现需要原私有JPEG及审计输入；不是整个机器人系统或全量RAW发布。
