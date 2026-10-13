# 场景接口与物理终点缺口

状态：只读源码审计与扩充设计。已有资产、控制代码、历史采集和新实验准入是四个不同状态；这里不把控制代码存在认定为完整场景已验收。

## 实际读到的基础设施

本轮读取 Paper B 上轮场景文档、NEXT_EXPERIMENT_PROTOCOL、PROGRESS，并只读检查独立复制目录 /data/liyufeng/paperb_benchmark_scene_timing_20261013_v1 的源码。SOURCE_ORIGIN 指向 benchmark V79；A-r7 原 placement plan 含 FR3 A、UR5e B/C、炉/干燥箱、XRD、托盘、转盘、天平、移液工具等几何资产。

scene_cfg_twin.py 提供真实 articulation/rigid-body 配置、关节目标执行和站点 RGB-D/腕 RGB 相机；炉门和 XRD 窗是受驱动关节。contact_telemetry.py 记录 PhysX 接触冲量、分离、碰撞体路径及采样 tick，但覆盖范围明确不能直接保证所有接触；缺少接触报告不能单独证明分离或绝无碰撞。原 plan 的 preparation_status 仍为 STATIC_LOADED_GEOMETRY_VERIFIED_RUNTIME_PENDING，不能覆盖后续各阶段审计；本轮 A 的新组件结果才是已执行证据。

额外只读检查 /data/liyufeng/goai_workflows/alab_twin_collect 的 b_heating_execution.py、b_heating_parallel_execution.py、c_full_xrd_candidate_execution.py；它们的 SHA256 与原 source_manifest 全部相等。B 代码实现实测托盘运输、炉架支撑、释放、退出与关门；C 代码实现 holder 接触夹持、XRD 窗关节、装载/释放/退出，明确把 weighing/diffraction 保留为任务 proxy。源码说明不等于历史所有试验都成功；本次不读取/运行整个 B/C campaign，不给新的成功数。

PsiBot native_package_v50 的 sim_backend.py 有 120 Hz PhysX、7 维 arm2＋6 维 hand2、head/chest/third RGB、物体/手指接触与关节状态；该 campaign 禁用 particle fluids、固定初始化、由自身准入管理。它可作为另一个机械操控接口参考，不是滴加/搅拌/温度过程验证器，不能借现有 job 产生 Paper B 新样本。

## 各场景的明确准入边界

| 场景/任务 | 已有控制与观测 | 独立事件可用性 | 下一项必需验收 |
|---|---|---|---|
| A-r7 B-T0 | FR3 关节目标、重力补偿、瓶取放、RGB-D/腕相机；本轮前已有接触计时轨迹 | 连续 native epoch 接触冲量与关节/物体数组；三样本确认需区分发生/确认 | 新质量设置、延迟 FIFO、分离/释放事件与采样误差；实际等待期间推进器 |
| A-r7 contact→release | 现有夹持/释放代码与接触日志可复用 | 必须新注册“有效失去双侧夹指接触＋独立支撑”定义，不能以 open 指令作终点 | 对 transient loss/re-contact、左删失、单侧接触残留、支撑后稳定及确认时延做校准 |
| B 炉/并行托盘 | UR5e、夹爪、loaded root feedback、炉门 actuator、support contact；B 空间运输代码存在 | 支撑、释放、门位可测；代码没有实际功率/温度/化学采样接口 | 热过程推进、通断功率传感、温度及余热模型校准；独立连续设备时钟；原 B 源成功审计逐条复用准入 |
| C XRD/测量 | UR5e、holder grip、driven Window_slide_joint、RGB、关节及物理放置 | 窗位/holder 支撑事件可测；当前 weighing/diffraction 是 proxy | 真实称量/衍射测量接口及 trigger/capture/completion 的独立时间；共享设备排队日志 |
| C5 颜色后 2 s 停滴 | YAML 与 F0 世界；旧 Isaac bridge 的 RGB 颜色/动作接口 | 旧代码直接 flow=False；未见粒子/阀后流量衰减独立 stop | 首先非化学安全滴水设备/阀模型，独立 flow sensor 或接收质量差分，RGB 颜色触发独立校准；真实反应终点另验 |
| C6 搅拌 120±10 s | YAML、F0 计数、旧 native rotor 显示 | 旧 bridge 直接 set_angular_velocity 开/关，不等于电机驱动与负载停转 | 新 motor torque/速度控制、转速观测、起转/停转区间及负载/摩擦漂移；不能仅累计转动秒数替代原 duration 合同 |
| C13 M1 加 A 等 D 再加 B | YAML 随机 A onset 5–40 s、公开 D=30–90 s、ε=0.15D、瞬时容器提示；RGB bridge | 旧 bridge 颜色赋值即 add_A，TCP 达到 marker 即 add_B；不是物理液体转移 | 独立容器/添加量事件＋无钟表输入审计＋随机提示采样；agent 不读取 hidden onset/verifier log |
| 新 B-T1 加热持续 | 可复用 B 炉的装载/关门几何 | 未看到物理加热开始/有效停止及温度观测 | 先明确“电功率停止”还是“有效热过程结束”，建立温度/热剂量及余热；不能把关门时刻当加热起点 |

## 旧语义后端可以与不能承担的角色

task_worlds.py 自称 F0 contract backends，C5 stop/C6 start-stop/C13 addition 都由 action 直接发 event；它能测试合同解释、trace/replay 和错误分母，不能作为化学物理证据。isaac_bridge_native.py 明确称 reagent transfer/color kinetics uncalibrated semantic/surrogate processes；其 native robot 与相机真实运行，并不能把相邻语义事件升级为真实流量或反应。thermal_dose.py 是标量热剂量 surrogate，可作为策略与判据组件，不自动变为原 B 炉的 native 热过程。

下一步最小可执行对象是 A 原生机械 duration 与共享设备机械 prototype；C5/C6 的“原任务完整落地”仍有上述独立传感和动力学工作。每个场景必须附 scene/version/model hash、实际动作接口、观测 allowlist、独立事件定义、校准 receipt、世界是否在 planner 等待期间推进、完整失败轨迹和新 episode ID。对跨进程 cold rebuild，只能复用刚体空间恢复；尚在运行的热/搅拌时间需要设备连续性证明，否则新 epoch、新实例。
