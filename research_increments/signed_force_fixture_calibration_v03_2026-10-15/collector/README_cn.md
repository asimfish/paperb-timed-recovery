# 条件力夹具 v03：接触处理的独立测量候选

状态：SOURCE/CPU候选，native 尚未执行；不称物理 FIXED。v02 已保留 C0 条件自由落体测量通过与 C1 实际 RED。v02 没有捕获 `/physics/disableContactProcessing` 的实际值，因此旧实际 setting 是 UNKNOWN；不能因源码写 True 就补造旧 readback。旧源、报告与未执行案例均不改。

安装源码给出可检验候选：SimulationContext._apply_physics_settings 默认把该 key 设 True，ContactSensor.__init__ 将同 key 设 False。直接 tensor contact view 没有实例化 ContactSensor。这是 CPU contact-report processing 的候选解释，不是已由源码证明的物理根因。

唯一新测量行为：每个新 worker 在 context构造之后/reset之前，用同一公共 carb settings接口，设置 case 绑定的明确 boolean。HEADER、BEGIN、每个受控 POST RAW、END 实读 `get(path)`，只有实际 builtin bool 才 OBSERVED；缺失、非bool、异常均 UNKNOWN，不做bool强制转换、不造False/True。pre-toggle真实值可能不是True，也必须按实际保留。该设置只属于本worker Kit进程，不操作外部GPU驱动。

六案在任何结果前冻结：①与C1几何完全相同的 off-control (disabled=True)，②至⑥ C0..C4正测量(分别disabled=False)。5365受控steps；几何、质量、重力、solver、dt、49窗口、阈值、sensor/filter/frame、default close、terminal-owned-context clear 和300+30全继承v02，不混入frame/path修改。off不是v02同case重试，不是算法负例，也不获得正测量资格；需要独立reader判定其实际setting与测量反事实。

ROOT 已前瞻确认 case顺序/max6，protocol以byte SHA绑定 ROOT_PROSPECTIVE_BATCH_SELECTION.json，并在执行门校验不变。calibrationfamily旧actual3（v01C0失败1+v02两案2）+新max6=上限9；shutdown诊断1、旧Mfamily3单独记账；本turn上限10native/6774steps由ROOT选择记录。保留各旧declaredcap，不暗改旧家族，也没有第七个隐含新case。每worker需24576MiB live GPU门，wait300+termination30、ownedPGcleanup独立观察，不信号外来PID，不放宽判据或结果后retry。

CPU证明仅边界：FakeCarb实际读back/ignoredsetter/nonboolUNKNOWN，SDK两条 exactpinnedAST setter statements 对照，setting安装先于reset与每RAW实读，六案normalize后物理dict与v02逐项相同。继承原12 signedcapture、terminalcleanup exactSDK STOP regression和外部source/header/reader/budget gate tests。没有SDK import/native/GPU或新增物理分。

ROOT source-review status `PASS_PROSPECTIVE_SIGNED_FORCE_CALIBRATION_V03_SOURCE_REVIEW`；admission status `ADMITTED_ONE_SIGNED_FORCE_FIXTURE_CALIBRATION_V03_CASE`。强制 source/source-review/reader SHA、case、GPU、maxnew6、familymax9、closedforcev1=1/v2=2/priorcalibration=3、diag1/M3、300+30及完整expected_header。private flatten root `/data/liyufeng/paperb_signed_force_calibration_20261015_v3`。

```sh
python3 -B /data/liyufeng/paperb_signed_force_calibration_20261015_v3/run_worker.py --case cal_force_c1_stack_processing_off_v03 --gpu-uuid GPU-... --verify-only
python3 -B /data/liyufeng/paperb_signed_force_calibration_20261015_v3/run_worker.py --case cal_force_c1_stack_processing_off_v03 --gpu-uuid GPU-... --execute --source-review /abs/SOURCE_REVIEW.json --reader-freeze /abs/SOURCE_FREEZE.json --admission /abs/ROOT_ADMISSION.json
```

Root独占一次/案执行；source与独立reader必须结果前freeze。G0仅条件夹具，S/F/R、全机器人load/unload/torque、硬件/化学结果与主算法MvsB3仍不能由本候选授予。
