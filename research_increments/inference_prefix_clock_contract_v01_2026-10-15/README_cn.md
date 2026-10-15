# Inference start 与当前 submit 的两个时域

这是一个小的纯 CPU 数据组件，不执行模型、SDK、physics step、driver、图像生成或 S/F/R 准入，也尚未接入真实异步 simulation。它绑定 sealed G1 v02 source release，同时要求外部独立给出的完整 header SHA，不能由待验输入自己决定 header。

1. **start**：冻结调用者已经捕获且已公开交付的有限 packet prefix。policy input 的 observation/proprioception/ledger 每项都必须绑定 prefix 内真实 packet 的 feature 原件，不能填一个重建值。数据序列化为不可变 bytes，实际捕获 binary bytes 若由调用者提供也复制并核对 descriptor SHA；不生成图像，未提供 bytes 的 asset reference 不宣称已完成字节验证。teacher private inputs 独立储存并 hash，不进入 student public prefix/model input。
2. **complete**：同一个 ticket 必须关联原 snapshot SHA 和原 prefix；只额外记录返回时实际调用者的 current native/deadline clock 和 wall monotonic clock。模型 output 是 8×9 chunk，不能 flatten 成 G1 不支持的 72D 单 command。迟到、unsafe 与 actor takeover 都保留为事实，不能改原 input，也不会产生 executed/success 标签。
3. **guard_submit**：再取得真正 submit 时 current execution state，不能用 start 或 return 的旧安全状态。deadline、lawful、absorbing failure 和 ownership 都以当前值检查；SAFE_LOCAL_RECOVERY/SAFETY_ABORT 还要求逐 9D target 的 trusted current-state authorization。每 slot 保留原 desired tick、tail/stale 原因、原 owner；不自动平移计划时间，不伪造零 target，不把未提交/未 APPLIED 的尾部当成功。

每个 receipt/event 都明确实际 submission/APPLIED 为 false。eligible_by_current_guard 只表达有限数据契约资格，不证明真实动作已获硬件授权或已执行。已记录 original full failure 不允许在之后清空；UNKNOWN safety abort 不制造 FALSE 或 R 标签。跨 native epoch/attempt/original deadline clock 的 subtraction 拒绝。单进程 trusted-caller 元数据契约，不是不可信进程隔离或物理时间真实性证明。

## 已复现的 G1 边界

`reproduce_g1_async_boundary.py` 使用封存 G1 的 public API 和明确 CPU synthetic fixtures。start prefix 的 as_of_time=100，返回状态 time=140：

- 原 prefix 直接用于当前 PROPOSAL：实际退出 2，PUBLIC_PREFIX_BINDING_MISMATCH（RED）。
- 当前收到 TEACHER_TARGET 监督：现有 public API 保留 student visit 的原 prefix=100，记录 target arrival=140（GREEN，仅监督，不是执行）。

原因是当前 G1 PROPOSAL 按 current state.time_ns 重建含 as_of_time 的 prefix。改写原 prefix 到 return time 会失去实际 input identity。这个组件没有修改 G1 来绕过该限制，action adapter 保持 **NOT_INTEGRATED_G1_ASYNC_PROPOSAL_SCHEMA**。未来需要单独版本的 G1 event schema 显式接受 inference-start binding 与 current submission state；真实 free-running physics/model adapter 也仍未接入。

## CPU 验收范围

测试涵盖跨多个 tick、deadline 后返回、unsafe current state、start refs 后续变动、future observation、prefix 篡改、student/teacher owner、teacher private isolation、8×9 stale/tail/flat72/nonfinite、current safety authorization、absorbing original failure。资产示例仅 ASCII CPU_SYNTHETIC_NOT_RGB bytes；没有真实图像、native rollout 或模型 checkpoint。

测试文件对真实 27-member parent source gate 验证一次，随后仅 mock 这项昂贵的 immutable 文件门槛，clock/input/guard 代码照实运行。public-API RED/GREEN reproduction 另实读 parent/v04 gates。初次 full-header fixture 的 V04 SHA 拼写错误导致 13 个 ERROR；日志保留，修正仅 fixture SHA，没有放松组件 parent-pin 门槛，不计作有效负测试或 native 结果。

组件 API 示例见 tests，三阶段调用为 start(...) → complete(...) → guard_submit(...)。下一步是独立 source review 与版本化 G1/native adapter；本 increment 不发布网页、不训练模型、不接入仿真、不改任何旧源。
