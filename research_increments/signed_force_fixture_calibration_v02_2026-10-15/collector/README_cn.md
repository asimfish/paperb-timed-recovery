# 条件力夹具 v02：有因果依据的退出候选

状态：CPU regression 已验证，native 尚未执行；不能称 FIXED 或 force PASS。

原 force batch v01 的 C0 已完成记录却 300 s 超时退出 -15，其余四项保留 NOT_EXECUTED。单独关闭诊断也以默认 app.close 复现同一生命周期失败；独立 boundary audit 的 11 个重复 owned stack 均定位 SimulationApp.close 的 USD stageclose → IsaacLab STOP 回调 while not timeline.is_playing:render。关闭前 Replicator 实际 STOPPED、队列0/触发器空，END/RESULT fsync 已完成，因此有依据选取本 narrow candidate。

唯一候选修改：完整 END+RESULT fsync 后，确认 public SimulationContext.instance() is 本 probe sim，然后调用既有公共 SimulationContext.clear_instance()。安装源码会 unsubscribe own STOP callback并清本 context callbacks/singleton。随后保持默认 app.close() 零参数。没有 task中清回调、改阈值/等待/skipcleanup/SDK patch，没有其它算法变化。

CPU regression 抽取并验证安装源码的真实 handler、lab clear_instance、base clear_instance、clear_all_callbacks AST，放在有界 fake STOP seam：不 clear 进入 render trap 得到 RED；调用实际公共 clear 的 AST 后 owned subscription unsubscribe、handlerNone、singletonNone、所有 own callback字典空，stageSTOP不再进入 loop 得到 GREEN。不是实际 Carb/USD/framework shutdown，不能替代 native counterfactual。初始 helper metadata 路径错误的 CPU ERROR 记录也保留，修正仅 CPU helper source/flatten路径选择，没有改 candidate cleanup或数值。

新 batch 在任何结果前冻结全部五个不同 v02 case，fixture_reference_case_id 指向原 v01。所有质量/重力/旋转/创建顺序/dt/步数/49点窗口/力与低运动阈值逐项与原 protocol 相等；C4 质量对照不是按结果选择。明确预算：v02上限5 + closedv01实际1 = calibration family上限6；独立 shutdown诊断1、旧 M0/M1/M2 cap3 单独记账。没有第六隐含 v02 epoch，也不重跑旧 case 或重新打开旧 batch。

关闭标记为 AFTER_RESULT_FSYNC → BEFORE_CLEAR_INSTANCE → AFTER_CLEAR_INSTANCE → BEFORE_APP_CLOSE → AFTER_APP_CLOSE。clear 后不再取 physics getter/native time，只存 cached_pre_clear_clock 并明确不是 fresh，以及 Python callback计数、public singletonNone与ownstophandleNone。取消订阅后的计数不证明 backend永不再走physics；force计时资格只来自完整受控 RAW/END，在 release 前封存。15秒重复 ownedstderr 堆栈保留用于候选仍失败时定位。

源、schema、installed API、外部完整 header、独立 reader与ROOT admission全部先冻结；actual native由 root 独占。每 case wait300s、termination30s，ownedPG清理独立观察，不操作其它PID/驱动。失败保留、不按结果重试。科学资格仅允许独立固定reader评价条件夹具 signed/dt/frame/mass，不授全机器人load/unload/torque、S/F/R、硬件或化学成功。

Root review status `PASS_PROSPECTIVE_SIGNED_FORCE_CALIBRATION_V02_SOURCE_REVIEW`；admission status `ADMITTED_ONE_SIGNED_FORCE_FIXTURE_CALIBRATION_V02_CASE`，绑定 source_release/source_review/reader SHA、case、GPU、maximum_new_distinct_native_epochs=5、closed_old_family_cap=3、closed_force_v01_actual_epochs=1、calibration_family_cumulative_upper_bound=6、separate_shutdown_diagnostic_actual_epochs=1、300+30、execution_gate.expected_header 生成的完整外部 header。

```sh
python3 -B /data/liyufeng/paperb_signed_force_calibration_20261015_v2/run_worker.py --case cal_force_c0_freefall_v02 --gpu-uuid GPU-... --verify-only
python3 -B /data/liyufeng/paperb_signed_force_calibration_20261015_v2/run_worker.py --case cal_force_c0_freefall_v02 --gpu-uuid GPU-... --execute --source-review /abs/SOURCE_REVIEW.json --reader-freeze /abs/SOURCE_FREEZE.json --admission /abs/ROOT_ADMISSION.json
```

作者 native/GPU/SDK import=0。完成 counterfactual 正常原生关闭之前，候选只叫 CPU_PASS_NATIVE_UNVERIFIED。
