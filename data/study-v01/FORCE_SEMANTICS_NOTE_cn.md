# 受力符号、单位与坐标系：独立研究结论

这份记录只包含只读源码核对、一手文档和新校准设计，没有原生仿真、GPU、重积分或旧结果重评分。当前 `force_sign_qualification / load_ready / robot_unloaded / complete_backend_constraints / torque_balance` 仍为 `UNKNOWN`。

## 关键判断

“法向标量必定非负”不适合作为通用 API 数据格式前提。Isaac Sim **5.1.0** 的 `RigidPrim.get_contact_force_data` 官方示例包含负的接触标量，例如 `−156.449`，对应正 Z 法向量；计数与起始索引实际引用这些负值，并非未使用的缓冲槽。[官方 API 示例](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim.get_contact_force_data)

该例子省略 dt 参数，默认值为 1，因此这些示例数值应按冲量理解，不能称作 `−156.449 N`。它证明格式允许有符号数值，不是本项目的单位校准。[同一 API 的 dt 定义](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim.get_contact_force_data)

本机同一高层方法与中间 `RigidContactView` 的 docstring 也保留该示例。高层方法直接委托中间层；中间层调用张量 API `get_contact_data(dt)`，随后只克隆张量和选择传感器索引，没有取绝对值、截断、符号翻转或坐标旋转。下层扩展版本是 `omni.physics.tensors-107.3.26+107.3.3`。这建立了官方例子与本机接口之间的源码桥接，但 C++ 后端如何将 shape 顺序映射到 sensor/filter 顺序仍未由所读 Python 实现揭示。具体文件、行号与哈希见 `INSTALLED_API_PROVENANCE.json`；没有复制供应商代码。

## 明确说明、未说明与本次现象

| 主题 | 已核对的证据 | 可得结论与边界 |
|---|---|---|
| 数据符号 | 上述一手例子包含被引用的负值 | 否定通用 `scalar ≥ 0` 格式规则；不保证任意负值都具有正确物理含义。 |
| 聚合 | Omni Physics **107.3** 张量 API 示例将各标量与对应法向量相乘后求和 | `Σ sᵢ nᵢ` 是应核对的表示；不能改为 `Σ |sᵢ|nᵢ`，也不能把它与 pair matrix 再相加。[张量 API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/runtime/source/omni.physics.tensors/docs/api/python.html#omni.physics.tensors.impl.api.RigidContactView.get_contact_data) |
| dt | 同一张量 API将参数定义为冲量转换所用的仿真时间步；本机把 dt 原样传给后端 | 现有 getter 已接收 `1/240`；不要再除一次 dt。数值缩放仍需同一时刻的 `dt=1` 与 `dt=1/240` 配对校准。 |
| 覆盖范围 | 本机 IsaacLab 数据类声明 net 与 matrix 为 world-frame **normal-only**；切向力另外保存 | net/matrix 不能被叫作完整外力；完整约束和其他 wrench 覆盖仍未知。 |
| 法向量方向 | PhysX **5.1.0** contact-pair 文档规定从第二 shape 指向第一 shape，并把点和冲量描述为世界坐标 | 该低层 shape 规则不能直接替换为“filter 指向 sensor”；它也不是本机 C++ 构建的完整版本认证。[PhysX contact-pair](https://nvidia-omniverse.github.io/PhysX/physx/5.1.0/_build/physx/latest/struct_px_contact_pair_point.html) |
| 实际 frame | 本机 IsaacLab 使用 `_w` 字段并直接消费 getter；中间桥接无坐标旋转 | 支持 world-frame 的接口意图；应通过旋转整个夹具与重力的独立试验验证本机实际输出。 |
| 缓冲寿命 | 本机 normal/friction getter复用 count/start 成员 | 两次 getter 之间必须完成选中范围、计数与索引的快照；不能保留 provider 引用后再解码。 |

文档**缺少**普遍非负保证本身不是负值合法的证据；这里更强的证据是可定位的负值例子。该例子也不提供 sensor/shape 重排下的通用标量符号定理。

## 已封 M2 的证据边界

仅使用已验收 `PUBLIC_AUDIT.json`，没有重新扫描 RAW。其 SHA 为 `5146cc636db256c1138090e23e7801cca38a522fa1b46c8390315309656017ad`。

首 TASK 点位于 `POST_STEP / tick 3597 / view 0 / filter 2 / buffer 4`，标量 `−1.9239716529846191`，法向量约 `[0.11714462, 0.99311489, 0.0000133214]`。其有符号乘积与 pair 聚合诊断相容，整对的差范数为 `2.2308364×10⁻⁸`。约 1.924 的量级不是接近零的舍入量；但标量乘积与矩阵共同出自同一个后端，它们相符只证明表示一致，不能独立证明正确方向、SI 标度、重力平衡或外力完整性。

旧 M1 的被丢弃值不能由 M2 追溯填入。旧 M1 RED 和 M2 依据旧约定得到的 `INVALID_NEGATIVE_NORMAL_SCALAR` 均保持封存。M2 通过的是选中原值与 censor 完整性，完整任务及 strict hold 没有评分，训练准入为 0。

## 新实验优先级与决定性反证

1. **无接触自由落体**：核对实际重力、禁用标志、加速度与 net normal≈0。若身体没有接触却表现为 `a≈0`，或有不明 external wrench，停止力学资格判断；不要把不明约束当作零。
2. **两个 dynamic bodies 叠放**：顶块 A 的唯一接触对象是底块 B，底块落在地面。两块都能成为传感器，避免假定静态地面支持 reciprocal sensor。顶块应有 `F_B→A≈−m_A g`，反向 pair 应相反。ground 是 B 的额外 filter，不能混进 A/B reciprocal 比较。
3. **同一时刻配对 getter dt**：原生时间和 callback 不变时，比较 impulse 查询 `dt=1` 与 force 查询 `dt=1/240`；对标量、pair matrix、net normal 与 friction 各自比较，立即克隆选中范围。任何额外除 dt 会出现明确倍率错误。
4. **整体旋转夹具及重力**：把支持方向从 +Z 转到 +X。若输出仍停在旧 Z 轴、而实际 gravity/pose 已转动，拒绝 world-frame 解释。原生场景中的实际 getter值决定预期，不用配置默认值代替。
5. **创建顺序与质量分别单因素改变**：前者保持名称、物理设置与质量不变，只反转创建顺序，并记录实际 header/shape 顺序；后者保持创建顺序不变，验证线性质量标度。若创建顺序变化没有改变 backend 顺序，该机制检验仍不确定。不得将质量与顺序合并后归因；词典序改名留给后续独立协议。

`CALIBRATION_PLAN.json` 提出新的至多 5 个 epoch，core 为前 4 个，质量变化为第 5 个。所有窗口、阈值、模型对照和停止规则均在结果前规定；目前只是 proposal，不延长已封 M0/M1/M2 的 cap3，不自动开始新采集。

每个 episode 使用预先规定的末尾 49 点，时间跨度 0.2 秒，不在结果中搜索最好的窗口。低速度与近静态门禁只用于叠放、旋转、顺序和质量场景；自由落体应满足 `a≈g`，不能同时要求线性加速度近零。C0 为 120 步，C1–C4 各 1049 步；core 总步数 3267，最多 4316。资源提案为每例 300 秒 child wait、最多 30 秒终止等待和单独报告的清理时间；这是未来方案，没有已发生的资源消耗。

即使新夹具通过，也只支持该 SDK/后端/单位设置/fixture 的接触方向与数值单位。机器人场景中实际 kinematic/drive/joint/外力覆盖、真机单位与独立物理终点还需分别验证，不能把夹具资格迁移成 SafeLab 完整受力资格。

## 来源日期

核对日期：**2026-10-14 UTC**。在线来源有明确版本目录（Isaac Sim 5.1.0、Omni Physics 107.3、PhysX 5.1.0），页面未给出可确认的发布日，不将抓取日期写作发布日期。本轮恰好使用 4 条搜索 query，最终只依据 3 个 NVIDIA 一手文档页和本机哈希固定源码；未引用论坛或二手回答。
