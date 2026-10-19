# AsyncBridge v0.2 独立对抗审查与处置（2026-10-19）

审查者为独立 agent，只拿到 v0.1/v0.2 源码的只读副本。它自己编写了不导入被测模块的 reservation reader，以及对抗与 fuzz 脚本（见 `out/`）。原始结论逐字保存在 `REVIEWER_FINAL_REPORT.md`。

## 结论

**字节与条数预留成立：**
- 2,560 次 fuzz 运行、227k 个操作，含 545 个零余量状态；
- 5,835 次最坏内容的 fork-and-drain，共写入 31.5k 个保留事件；
- 没有保留事件因字节或条数被拒，没有拒绝改变过状态或文件，回放结果与实时状态一致；
- 审查者的独立 reader 与模块在 9 个交叉检查日志和 6,699 个 fuzz 日志上全部一致；
- 两套行长上界都没有被任何实际行突破。

**确认的缺陷不在预留算法本身：**

| 编号 | 严重度 | v0.2 问题 | 处置（v0.3，`/data/liyufeng/paperb_async_bridge_v03_20261019_v1`） | 用审查者原脚本对 v0.3 复跑的实测 |
|---|---|---|---|---|
| T1/T1b | 中 | `commit_slot` 用 `==` 比较，接受类型不同但数值相等的 prepared，例如 309 位整数、float 类型的 tick | canonical JSON 往返，比较改为 canonical 字节 | 原复现在 commit 处被拒：`PREPARED_STALE_OR_TAMPERED` |
| T2 | 低-中 | 子类对象导致实时写入与回放结论不一致 | 同上；只保留普通 JSON 类型 | T2a 实时拒绝且回放一致；T2b 中子类被归一为普通 int，下一条 `earliest_apply_tick` 为 1 位整数，偏离原定 tick 的 APPLIED 被拒，回放一致 |
| T5 | 低 | 回放接受 float/bool 类型的 seq 和 float 类型的 clock | 回放要求信封类型精确 | HOLDS，4 种伪造全部被拒 |
| T6 | 低 | 部分畸形输入抛出原生异常 | 全部转为 `BridgeError` | 8 种畸形输入全为 BridgeError，状态与文件不变；“non-BridgeError refusals: none”。审查脚本把含 `:` 的错误码当作原生异常，所以标签仍显示 CONFIRMED_DEFECT |
| T3 | 中（契约文字） | README 声称所有保留事件都“一定写得进去” | 更正文字：CASE_END 是唯一无条件保证，前提不满足的槽位在 CASE_END 中删失 | 行为与 v0.1/v0.2 相同，按更正后的说法成立 |
| T7 | 注记 | token 上限无界，计算上界时内存增长 | v0.3 header 上限 4,096 | 审查脚本直接调用 `line_bounds`，绕过 header 校验，所以仍显示注记 |

复跑方法：审查者脚本不做任何改动，被测模块换成 v0.3。只有一处例外：审查者 reader 中硬编码的事件 schema 常量从 `AsyncCollectorEvent/0.2` 改为 `/0.3`，原文件另存为 `independent_reservation_reader_v02_original.py`。第一次复跑时 reader 仍用 0.2 常量，因此所有 v0.3 日志都在信封处失败；那次输出带 `run1_reader_schema02` 后缀保留，不作为结论使用。

改正常量后的复跑结果：reader 交叉检查 `ALL_AGREE_PASS`；400 s 对抗与 fuzz 中异常为 0；与 v0.1 的差分只有预期的收紧，以及“无状态时也可关闭”这一项。

## 对已有证据的影响

- NA1 原生案例使用 v0.2。它的日志经审查者 reader 检查为 PASS（该 reader 会拦下 T1/T5 类型违规），最小余量为 503,682,637 B。NA1 的 owner 只提交模块自己算出的 prepared，不涉及 T1/T2 的调用方构造。
- v0.2 源码保持封存。v0.3 是后续候选版本，尚未用于原生案例。
