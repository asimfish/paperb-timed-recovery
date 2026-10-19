# AsyncBridge v0.3：独立审查后的类型与回放加固（2026-10-19）

v0.2 的字节预留经独立对抗审查后成立：2,560 次 fuzz 运行，31.5k 个保留事件，没有一个因字节或条数被拒。审查发现的问题集中在类型校验、回放严格性和契约文字。v0.3 只针对这些问题修改；字节预留的算法与 v0.2 相同。NA1 原生案例使用的是 v0.2（`79a5b55…`），v0.2 保持封存不改。

## 修改

| 审查项 | v0.2 问题 | v0.3 处理 |
|---|---|---|
| T1/T1b | `commit_slot` 用 `==` 比较：1、1.0 和 True 相等，超大整数等于浮点数，类型不同的 prepared 会被写入 | 调用方传入的每个 body 先做一次 canonical JSON 往返；结构相等一律改为比较 canonical 字节 |
| T2 | 子类对象（`__eq__` 恒真的 dict、改写运算符的 int）会让实时写入与回放结论不一致 | canonical 往返后只剩普通 JSON 类型；比较不再调用子类的 `__eq__` |
| T5 | 回放接受 float/bool 类型的 `seq` 和 float 类型的 `clock` | 回放要求信封类型精确：`seq` 为 int，`clock` 为 int 列表或 null |
| T6 | NaN、超大整数、列表形式的 status 等会抛出原生异常 | 统一转为 `BridgeError`（`BODY_NOT_CANONICAL_JSON` / `MALFORMED_INPUT:<类型>`），状态与文件不变 |
| T7 | `max_token_chars` 无上限，计算上界时内存随之增长 | 上限设为 4,096 |
| T3 | README 声称所有保留事件都写得进去 | 只更正文字：CASE_END 是唯一无条件的关闭保证；槽位处置还受用途前提约束，前提不满足的槽位在 CASE_END 中被显式删失（已有回归测试覆盖） |

日志 schema 升为 `AsyncCollectorHeader/0.3` 和 `AsyncCollectorEvent/0.3`，与 v0.2 日志区分。

## 证据

- **服务器（Python 3.10）：**
  - v0.1 作者测试 41 项（经 v0.2 移植）：通过；
  - v0.3 回归测试 9 项：通过，逐项对应审查 T1–T7；
  - 字节预留测试 16 项：通过，`results/capacity_tests_run1.log` 用时 212.9 s；同一套件的第二次运行保存在 `capacity_tests.log`。
- **本机（Python 3.12）：** 同样三套测试全部通过，字节预留套件用时 479 s。
- **用审查者原脚本复跑**（`independent_rerun/`）：
  - 只把 reader 的事件 schema 常量改为 0.3，原文件另存；
  - reader 交叉检查 `ALL_AGREE_PASS`；400 s 对抗与 fuzz 中异常为 0；
  - T1 原复现被拒：`PREPARED_STALE_OR_TAMPERED`；
  - T2a 实时拒绝且回放一致；T2b 子类被归一为普通 int，偏离原定 tick 的 APPLIED 被拒；
  - T5 的 4 种伪造全部被拒；T6 全部为 BridgeError，状态与文件不变；
  - 审查脚本中 T1/T2/T6 的标签是硬编码或启发式判定，应以实测字段为准。
- `results/V02_TO_V03.diff` 是相对 v0.2 的完整差异。

## 未覆盖

同 v0.2：单一可信 owner；不承诺磁盘或 fsync 故障下仍能结束；不是形式化证明。审查者的 reader 只核对 `prev_sha256` 链接字符串，不重算哈希。v0.3 尚未用于原生案例。
