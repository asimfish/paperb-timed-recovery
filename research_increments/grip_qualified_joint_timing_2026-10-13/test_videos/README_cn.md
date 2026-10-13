按冻结video_case_ids选择4条同固定条件（质量0.9、位置target FIFO12tick）的测试录像，覆盖4方法。只根据完成receipt和实际6fps原生RGBD记录导出，未读取成功率或时间得分选择视频。VIDEO_EXPORT_PLAN.json保留16测试完整capture名单，其中仅4条预先录制视频；其余stage图不转成假视频。

这些画面来自IsaacLab/PhysX仿真，不是真实机器人硬件或化学终点。每条原生录像168帧，对应测量的native physics时钟；MP4以6fps编码，不插帧、不合成、不修改场景。6fps视频不是25ms时间合同判据。

每case的VIDEO_PROVENANCE.json保留原JPEG SHA和录像时间；VIDEO_VALIDATION.json另核对逐帧原RGBD JPEG/NPZ byteSHA、RAW poststep native clock/epoch、ffprobe帧计数及完整CPU ffmpeg解码。原native未压缩RGB SHA只能作为录制器元数据，不能从有损JPEG/MP4重新计算。原深度NPZ保持不动，MP4只包含RGB。

source_snapshot/保留本次CPU导出工具及source哈希。可运行export_frozen_test_videos.py --root <冻结执行root> --out <工具root/test_videos>，已有验证视频只核验不覆盖；--watch使用inotify等待worker terminal文件，物理worker独立继续，不启动GPU、fit或simulation。snapshots/保留导出进度或错误，失败输出不会删除。
