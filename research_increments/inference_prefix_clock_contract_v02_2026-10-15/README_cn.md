# 推理时钟契约 v02：接受事件后的时钟不能倒退

这是针对 root 独立审查发现的一项小修复。v01 的 `guard_submit` 只把当前时间与这个 ticket 的返回时间比较；一次更晚的 unsafe guard 已经记录后，再提交介于 return 和该 guard 之间的旧状态，仍会重新获得 eligible slots。原 root 审查与完整 v01 源码在 `inherited_v01/` 原样保留。

v02 给每个 contract 增加最新 **已接受事件** 的执行时钟 highwater：`tick`、`time_ns`、`deadline_time_ns` 三个维度都不能倒退。`start`、`complete`、`guard_submit` 的 execution 数据验证都与这个 highwater 比较；只有事件已完成内容复制、哈希、receipt 复制并追加成功后才提交 highwater。无效 prefix、错误 output、错误 guard、序列化异常和事件容量拒绝不会推进它。

事件可以处于相同的三个时钟值。多个 ticket 可以同时处于待返回状态，后开始的 ticket 可以先返回；日志记录的是真实 arrival 时取得的 current execution clock，因此这种返回顺序不被禁止。原始输入 snapshot、prefix、desired ticks、8×9 chunk、episode tail、actor ownership、teacher private 隔离、absorbing original failure 和 deadline 数值都保持原规则。不重建 input，不移动动作时刻，不把迟到结果变成成功。

## 实际证据

- v01 root 独立审查原件：`inherited_v01/root_review/ROOT_INDEPENDENT_REVIEW.json`，原状态 `SCOPED_SNAPSHOT_CHECKS_PASS_SERIAL_CLOCK_ROLLBACK_OPEN`。
- 先把新的回归断言运行在未经修改的 v01 副本：实际 **FAIL（ValueError not raised）**，日志 `reports/RED_V01_ROLLBACK_REGRESSION.log`。
- 再通过 public API 实读原目录已 pin 的 v01：unsafe late guard 时没有 eligible slots，随后回滚 guard 重新接受 `[2,3,4,5,6]`，实际 exit **2**。完整输入与 receipts 留在 `reports/ACTUAL_V01_RED_PUBLIC_API.json`。
- 同一输入运行 v02：拒绝 `ACCEPTED_EVENT_EXECUTION_CLOCK_ROLLBACK`，事件链不变，实际 exit **0**，记录 `reports/ACTUAL_V02_GREEN_PUBLIC_API.json`。这是针对 root finding 的明确 CPU 等价复现，不声称恢复了 root 未公开的原始输入。
- **24 项 CPU 测试 PASS**：13 项原测试字节不改，11 项新增 clock 回归；逐维回退、等值多事件、重叠 ticket 逆开始顺序返回、失败操作与 1024-event 容量都覆盖。每组先实读 27 件 G1 parent 源码 gate，数据测试仅 mock 这个重复的文件门槛。

最初写测试时工作目录路径拼接错误的日志保留为 `reports/INITIAL_TEST_PATH_ERROR.log`。它是测试准备失败，不计作 RED 或有效测试。

## 可运行命令

从这个 increment 目录运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B code/reproduce_serial_rollback.py --source-version v01
PYTHONDONTWRITEBYTECODE=1 python3 -B code/reproduce_serial_rollback.py --source-version v02
```

v01 reproduction 预期 exit 2，v02 预期 exit 0。它们验证冻结 parent/source/root finding 的 SHA 后使用 public API，不导入 SDK，不执行模型或物理。

## 证据范围

作者 CPU acceptance 已完成，root 独立 source review 待进行。适配器仍为 **NOT_INTEGRATED_G1_ASYNC_PROPOSAL_SCHEMA**；native/model/GPU 调用 **0**，S/F/R 准入 **0**。这不是原生异步运行、物理时钟真实性或动作安全授权证明。

这是单线程、可信调用者的有界 arrival 日志契约。多个 pending ticket 的交错是允许的；组件没有新增线程同步或不可信进程隔离。变化仅修复 accepted execution clock 的提交时点；原件已有的 ticket/return 登记与 absorbing 状态更新语义没有重写，因此不宣称所有失败 API 调用都是全状态事务。`SOURCE_DIFF.patch` 给出最小源码差异，`PARENT_PIN.json` 绑定 v01 freeze、root finding 和 G1 parent；旧目录均未修改。
