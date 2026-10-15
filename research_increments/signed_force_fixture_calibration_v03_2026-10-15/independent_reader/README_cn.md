# V03 独立前瞻验收器

本副本只验收受控仿真夹具的接触表示、getter 的 dt、世界坐标和固定 49 点窗口。它不证明真机 SI 校准、机器人承载、化学成功、S/F/R 或训练准入。V01、V02 及关闭诊断的封存源、报告、失败和未执行项均不修改。

唯一新增测量行为是调用 SimulationContext 构造后、reset 前设置当前 worker 的 `/physics/disableContactProcessing`。六案按 ROOT 的结果前选择固定：先关闭接触处理的 C1 阴性测量对照，再开启处理的 C0..C4。原五案的几何、材质、过滤器、质量、重力、dt、控制步数、窗口和物理阈值保持。独立 `independent_math.py` 与清理模块逐字继承 V02，非 main 的读回/物理/跨案方法仅更新 case 与 epoch 标识。

独立检查实际设置读回：安装后的值以及 HEADER、BEGIN、每一条受控 RAW 和 END 必须为实际 OBSERVED 的 builtin bool，等于案例预声明值。每次读回前后 native clock 必须相同。设置前实际值允许 False 或 UNKNOWN，绝不根据 Python 构造器推断旧 V02 的实际开关为 True。设置读回通过本身不是力学通过。

阴性案的角色严格为 `NEGATIVE_PROCESSING_DISABLED_CONTROL`。若零接触力使原 mg 判据在全部 49 点失败，仍报告 `FAIL_CONDITIONAL_FIXTURE_MEASUREMENT`，并分类 `EXPECTED_ALL49_MG_FAILURE_RETAINED`。它不是学习方法失败，也不计为正向夹具通过。意外通过同样保留原物理状态，并用 `NEGATIVE_CONTROL_NOT_POSITIVE_QUALIFICATION` 排除正向准入。C3 的完整 backend shape order 无公开 getter，机制仍 INCONCLUSIVE；C4 与同源 C1 做质量倍增比较。缺失或未通过 C1 时跨案为 UNKNOWN，不补造基线。

运行只接受 ROOT 终态通知请求 `/3`、外部 request SHA 和 reader freeze SHA。12 个输入均需外部摘要绑定，新增 `CONTACT_PROCESSING_INSTALL_BEFORE_RESET.json`；源/API、ROOT 选择、准入和 review 验证在物理计分前完成。完整 49 点 finite 窗口即使物理 RED 也输出绑定诊断 series；源、读回、结构、时间或生命周期拒绝时不输出 series。

延续清理的结果前约定：END/RESULT fsync 后才释放本 worker 的 public SimulationContext，确认 singleton None、own stop handle None；之后不再调用物理 getter。default app.close() 零参数。SDK fast_shutdown 的正常 exit0 可以不回到 Python；完整 preclose/readonly-return markers、exit0、无超时和 owned group empty 可验收测量，但 Python 返回及释放后 fresh native time 必须 UNKNOWN，不能补造 AFTER_APP_CLOSE。

预算：原 V01 实际 1 案、V02 实际 2 案已关闭，新 V03 最多 6 个独立 epoch，总校准族上限 9、5365 个新受控步。旧 V01 其余 4 案和 V02 其余 3 案保持 NOT_EXECUTED；关闭诊断 1 案、旧 M 族 3 案分别计。300 秒 worker + 30 秒回收不变。不开 GPU、SDK、native，不读未通知实际输出。ROOT 每案运行冻结 reader 一次；不能根据实际 RED 改 reader。

CPU probes 的素材均显式合成，不是 native 数据。首轮完整阴性 fixture 测试先暴露 tuple epoch 未更新，次轮暴露 boundary snapshot 摘要未重算；两份错误日志保留，只修合成 fixture，不降低 reader 拒绝规则。最终日志和摘要在 reports/；源审查验证 NAS/private 28 件、API 22 件、source ZIP 29 件 CRC、ROOT 六案以及原数值一致。
