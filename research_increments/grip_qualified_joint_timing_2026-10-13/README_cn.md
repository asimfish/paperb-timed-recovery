# 联合时间合同、原外部事件与共享资源：本轮完整组件交付

本增量扩充两类原生物理实验与四种同信息方法规格。机器人测试为IsaacLab/PhysX，三转子开发族为MuJoCo；两者均不是硬件、独立化学终点或学习VLA结果。全部已有失败、拒绝和证据纠正保留，完整科研验收仍 **MAJOR_OPEN**。

## 当前研究问题与创新边界

化学操作不仅要做对，还可能必须在原事件后的窗口内完成，并持续保持某个状态。当命令在总线排队、物理作用滞后、多个任务争用资源或初次执行失败时，命令ACK、真实effect onset和后续confirmation不是同一个时间。我们以原事件身份、区间时间合同、资源约束及独立物理判据统一定义这类问题。

已有MATTERIX等工作包含等待、时间流程和HSM恢复，已有机器人工作关注推理延迟与异步执行。我们不能声称“首次关注时间”“首次使用agent/harness”或DP→RL→蒸馏流水线本身是创新。目标方法问题仍是：agentic Real–Sim–Real系统能否把**可验证的失败与恢复经验**吸收到单一自适应多任务策略。当前完成的是必要机械组件与可证伪的对照，尚未验证最终学习系统。

## 方法与数学接口

原事件a的时间区间为[l_a,u_a]，真实操作b为[l_b,u_b]。对请求间隔D与容忍eps，保守误差区间为[l_b−u_a−D,u_b−l_a−D]；整个区间落入[−eps,+eps]才pass。分别检查contact、stable release、contact→release gap，并与原机械成功和非refusal合取。事件onset与confirmation分开；有限采样不自动证明连续维持。共享不可抢占资源与有向依赖边独立检查。

经验延迟盒用于插入合法重复位置目标hold和联合调度，不覆盖物理状态、不加速原动作、不用测试接触事件重新校准。场景公开q/v及ACK包与private referee严格隔离。四种后续方法共享公共估计器、1000候选/decision与10000/episode计费、最多4个stop/最多每rotor2次请求：batch、robust HSM+retry、EDF重规划与区间MPC。完整生命周期见[方法规格](controller_design/METHOD_SPECIFICATION.md)；[初始组件可复验包](controller_design/public_initial_controller_component_v3.tar.gz)包含18 CPU测试、32初始计划、已接受未ACK重复提交的红/绿反例与独立guard复核。当前不是四个完整stateful native policy。

## 全16机器人测试

原K800四校准的重载失败和单条K1600资格保持独立分母。随后统一K1600开展四条**全新**质量/惯量倍率0.8/1.2×FIFO0/12校准，全部机械/RAW/preimage准入后冻结经验min/max；测试用质量/惯量倍率0.9/1.1×FIFO0/12×四固定规则，共16条。每方法4条，不删失败/UNKNOWN，±25ms不因结果变化。D/H随mass/FIFO绑定，因此不提供独立factor因果估计；0随机seeds、无统计CI，固定配对率不是总体泛化率。

| 固定规则 | 时间+机械primary | 原机械任务 | strict sampled hold | primary+hold |
|---|---:|---:|---:|---:|
| nominal_prior | 0/4 | 4/4 | 0/4 | 0/4 |
| public_delay_prior | 0/4 | 4/4 | 0/4 | 0/4 |
| calibrated_interval | 4/4 | 4/4 | 0/4 | 0/4 |
| joint_exact_grid | 4/4 | 4/4 | 0/4 | 0/4 |

总体primary TRUE/FALSE/UNKNOWN＝8/2/6：仅nominal两条release明确LATE，其余六条联合为UNKNOWN；先验规则的contact/gap多数INDETERMINATE，不能统称确定物理失败。校准中点与精确网格均4/4，本矩阵未证明网格的额外物理收益。先验gap上界约25.00094–25.00099ms，仅约0.94–0.99µs超边界，来自实际native clock与名义网格累积差；必须保留exact判定，但不能宣传明显gap违约或巨大实际失败效果。

[全部16行CSV](robot_results/ALL16_RESULTS.csv) · [独立全部测试audit](robot_results/TEST_AUDIT.json) · [独立四校准准入](robot_results/CALIBRATION_AUDIT.json) · [范围与成本](robot_results/PUBLIC_SUMMARY.json) · [误差区间图](robot_results/all16_timing_intervals.svg) · [冻结执行源/CPU复验包](execution_design/qualified_joint_timing_execution_design.tar.gz)

接触到复合稳定释放的gap不能解释为全过程夹持，张开后至稳定释放前的双侧负点均保留。strict sampled hold及primary+hold与primary使用同16分母。9DOF K/D/force在前、后、末三时点完整读回；56bodies/9articulations preimage可独立重算，不称逐tick增益遥测或包含隐藏solver state。FIFO只延迟位置目标，重力/guard即时，不是全通信或LLM墙时。校准范围只是4格经验包络，不是真实支持/置信区间。

16测试任务样本224,132，四校准53,732另计；测试约1.170727 allocated GPU小时上界，校准0.301184小时另计。所有owned进程组已清空。启动未通过资源门槛的尝试无native，0episode，拒绝及开销日志保留。

## 四条实际原生视频

图的m0.9/1.1表示原质量倍率，不是kg。固定camera roster为test_m090_d12的四方法，不按结果挑选。各168张原生JPEG、28秒/6fps/640×400；每帧native clock、epoch、JPEG/depth byteSHA及实际capture索引核对，ffprobe/全帧CPU解码与浏览器播放/seek验收。6fps仅展示轨迹，±25ms计分使用240Hz RAW，不从视频估计deadline成功。无插帧或AI图像，非真机、非真实LLM在线录像。有损JPEG不能反推原uncompressed RGB digest。

[视频总收据](test_videos/VIDEO_EXPORT_SUMMARY.json)；四条MP4在各case子目录与GitHub网页对应播放器中。校准曲线和全部16条**预定**计划见[独立于测试结果的校准报告](calibration_and_frozen_plans/four_calibration_and_prospective_plans.tar.gz)，计划不等价于实际成功。

## 场景扩充与有效否证

三转子族包含不可撤销原B角度事件、A-stop首次丢弃、A/C共享bus、C窗口、A上界、A↔C依赖边与B sampled maintenance。1条12s开发例基于已收到公开反馈retry，C在等待69ticks期间继续运动；1201 RAW，非OOD。其命令复积分诊断独立另计。

8个2图×2B占用×2deadline开发见证9608 RAW全部joint通过，并经第三独立packet/状态/条件/预算/精确command reintegration核对。主分母仍8；8 controlled+8 producer replay+8第三复查，共24epoch/28824样本，replay不增加实验分母。使用known public model可从合法q/v历史细化**同一个**B事件，原coarse identity保留；50ms粗盒不是不可约信息下界。

**强batch预先双A冗余已解决全部8格。**这不等价反馈诊断、agentic适应或学习，当前family不支持query/agentic必要性。已见开发配置不能重新称heldout。旧32草案在声明模型/动作域下6/8资源不可达预检完整保留；新32正式四策略评测仍0。强对照必须保留，下一族应事先定义真实不确定性与任务空间变化，不能针对本轮结果删基线或微调阈值制造优势。

[单条开发完整源码/RAW](research_design/development_component/native_development_bundle.tar.gz) · [八见证完整114成员包](research_design/prospective_v2/complete_native_witness_bundle.tar.gz) · [八条见证表](research_design/prospective_v2/WITNESS_TABLE.csv) · [第三独立audit](research_design/independent_prospective_v2_witness_review/PUBLIC_AUDIT.json) · [公开可达性推导](research_design/prospective_v2/TIME_BOX_DERIVATION.json)

## 论文、图与证据纠正

[原生机器人结果补充稿](manuscript/robot_supplement/ROBOT_TIMING_SUPPLEMENT.pdf) · [补充稿源码可复验包](manuscript/robot_supplement/ROBOT_SUPPLEMENT_SOURCE.tar.gz) · [统一故事/背景/数学/实验解释](manuscript/METHOD_EXPANSION_cn.md) · [ICML组件稿](manuscript/COMPONENT_NOTE.pdf) · [源码](manuscript/source/component.tex) · [真实事件与排队时序](figures/physical_event_timeline.svg) · [原始角速度](figures/raw_velocity_traces.svg) · [21采样点停转确认](figures/confirmation_samples.svg)

[旧active读回纠正](independent_audit/LEGACY_ACTIVE_READBACK_CORRECTION_cn.md)：旧四条setup/boundary_state实际含warmup末9DOF K/D/force getter读回。原“完全没有active readback”是metadata overstatement；专门after30/task-start/end快照仍缺，epoch/callback部分是相邻日志关联而非该boundary文件直接字段。旧封存原文、源和结果不修改。本轮前/后/末完整preimage补齐是日志能力改进，不据此追溯改旧分数或证明夹持失败唯一因果。

## 下一研究门槛

1. 四种完整stateful公共控制器：预约ledger、提交/ACK/effect状态分离、候选与请求累计预算、取消/重规划规则、公共信息因果与原anchor不变。先独立反例验收，再freeze/run；初始32计划不能代替这一步。
2. 场景加入事先冻结的未知动力学/时变延迟、分支任务依赖与可恢复失败；独立证明正/负可达性。所有强model/HSM/EDF/MPC与blind redundancy对照保留；开发/校准/任务测试分开，避免看过条件伪装OOD。
3. 验证经验吸收：成功/失败/恢复/独立verifier消融；学生访问状态labeling、offline蒸馏/DAgger/OPD同信息预算；第一次及2/3/5/10次尝试，清空上下文和冻结权重对照。分别记录artifact K、task context M及policy weights θ，不能把代码修正叫模型自我学习。
4. 真实RGB/control/native-clock与独立物理/化学终点采集及Real–Sim–Real校准。没有这些证据前，不声称化学效果、硬件泛化或真实在线LLM deadline保障。

全部原生机器人RAW目前留存在私有执行root，公开的是冻结源码包、逐行结果、hash绑定独立audit和视频；不声称已发布完整可公开重算的机器人数据集。CPU八见证包包含完整RAW可公开重放。

新增权重更新0、真实机器人0、独立化学终点0。完整学术论文的VLA、offline/online RL、OPD和真实反馈吸收尚待完成。
