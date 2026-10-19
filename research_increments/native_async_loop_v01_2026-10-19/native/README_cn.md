# NA1：一次原生异步 P0 闭环（2026-10-19）

**结论：** 一次正式原生案例正常结束，独立 reader 的 13 项检查全部通过。这是接线检查，不是任务、策略或时间精度的成功。

**环境：**
- Isaac Sim 5.1.0，PhysX `omni.physx-107.3.26`，IsaacLab 0.54.2。
- 场景、PhysX 参数、dt = 1/240 s 和 station-A 相机都与 M1 相同。
- 机器人 fr3_A，先 warmup 240 tick，再运行 1,200 个任务 tick（仿真时间 5.0 s）。

**结构：**
- owner 进程负责步进物理。
- 独立 CPU 进程运行此前的 P0 工程 checkpoint（200 次 CPU 更新，已知不准）。
- 推理返回的 8 槽动作经 AsyncBridge v0.2 记录，只能在各自原定的 tick 生效。

## 实测结果

| 项目 | 结果 |
|---|---|
| 推理 ticket | 149 个，全部返回，worker 错误 0；worker 正常退出，参数摘要前后一致，未初始化 CUDA |
| 1,192 个动作槽 | 150 STALE、1,042 SUBMIT。每个 ticket 的第 1 槽在返回时已过期，没有改时 |
| 通道结果 | 99 APPLIED，全部恰在原定 tick，每 tick 至多一条；943 REJECTED（超出关节限位，不裁剪）；0 DROPPED |
| 推理与物理并行 | 149/149 次模型计算区间与真实物理步进区间重叠，重叠时长中位 3.9 ms。worker 计算中位 5.46 ms（3.75–13.8 ms）。两个进程使用同一主机 CLOCK_MONOTONIC |
| 返回间隔 | owner 每个 tick 只读取一次返回，所以 148 个 ticket 在 1 个物理 tick 后被接受，1 个在 2 个 tick 后 |
| 状态守卫 | 全程未触发；臂关节速度最高 2.62 rad/s |
| 日志 | 3,884 条事件，8,313,288 B，正常 CASE_END，无删失 |
| 视频 | 每 10 tick 一帧，共 120 帧原生相机图像，24 fps 编码为 5.0 s。帧间隔即仿真时间，无插帧 |

## 必须同时说明的限制

- **策略质量很差，且符合预期。** 提交的目标中有 90.5% 超出关节限位而被拒绝，越界值最高约 ±38 rad。机械臂移动之后，P0 的输入已远离它唯一见过的 M1 episode。图中关节运动来自那 99 条在限位内的命令，不代表策略能力。
- **不是实时控制。** 物理步进本身中位 4.4 ms。但 owner 每个 tick 还要渲染、fsync 和写日志：每次迭代中位 169 ms、p90 543 ms、平均 250 ms，5 s 仿真共用约 300 s 墙钟。仿真时间不按墙钟节奏推进。
- **只运行了一次。** 这是唯一的正式原生案例：执行前在 CPU 上预演 4 次，原生只启动 1 次。预演发现 `nominal_offsets` 单位错误（应为秒，误传为 tick），在冻结前已修正，见 `REHEARSAL_NOTE.json`。
- **不涉及以下内容：** 任务完成、受力或承重资格、化学终点、S/F/R 准入、M/B3 学习对比、真机。

## 文件

- 冻结与准入：`protocol.json`（执行前声明）、`SOURCE_FREEZE.json`、`launch_attempts/`、`logs/gpu_wait.jsonl`、`resource_gate_refusals/`。
- 驱动胶囊：`DRIVER_CAPSULE.json`。服务器重启后 `/tmp` 下原有的胶囊已丢失，在本目录重建为指向 570.124.06 的符号链接。
- 案例原始记录：`cases/na1_p0_async_closed_loop_a1/`，包括 `ASYNC_JOURNAL.jsonl`、`RAW_WORKER_CHANNEL.jsonl`、`TICKS.jsonl`、`TICKETS.json`、`frames/`、`request_frames/`、`READER_REPORT.json`。
- 分析：`analysis/COMPUTE_PHYSICS_OVERLAP.json`、`analysis/figures/na1_timeline.{svg,pdf,png}`（`figures_layout_v01` 为首版布局，数据相同）、`analysis/na1_native_camera_1200ticks.mp4`。

## 下一步

1. 让 owner 按墙钟节奏推进：渲染移出关键路径，日志采用批量持久化，并把墙钟节奏写进协议。
2. 用合格数据训练的策略替换 P0，之后才能进入 S/F/R 数据采集和 M/B3 同预算对比。
