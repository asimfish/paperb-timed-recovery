# 物理观测最小组件

只对已经初始化的旧 Isaac 场景调用 getter，不创建、重置、推进场景，不更改控制、任务判分或原始标签。此目录不包含任何新 native 数据。纯 CPU 反例使用假 getter，不证明实际 SDK 所有 getter 在该场景均可用。

Root 从 `code/physical_capture.py` 与 `code/physical_validate.py` 复制冻结实现，调用：

```python
capture_snapshot(
    body_view=scene['precursor_1'].root_physx_view,
    simulation_view=scene['precursor_1']._physics_sim_view,
    rigid_object=scene['precursor_1'],
    clock_read=lambda: dict(native_epoch=epochs,
                           time_s=float(sim.current_time),
                           callback_count=callback['count']),
    tick=i, phase='PRE_WRITE', body_path='/World/StationA/precursor_1',
    usd_inventory=initial_or_final_composed_usd_inventory,
)
```

`PRE_WRITE` 必须在 `scene.write_data_to_sim()` 前。`POST_STEP` 必须在 `sim.step()/scene.update()` 后。`TASK_BEGIN` 与 `TASK_END` 是端点读回。每组 getter 前后原生 epoch/time/callback 数完全相同，否则记录错误，不把推进后的读回冒充同时观测。`POST_STEP` 的 instantaneous wrench 可能已清空；只有 `PRE_WRITE` 缓存描述即将施加的该外力输入。两 composer 的值是瓶体 link/body 坐标系力 N、力矩 N m，shape `[1,1,3]`，不是世界坐标系。机械臂重力补偿不能替代瓶体接触承重测量。

| 字段 | 实际已安装方法 | shape / 含义 |
|---|---|---|
| transform_xyz_xyzw | root_physx_view.get_transforms() | `[1,7]`，xyz + **xyzw**，SimulationView subspace 坐标系；已安装 SimulationManager 初始化 subspace roots 为 `/`，新运行仍需绑定该源码且不能随后更改 |
| velocity_world_com_linear_angular | get_velocities() | `[1,6]`，世界坐标系，COM 线速度 m/s、角速度 rad/s |
| acceleration_world_com_linear_angular | get_accelerations() | `[1,6]`，COM 线/角加速度；原文此处沿用 velocity 的 note，保留 SDK 文档边界 |
| mass_kg / inverse_mass_per_kg | get_masses() / get_inv_masses() | `[1,1]`，实际 backend 值；inverse mass 不作为运动学 flag 的替代证明 |
| com_local_xyz_xyzw | get_coms() | `[1,7]`，相对 rigid body prim 的 COM/principal axes pose |
| inertia_com_body_frame_column_major_kg_m2 | get_inertias() | `[1,9]`，COM 处、body prim 坐标、column major |
| gravity_disabled_flag | get_disable_gravities() | `[1,1]`，**1 禁用、0 启用** |
| simulation_disabled_flag | get_disable_simulations() | `[1,1]`，**1 非仿真、0 仿真** |
| scene_gravity_world_m_s2 | simulation_view.get_gravity() | carb.Float3 或 None；None、异常都保留 UNKNOWN，不填零 |
| external_wrench_buffers | instantaneous/permanent_wrench_composer | active + composed_force_as_torch/composed_torque_as_torch，写入前立即复制 |

所有 tensor 立即转为普通 JSON 数值，不保留随下一 getter 更新的 buffer 引用。缺失、异常或非有限值写 UNKNOWN 与原因。record hash 为 `json.dumps(sort_keys=True, allow_nan=False, separators=(',', ':'))` 的 UTF-8 SHA256，排除 `record_sha256` 自身；这与旧 gain snapshot 的编码不是同一契约，不能混用。

新 task 初/末须另外记录 composed USD 的 `physics:kinematicEnabled`、`physics:rigidBodyEnabled`、`physxRigidBody:disableGravity`、轴锁字段、所有 joint body0/body1/enabled 与 collider→rigid-body 祖先关系。USD 是 authored/composed 证据，**不是完整 active backend constraint inventory**。当前安装 tensor API 未找到完整 kinematic flag / 全部外加 constraint getter，组件诚实保持两字段 UNKNOWN。

接触采集器须保留原 `actor0/actor1/collider0/collider1`、callback ordinal/header index/contact index、stage id、normal/impulse/position/separation，摩擦 anchor 保留独立 index/offset。原 contact 与 friction anchor 不相加，不把 normal 标量/总 impulse 混淆。PhysX 文档给 normal 第二 shape 指向第一 shape；Omniverse 绑定具体 actor 顺序、flipped pair、force-on-object 符号与单位转换仍需独立确认，不能仅套用该定义生成承重标签。旧 logger 丢失的 index 信息不能事后凭空恢复。

可选 RigidContactView 新观测：`existing_simulation_view.create_rigid_contact_view(body_root, filters, max_contact_data_count=N)`。这是传感器 view 创建，**本最小 adapter 没有调用**。需正式 preexec review 通过，保存实际 sensor/filter paths 与 counts。`get_contact_data(actual_dt)` 实际返回 6 buffers（其 doc tuple“五项”是 typo）：scalar forces、points、normals、separation、pair counts、starts；`get_friction_data(actual_dt)` 另 4 buffers。只导出 counts/starts 指向的有效项与原 buffer index；保存容量/解析异常/溢出未知，不导出未初始化 buffer 作为有效样本。actor/filter 按 rigid body 选取，pan 是 collider，不保证其 path 可直接当 rigid-body filter；必须保存 ancestor mapping。任何 sign/frame/coverage 未确认，load-bearing 均 UNKNOWN。

一次观察单例不新增承重、卸载或严格保持的成功标签。该组件结构 PASS 只意味着日志形状与 hash 满足契约；实际物理前置缺失仍 UNKNOWN。
