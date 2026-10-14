# 最小 collector 接入位置（0.3）

本文件只在新目录继承，不改0.2。outcome必填label_kind，chunk预声明required_for_execution。EXECUTION_OUTCOME的TRUE晚于相关实际submit/APPLIED，STATE/PROPOSAL不能执行成功。UNKNOWN不借后来控制升级，optional尾部须标签前显式mask。跨chunk全任务仍由独立全任务合同验证。

这套接口已经可以 CPU 运行；未接入 native collector。本次 production 合格行、入训行、θ 更新都是 0。离线 BC 使用特权教师是合法设计，不要求教师曾通过相机决策。因果模式仍要预先定义，不能把旧缺失交付状态写成已交付。

1. 采集前创建新版本 header：原 episode/actor epoch、clock、actor 源、原 role、group/split、实际 protocol/source/split plan SHA、允许的 audit/teacher source SHA。生产 writer/reader 同时由 collector 传入外部 expected pins。已见任务可采入 TRAIN；旧 test/calibration 的训练用途明确声明并保留 original_role。未来 heldout 不得已见，同组不能拆到不同池。
2. renderer 或合法 public sensor 返回快照后，立即持久化不可变 bytes 与实际 capture timestamp，再记录 capture。JPEG SHA 只验证编码后 bytes，不声称重建 uncompressed RGB。图像、depth/proprioception 必须同 epoch；clock 的 native→ns 换算方法写入前瞻协议，原 native scalar/step/source-order 原件另保留，不能以理想 dt 替代真实时钟。
3. ONLINE_DELIVERED 在学生真正收到 DTO/asset handle 后记录 delivery；decision 后记录 chunk。在 OFFLINE_CAPTURE 中前瞻声明捕获快照可作为离线学生输入，capture-before-future-submission 是监督配对依据；不伪装 teacher 看图或在线送达。same-time 以 recorder 全局 seq 证明源代码次序。
4. 实际 middleware submit 点记录未来提交 target/request，包含 chunk/slot 身份；channel 实际 application/drop/reject 单独记录。proposal 不等于提交，ACK 不等于物理 effect，尾部未执行 mask 不能变动作标签。原 native driver 的 continuous physics、资源等待、accepted 不可取消等原语义不变，本接口不代替它。
5. 学生 rollout 单独记录 visit 的 actor/obs/state digest。教师查询把 source/特权输入/target 时刻放 supervision 文件，并绑定学生实际访问状态。先验 expert replay 不是 OPD，BC 特权标签也不自动变 OPD。实际训练、教师查询计算计费与安全 exploration 是后续实验原有授权下的实现，不是本增量新增审批条件。
6. 独立 audit 原件仍由 driver/referee 原通道保存。supervision 只挂源 SHA、三值目标、reward mask、失败/恢复以及原 anchor identity；不回写 student features。恢复局部已验证并不改变全 episode 失败，未定义 reward 不补 0。缺失或不匹配留 UNKNOWN/拒绝原件，不能丢掉分母。

现有最小挂点是机器人 native_probe 既有 render-before-next-FIFO-step、target submit/application 和独立 RAW。CPU rotor driver 只有 public packet/command，可合法采 state/control，却没有 RGB，不称 VLA 数据。接入新 supported-handoff collector 时，应复制到新的 source closure，保持旧 currentA/paired32 原封存；不能向它们追加日志。

承重/交接资格尚不由此 recorder 证明。新 native raw 应保留 actual object velocity、effective/body gravity、kinematic/attachment 状态、实际对象质量和惯量读回；contact 的 point impulse/friction、作用于 object 的 target/finger/other force 分来源保留，未经 sign/units/aggregation 校验不转成载荷。静止或接触不等于已承重。若 240Hz 下要求 200ms sampled confirmation，应按 native time span 计数，均匀点需要 49 个 readbacks；CPU 10ms fixture 的 21 点规则不得移植。它们默认是 audit-only 证据；学生只有前瞻协议确实公开且已交付的传感器。

reader 的 observation catalogue 是独立索引，并非可整体拼给任意时刻策略的输入。每行 student_available_history_ids 只列在 decision 前已捕获/已交付的观察；未来 next observation 与 reward 属于监督 transition。递归私有键拒绝和 source pin 是可信 collector 的有限类型/来源检查，不能识别被重命名的秘密数值或证明任意外部文件真实拍摄，后续接入仍须独立源代码及 RAW 审查。
