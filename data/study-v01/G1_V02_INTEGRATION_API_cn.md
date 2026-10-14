实际 API 与未来 collector 挂点

`MixedActorRegistry(header, expected_pins=..., directory=...)` 创建新的只增文件目录。header 具有固定 student/teacher 来源、原 attempt/failure root、原 deadline clock/value、group/split、动作维数和有限 history cap。expected pins 必须由已核验的外部协议／源码清单提供，不能由待验日志自己选择。registry_source_sha256 另对当前模块文件核验。v04 manifest SHA 固定为 be4882960804a9d23fb1b0d633054e3ee85d2d3c0fdec70748f7bba7fddaebdb；每次载入核对该清单的 40 件原文件。

`append(kind, payload)` 的实际输入字段列表见 `SCHEMA_CONTRACT.json`。合法用途如下：

| 顺序／通道 | 实际方法 | 数据要求与结果 |
|---|---|---|
| 实际物理 readback 后 | append OBSERVED_STATE | 原生 tick/time、独立原 deadline clock time、同 episode 状态摘要、lawful flag、collector 来源。跨 epoch 不相减。 |
| 真实公开观测交付点 | append PUBLIC_PACKET | capture/delivery time、合法 v04 features/assets/state digest。晚公开 packet 不能进入较早策略历史；asset bytes 仍由原 v04 reader 独立验证。 |
| 策略决策前 | public_prefix(start, end, decision_time_ns) | 返回有限完整原件摘要及 IDs。bind_M_B3_prefixes(..., observed_state_id=...) 对两臂重新核对实际原件，然后要求严格相同。 |
| 学生实际得到并访问观测 | append STUDENT_VISIT | student actor、当前物理状态 ID、已交付 obs packet ID、精确状态摘要、公开 prefix。教师阶段不能伪造 student visit。 |
| 调度器实际转换主体时 | append ACTOR_TRANSITION | 从实际当前 actor 转到 teacher/student，使用最新同 episode 物理 tick；已接受 FIFO 不清空。 |
| 策略确实产生动作候选时 | append PROPOSAL | actor、物理状态、公开 prefix、有限目标。仅证明候选存在；不产生 executed target。 |
| 独立教师响应到达时 | append TEACHER_TARGET | student visit ID、精确 pinned teacher 来源、有限 target、单独 private input。它继承学生原 visit 的公开历史，而非教师未来上下文。 |
| middleware 实际接受 command 时 | append SUBMITTED | driver 原 command/proposal IDs、当时 actor、ready tick 与完全匹配的 target/channel 来源。存下 owner/source；不能接管后把旧学生 proposal 改属教师。 |
| channel 真正执行／拒绝／丢弃时 | append CHANNEL_RESULT | APPLIED/REJECTED/DROPPED 与实际观察状态、原 owner、同 target；APPLIED 不意味着物理 effect 完成。 |
| 独立审计到达时 | append VERIFICATION | 单独审计 artifact/source、执行标签 scope、三值、原 clock 上的 effect bracket、明确控制 IDs、力学与机制资格。F 另绑定实际失败 student state 摘要及教师纠正 ID。 |
| 已核验全任务失败 | append FULL_TASK_FAILURE | 独立源、原 failure root、当前观察状态；其全任务 FALSE 不因恢复／reset 擦除。 |
| 确实另开尝试 | append RESET | 新 attempt/epoch、原 failure/deadline/split 完整不变。未处理的已接受 command 会使 reset 被拒绝；不可伪造 application/cancellation。 |

独立准入：

1. `admit_behavior_target(command_id, as_of_seq=...)` 要求标签 prefix 内已经实际 APPLIED。UNKNOWN force 不影响这种行为监督；返回 success/recovery false 和真实 owner。
2. `admit_teacher_target(target_id, as_of_seq=...)` 要求 prefix 中已到达的教师目标及实际 student visit。这是监督纠正，返回 execution_evidence false、actual_OPD_update false；不能宣称该目标已成功执行。
3. `admit_verified_label(label_id, as_of_seq=...)` 对 S/F/R 分别检查执行类型、已 APPLIED 关联控制、三值和原 deadline。S/R 缺 qualified force 或机制就拒绝；F 要真实学生执行与已核验失败状态，target 仍是教师合法纠正，不能模仿失败动作。原早标签不利用后来的 audit 或 application 自动升级；应写一个新的晚标签。

`public_export()` 仅返回当前 attempt 的已交付公开 packet。`close()` 保留 pending IDs，冻结 writer。`readback(directory, expected_pins=...)` 校验 hash chain 并重放每条规则；对 teacher/source/owner/epoch 等重新派生值逐件一致。

此旁路目前没有修改 v04 logger。未来接入时，v04 的单 actor header 需按真实 actor 段分别建新日志或明示纯观测段；不能把 teacher 段塞进 STUDENT header。旁路 journal 将段、访问、proposal、driver command IDs 与真实 owner 连起来。旧 ARIS/M0/M1/M2日志不补写、不伪造交付、学生访问或教师调用。

当前采用单进程、单 writer、顺序调用。它不是对不可信程序的隔离器；同进程调用者可伪造元数据或修改对象。source pin、hash 与 replay 证明的是已声明数据契约，真实 physical/force/complete-task 事实必须由可信采集器、独立 RAW reader 和 verifier 另行审查。超出有限 history/event cap 应另开前瞻版本，不能静默截掉 B3 历史或删除失败分母。

v02 替换 v01 的 deadline/safety 挂点（本节为当前规范）

Header schema 改为 PaperBMixedActorRegistryHeader/0.2；pins 新增 safety_authorizer_source_sha256，必须和外部 expected pins 一致。ACTOR_TRANSITION 新增 operation_purpose，仅记录行政转移；最新 unsafe 观察也可登记转移，并不授权控制。STUDENT_VISIT 同样是 readonly 实际访问，可记录 unsafe 或 post-D 失败。

PROPOSAL 和 SUBMITTED 必填 operation_purpose 与 safety_authorization。ORIGINAL_GOAL 的 authorization 必须 null；其当前 state 必须 lawful、原 goal deadline 未过、无吸收的已知 full FALSE。SAFE_LOCAL_RECOVERY 和 SAFETY_ABORT 的 authorization 是精确字段字典：source_sha256、artifact_sha256、observed_state_id、operation_purpose、target_sha256、verdict=LAWFUL_TARGET_AUTHORIZED。许可 source 绑定 trusted harness；target SHA 绑定实际有限目标；state ID 绑定当前实际 readback。每次实际 submit 再取得/核验当前状态许可，不用旧 proposal 许可代替它。source/artifact 对应的真正 authorizer 程序与结果原件仍需独立审查，不能 controller 自填。

SAFE_LOCAL_RECOVERY 要有已验证原 failure，post-D 还要独立已知原 full FALSE；SAFETY_ABORT 不要求将 UNKNOWN 变成 FALSE。两个 purpose 可以从 unsafe state 开始，但必须有逐动作 trusted 许可，保持 observed lawful=False 原值。owner 与 purpose 在 submit 冻结，并贯穿实际 APPLIED，即使其间发生 teacher takeover/student return。

verified-label 分流：F 可以 effect>D，但不缺实际失败访问/学生执行/独立 FALSE/教师合法纠正；S 的物理 effect 必须≤原 D、≥关联 APPLIED，并无已知吸收 full FALSE，audit 到达晚于 D 不是否决条件。完整成功可以包含 D 内合法的可恢复局部控制，不要求整个任务所有关联命令都是 ORIGINAL_GOAL。R 要独立合格局部恢复、真实 SAFE_LOCAL_RECOVERY 执行，输出 LOCAL_RECOVERY_NOT_FULL_ORIGINAL_SUCCESS；若原 full FALSE 已知，原任务 verdict 保留 FALSE。默认 SAFETY_ABORT 控制仅可作为 APPLIED behavior target，UNKNOWN 止损不能变成 R/S。

所有三值是独立 verifier 的声明输入及有限 source 契约结果，不是登记器从时钟或许可自动证明的物理结果。迟到的完整成功必须使用真实原 clock effect bracket；不能给晚 APPLIED 伪造一个早 effect 来绕过 D。原 full FALSE 不因 local cleanup、actor switch 或 reset 清除。
