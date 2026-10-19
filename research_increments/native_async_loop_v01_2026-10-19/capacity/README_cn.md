# AsyncBridge v0.2：字节级容量预留（2026-10-19）

v0.1（`d044729…`，已封存不改）只预留事件条数、事件类别条数和命令条数，没有预留未来日志字节。独立 reader 的反例：5,360 B 总字节上限下，v0.1 在 5,260 B 处接纳了一个推理 ticket，随后 CASE_END 因 `JOURNAL_TOTAL_BYTE_CAPACITY_REFUSED` 写不进去，案例无法合法结束。本目录 `retained_v01_red/byte_closure_rerun/` 在今天用原 v0.1 源码重新复现了这个失败（结果与 10-16 记录逐项一致）。

## v0.2 的保证

> **审查后更正（2026-10-19）：** 原文写的是所有保留事件都“一定写得进去”，这说得过头了。独立审查 T3 发现：槽位处置还受用途前提约束。例如 SAFE_LOCAL_RECOVERY 需要已知失败，而记录失败本身是普通事件，可能因容量被拒。这时 8 个槽位只能在 CASE_END 中被显式删失。v0.1 同样如此。下面是更正后的表述。

构造成功之后：
- **CASE_END 一定写得进去**，这是唯一无条件的关闭保证；
- 每个已接纳 ticket 的 INFERENCE_RETURN、8 条 SLOT_DISPOSITION、每条已提交命令的 CHANNEL_RESULT，以及剩余的 CAPACITY_REFUSAL 回执，都已预留字节和条数，不会因容量被拒；
- 不过，槽位处置仍要满足各自用途的语义前提（已知失败、当前授权等）。前提不满足的槽位保持未解决，并在 CASE_END 中被显式删失。

实现方式：

1. **有界字段。** 能进入上述保留事件的字符串都必须是可打印 ASCII token（不含引号和反斜杠，长度 ≤ `caps.max_token_chars`）。整数 ≤ 2^63−1，目标值中的整数 |v| ≤ 2^53，浮点数有限。这样 canonical JSON 的长度有确定上界。v0.1 中 STALE/PADDING 等早退分支不校验 authorization，可以塞进任意大的对象；v0.2 对所有分支都校验其形状，ORIGINAL_GOAL 一律要求为 null。
2. **按类别的最坏行长。** `line_bounds(header)` 用最坏取值（64 字符 token、20 位整数、24 字符浮点）构造各保留类别的事件并取 canonical 长度。CASE_END 的上界为 `base + open_tickets × per_ticket`。
3. **接纳不变量。** 每条事件接受后都要满足 `journal_bytes + byte_reserve(state) ≤ caps.journal_bytes`。普通事件若会占用预留空间，在写盘前就被拒绝（`BYTE_RESERVATION_REFUSED`），状态和文件均不变。保留事件消耗的预留至少等于其行长，所以不会被拒绝。CASE_BEGIN 也先完成预留检查再创建文件。
4. **允许无状态结束。** 若第一个 OBSERVED_STATE 就因容量被拒，refusal 回执和 CASE_END 可以在 clock = null 的情况下写入。
5. **只读回放同样执行字节门。** `replay()` 用相同的 `_byte_gate` 逐行重算预留。绕过门写出的日志会在违约的那一行被拒绝（有测试）。

## 实测证据（服务器 Python 3.10）

- v0.1 作者测试 41 项移植到 v0.2 后全部通过（只改了 mode 拒绝码的名称）：`results/author_ported_v01_tests.log`。
- 新增容量测试 16 项全部通过，耗时 202 s：`results/capacity_tests.log`。包括：
  - 普通值与最坏值场景下，每个起约束作用的普通步骤做 cap−1 / cap 的正负一字节测试；
  - 两种模式的粗扫；
  - 最坏行长不超过上界，且字段集合与真实事件一致；
  - 普通事件不能占用预留空间；
  - 三个 ticket 并存（未返回 / 8 槽未处置 / 有待执行命令）时在精确上限下结束；
  - 第一个状态就被拒时仍可结束；
  - refusal 用尽；
  - 行长上限对并发 ticket 数的约束；
  - 回放拒绝伪造日志；
  - token 与整数边界；
  - 保留事件持久化失败时进入 BROKEN、不重发。
- 原反例序列（state → packet → 一个 8 槽 start → close）在 v0.2 下的结果见 `results/V02_CAPACITY_RESULT.json`：
  - 5,360 B 时在 CASE_BEGIN 处拒绝，因为 8 条 refusal 回执和最坏 CASE_END 在开始时就已预留；
  - start 的最小接纳上限为 43,124 B；
  - 43,123 B 时 start 被拒但案例正常结束，43,124 B 时 start 被接纳并正常结束；
  - 以 7 B 为步长扫描 6,189 个上限，没有出现已接纳却无法结束的案例。
- 代价：`max_token_chars = 64` 时，一个打开的 ticket 约预留 35 KB。可以调低 token 上限来减少预留。

## 未覆盖

- 只覆盖字节和条数的接纳。fsync 结果不确定等持久化故障仍按 v0.1 规则进入 BROKEN，不承诺任意磁盘故障下都能结束。
- 仍只允许单一可信 owner，不支持并发写者。新增的 `NATIVE_SIM` mode 只是允许仿真 owner 使用该组件，并不表示这个组件本身证明了任何物理效果。
- 独立 reviewer 的对抗审查结果单独记录，见 `independent_review/`。
