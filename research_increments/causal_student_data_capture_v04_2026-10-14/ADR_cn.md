# ADR: 恢复标签的已知证据前缀

采用新0.4显式schema；0.2/0.3不能静默升级。原目录immutable，历史检查不改。

| 选择 | 判断 |
|---|---|
| 把audit onset当作证据到达时间 | 物理发生与独立审计到达不同，拒绝 |
| 保持早label却把晚audit称retroactive既已verified | 没有独立retroactive标签类型，违反现有prefix合同，拒绝 |
| 以label自身time_ns+seq检查anchor已知；晚audit后新出具label | 采用 |

known verified恢复须每个original anchor已在labelprefix；UNKNOWN未来anchor明确保留UNKNOWN，不读取未来onset。这里不要求audit早于policy decision，特权监督合法。原执行失败须EXECUTION_OUTCOME。成功执行证据检查共用globalTRUE与verified recoveredTRUE，required controls已actual submit+APPLIED，optional masks as-of。

生产入训/native/GPU/θ0只陈述证据状态。真实collector/全任务referee接入与独立原件复核仍未完成。本增量不添加审批要求或追溯改旧row。
