# V02 力校准前瞻独立 reader

继承已封存 V01 reader 的 signed force、Newton/mg、reciprocal、world rotation、三 getter dt、每 selected scalar/vector、fixed all49、low-motion/freefall、source/RAW/header/clock/readback/unused-capacity 判据。`code/independent_math.py` 与 V01 byteexact；不改变物理误差门槛、不选择新窗口、不改负号、不重写旧失败。

本批唯一运行身份为 C0…C4 后缀 v02，source 的 fixture_reference_case_id 指向 V01 定义，全部五案例在结果前选择。V02 最多 5 个新 epoch，加已关闭 V01 的一个 C0 failed epoch，force-fixture family cumulative upper bound 是 6。V01 其余四案保持 NOT_EXECUTED；独立 shutdown diagnostic 1 和 closed M0/M1/M2 family 3 分开统计。不同 family 的失败不会被删除。

唯一实现变化发生在完整 measurement END 与 RESULT fsync 后：确认 public `SimulationContext.instance() is own sim`，调用 public `SimulationContext.clear_instance()`，再保持默认 `app.close()` 零参数。它先解除本 probe 的 STOP subscription，再调用 parent clear；source/CPU evidence 只说明这是因果修复候选，native 未验证前不称 FIXED。Reader 增加 `LIFECYCLE.jsonl` gate，检查 durable hashchain 和 `RESULT_FSYNC → BEFORE_CLEAR → AFTER_CLEAR → BEFORE_APP_CLOSE` 的顺序、public owned identity、actual public instance/stop handle None、实际 Python callback counter及 RESULT byte-size。

解除 callback 后不能用 callback counter 不变证明 backend 未推进，也不能用 pre-clear 缓存作为 fresh clock。AFTER_CLEAR_INSTANCE 起 native clock wrapper 必须 UNKNOWN/null，无 SDK physics readback；after-framework native time 同样 UNKNOWN。Physics qualification 全部依据解除之前已捕获的 original RAW/END/RESULT，后续 cleanup 不删分数或重新读取损毁的 physics handles。默认 framework 若直接退出进程，AFTER_APP_CLOSE 可能不存在；必须保持 worker exit0、无 timeout、owned groupempty，不能编造 function return。

原 complete-backend-constraint inventory、robot load/unload/torque、硬件 SI、化学成功和 S/F/R 准入限制保留。C3 complete shape order 未暴露则机制仍 INCONCLUSIVE，允许独立报告世界力 invariant 的条件性结果。C0 details/pair/friction 未配置为 null，不填零。来源/结构/cleanup 失败不输出可绘图物理序列；物理阈值 RED 但上述 gate 完整时允许保留固定 49 点诊断，由 REPORT SHA 绑定，不能把图当资格。

```bash
python3 -B code/audit_fixture.py \
  --request /absolute/ROOT_TERMINAL_AUDIT_REQUEST.json \
  --request-sha256 ROOT_REQUEST_SHA \
  --reader-freeze-sha256 PROSPECTIVE_READER_FREEZE_SHA \
  --output /new/unique/v02/case/audit
```

request schema `SignedForceFixtureROOTTerminalAuditRequest/2`，authorization `ROOT_TERMINAL_NOTIFICATION_ONE_ACTUAL_READ_PER_CASE`，以及 `case_id`, `reader_freeze_sha256`, `root_admission_sha256`, `source_review_sha256`, `expected_header`, `files`。

`files` 每值 `{path,sha256}`，固定 11 key：`HEADER.json`, `BEGIN.json`, `RAW_POST.jsonl`, `END.json`, `RESULT.json`, `LIFECYCLE.jsonl`, `WORKER_TERMINAL.json`（private logs/case.json）, `SOURCE_RELEASE.json`（private EXECUTION_RELEASE.json）, `INSTALLED_API_PIN.json`, `ROOT_ADMISSION.json`, `SOURCE_REVIEW.json`。C3/C4 `reference` 包含本批 C1-v02 的 `REPORT.json`, `AUDITED_SERIES.json`, `HEADER.json` 相同 pin。C1 未 qualified 时 cross-case UNKNOWN，不调阈值。

reader 在 V02 native 结果前封存，独立标准库实现、不导入 collector/SDK，实际读取必须 ROOT terminal notification，每 case 一个独占 output 目录。旧 V01 和 shutdown reader/source/report 保持原 hash。
