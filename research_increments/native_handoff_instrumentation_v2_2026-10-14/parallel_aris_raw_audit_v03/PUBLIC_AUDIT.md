同一已见开发单例 dev_seen_handoff_instrumentation_002_aris 的完整 RAW 门通过。采集由已运行的另一分支执行，本 root 在 child 启动前取消重复采集。真实证据包括14,007 task RAW、28,016物理快照、13,995次提交与13,995次实际应用、12 tail ticks、177组JPEG/depth、168 video frames、176个合法未来提交配对及1个无后续提交的终态capture。全部14,007个POST_STEP位置与xyzw→wxyz重排逐值匹配原RAW；1,200 warmup与30 matched transient计入总15,237真实原生步。

最初盲读器因整event字典错误比较保留FAIL，第一次结果后schema修复又因二维depth误读保留FAIL；两份红结果均未改。第二次结果后修复严格验证冻结producer语义字段和SDK声明的400×640×1 float32原形状，18个事件与12个depth CPU回归通过后冻结新版本，再重读同一420个字节摘要一致的文件，取得本次PASS。此次PASS具有结果后读器修复资格，不能称为前瞻性新独立读器；未调时序/事件/物理阈值，未重积分。

实测mass为0.13500000536441803 kg，scene gravity为[0,0,-9.8100004196167]。全部28,016行的12类安装getter均OBSERVED，getter missing为0；gravity_disabled与simulation_disabled为观测FALSE。instantaneous/permanent composer active均FALSE，所记录force/torque buffer均零。backend kinematic、完整constraints、signed-contact load、机器人卸载和独立承重仍UNKNOWN；观测FALSE与UNKNOWN分别保留。

旧固定技能mechanism和declared sampled joint timing通过。strict sampled hold为FALSE，缺样索引8028..8038共11，strict为0/1、joint_with_hold为FALSE；旧全mechanical gate仍FALSE（not_diagnostic为FALSE）。承重UNKNOWN，训练准入、θ更新、reward/DPsuccess/OPD、chemical success均0，图像仅OFFLINE_CAPTURE。

worker真实wall为414.9332901739981秒，allocated GPU wall upper bound为0.11525924727055503小时；它不是实测GPU利用率。700秒是child wait deadline，另有最多30秒termination与实际startup/cleanup，无严格总700秒承诺。worker exit0、未timeout、所属进程组已清空；本审计未启动GPU/物理。原ROI/13视频和旧16例strict0/16、所有旧角色与结果保持保全。
