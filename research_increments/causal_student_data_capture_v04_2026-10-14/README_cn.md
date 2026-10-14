# Causal student capture 0.4

本增量修复冻结v0.3的恢复用途因果缺口。audit arrival170、物理onset[40,50]、recovery label160时，v0.3在close读取完整audits map，误把恢复资格判为TRUE。已声明prefix语义不包含retroactive审计类型；早onset不能证明审计证据在早label已知。

v0.4的独立anchor必须在label的(native time_ns, global seq)前缀。已知verified值不能借未来anchor；verified UNKNOWN保留UNKNOWN，并不读取未来anchor onset来回填或否定旧label。晚到audit后可新出具label180，合法用于离线监督。audit可以晚于policy decision，只需早于其监督label，保持特权教师BC和audit-only隔离。

邻接修复：verified TRUE且recovered_objective TRUE和全局objective TRUE共用执行证据检查，required控制须已提交且APPLIED；REJECTED/DROPPED/TIMEOUT不能成为已验证恢复成功。原执行失败须EXECUTION_OUTCOME；STATE/PROPOSAL不能充当执行恢复依据。失败RL、UNKNOWN reward不补0、学生实际visit+teacher query的OPD、explicit legacy train和seen非heldout合同保持。

original_v03_snapshot逐字保存原v0.3源、CPU80、收据、196193B archive及其原v0.2历史；original_v02_snapshot为原F1回归依赖，inactive。原v0.2/v0.3目录immutable；旧54/80PASS不是上述缺口的证据。tests保留原80并增加18项恢复回归，独立13 probes和实际writer/readback另留receipt。

运行：PYTHONDONTWRITEBYTECODE=1 python3 code/run_cpu_acceptance.py --output <new-directory> --legacy-root ../stateful_controller_expansion_2026-10-13/learning_data_design

CPU output建议先写本地临时目录再逐字复制，避免NAS fsync拖慢synthetic writer；不改writer持久化语义。所有快照仅源码、synthetic JSON、收据、旧metadata投影，无真实JPEG/native原件。production0/入训0/native0/GPU0/θ0。真实source attestation、sensor有效性和跨chunk full-task仍需独立collector/referee原件，CPU gate不证明化学或机器人成功。
