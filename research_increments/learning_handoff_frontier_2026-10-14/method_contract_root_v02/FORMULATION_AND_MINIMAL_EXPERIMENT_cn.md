# Event-time recovery：最小 formulation 与下一阶段预注册

2026-10-14；**方法设计候选v0.2，尚未执行**。本版保留原冻结稿，并修正共同预训练的数据并集预算：θ0固定只用S512，所有最终池包含同一S512。待检验的贡献是：同一共享策略能否把有原事件身份、合法失败状态与独立恢复结果的经验吸收到参数中，在关闭在线教师和跨会话检索后处理新任务合同。不是证明“加时间输入”首次成立，也不是用接口检查替代策略学习。DP已有视觉条件动作扩散；Chronos已明确使用观测capture与期望action execution时间，因此必须保留同时间信息的强对照。[DP](https://arxiv.org/abs/2303.04137)、[Chronos](https://arxiv.org/abs/2610.13929v1)

## 1. 事件、因果历史与恢复

一个尝试为 $a=(id,G,B)$，G含带身份的物理事件、hard/soft约束与允许的恢复分支，B为资源账本。原生物理时间为τ，实际单调墙钟为w；不同epoch不相减。观测k分别记录capture (c_k)、arrival与delivery (d_k)。在线学生历史严格为 $h_t=\{o_k:d_k\preceq t\}$，包含合法RGB/proprioception、已公开且已交付的event packet、合同与已提交控制；私有pose、force verifier、故障标签不进入学生输入。OFFLINE_CAPTURE是另行声明的训练配对模式，不倒称教师或旧学生实际看过图像。全catalogue不能拼成任意时刻输入。

事件e保留onset区间 (I_e=[l_e,u_e])、confirmation、audit arrival与来源，四者不互换。合同分开规定：

| 约束 | 认证与时钟 |
|---|---|
| 绝对deadline D | 事件onset区间整体≤D才TRUE；D锚定本尝试预声明start，不因重试后移 |
| 相对event窗口[L,U] | $I_j-I_e=[l_j-u_e,u_j-l_e]\subseteq[L,U]$才TRUE；原anchor不替换成恢复后的事件 |
| dwell d | 指定谓词按原生时间连续采样保持；N点覆盖(N−1)dt，240Hz下200ms至少49点。缺帧/边界为UNKNOWN；仅认证采样合同 |
| latency | delivery−capture、submit−decision、apply−submit分别测量；APPLIED/ACK不是独立物理effect |

区间确定不相交为FALSE，边界重叠或缺证据为UNKNOWN。策略可使用从已交付证据导出的剩余窗口 ([u_e+L-t,l_e+U-t])、dwell已覆盖跨度和剩余预算，但这是保守条件特征，不是已证明的完整可达集。未来audit不得进入这些特征。

**Hardcatch**：原绝对deadline、不可重锚的窗口或合同要求的严格连续保持已被确定违反，full-task失败吸收；后续安全处置或局部恢复不能清除它。**Recoverable**：例如张开前未取得合格支撑、目标位置未稳定，仍保持合法夹持且原窗口/资源未耗尽，可在同一attempt执行一次reseat并重新累计候选dwell。新dwell候选有新occurrence id，原touch/deadline和失败row不改。缺少可达性或物理证据时标UNKNOWN，不自称“总可恢复”。允许重试的局部目标FALSE可保留，同时最终G按预声明分支判定；不能把hard节点FALSE改TRUE。reset另开attempt，原失败仍在分母。

最小实现是**Event-Time Recovery DP**：TimeDP读取相同public原始事实，并额外使用确定性的prefix残余账本z；输出未来执行时刻上的控制chunk。固定教师在学生实际访问state上查询校正动作；以等量、去重的完整成功S、失败状态教师校正F、已执行且独立验证的恢复tail R训练同一个去噪器：

\[
\mathcal L(\theta)=\mathbb E_{(h,z,U^*)\sim S\cup F\cup R,k,\epsilon}
\|\epsilon-\epsilon_\theta(\alpha_kU^*+\sigma_k\epsilon,k,h,G,z,T^{exec})\|^2.
\]

F提供新的合法教师target，不模仿失败控制；R只监督实际提交、APPLIED且用途合格的动作，mask未知/未提交slot。未经验证的RL reward不填0；本阶段无RL。此机制的候选新意是残余合同与失败/恢复经验共同改变共享参数，若同信息TimeDP+DAgger即可解释结果，则不成立独立算法贡献。

v0.4约束的是 $Y^{prefix}_{\ell}=V(E_{\prec\ell})$：label160不能借audit170声称已verified。离线最终分数 $Y^{final}=V(E_{\le T_{close}})$可使用晚到原件，但在独立score命名空间；不覆盖早label。用于BC时须另出audit后新label/新row id并保持原因果h，不能把最终结果放回过去学生输入。这里的学生state聚合称**DAgger/监督蒸馏**：visit+teacherquery仅证明数据条件，不证明实际OPD更新。GKD的OPD也不逻辑要求RL，但本实验没有教师分布蒸馏/RL实现，不能称“true OPD成果”。[DAgger](https://proceedings.mlr.press/v15/ross11a.html)、[GKD](https://arxiv.org/abs/2306.13649v3)

规则/flow教师若只提供动作sample，可在一致动作域、时间和state配对下做回归/去噪监督；不能虚构teacher log-prob或把一次sample称KL。KL需明确密度或受验证的score-gradient估计器；[OneDP](https://arxiv.org/abs/2410.21257)使用扩散链分布蒸馏。[FA-OPD官方实现](https://github.com/vanzll/FA-OPD)另有PPO reward distillation与flow动作回归两条更新，本阶段没有复现这套算法。

## 2. 两个待证claim与最小对照

C1：在同public反馈、同数据/教师/计算cap下，事件账本和F/R使heldout完整任务成功及合法恢复优于同信息TimeDP+DAgger，而非只减违规或增加拒绝。C2：新参数在online teacher=0、跨会话context/retrieval清空后仍保留改善；当前episode合法历史不清空。首要反解释是计时器、更多信息/预算或学生状态标签本身已解释全部收益。

| 系统 | 对照作用 |
|---|---|
| B0 DP | 无显式时间；同backbone、G、public事实与harness |
| B1 TimeDP | capture与期望execution时间、时序randomization；S-only |
| B2 TimeDP+external timer+harness | 固定强规则调度和允许的reseat分支；同event反馈，不刻意减弱 |
| B3 TimeDP+学生状态DAgger | S/F/R与完整public事件原件均同量；无残余账本z，检验representation的增量 |
| M Event-Time Recovery DP | 与B3仅差prefix残余账本；无额外在线专家 |

四个baseline列属于三族：DP/TimeDP、external timer、DAgger。另对M做S-only、S+F、S+R三项消融，均1024个不同state/target对，不用重复成功片段冒充等量数据：共同池预留S1024/F256/R256；M与B3用512/256/256，去一个块则用768/256。相同target payload与teacher source、观测模态、执行guard、噪声种子和denoising步数。F/R属于同原attempt的窗口始终同split，不拆片段留出。

先采S，在执行前固定其中512个train-only state/target对为共同U0，仅用U0预训练固定collector θ0（5000 updates），再由该学生采F/R及共享教师标签；各最终训练池均包含U0，1024个去重pair上限包含祖先预训练与后续适应的并集，不能把1536个见过的pair称为1024。这是一次学生state聚合，所有臂得到同池，不把各臂更多rollout预算算作方法收益。teacher takeover后的R按真实actor记录为特权BC，不能伪造成学生访问或OPD轨迹。

任务图共12个（8 train/2 validation/2 untouched test）：训练中分别见absolute、relative、dwell及有限retry；test完整留出“absolute∧relative∧retry”和“双dwell依赖∧hard连续保持”，不只换图像/随机种子。对象目标组合、阈值和graph manifest执行前列明；旧20、paired32、C22和开发已见配置仅可显式legacy-train。视觉扰动单独列，不称task-space泛化。test不用于teacher query、threshold/hyperparameter或checkpoint选择。

预注册cap：训练采集≤96新attempt、≤1536 teacher queries；validation≤8。7个独立权重臂×3 seeds，B2复用B1权重；同架构、batch64、horizon8、15000 updates、≤2 GPUh。TimeDP的前5000次S-only构成共享θ0，B1/B3/M及消融再各10000次等预算更新；B0独立无时间训练同总量。未达到统一更新cap则报告预算不足，不选择性补跑。每checkpoint测12个heldout cells（2图×2 failure类别×3 latency档），共用world seed；主表5臂180 attempts、消融108、θ0对照36，共324。native每attempt≤90s、墙钟≤700s；含96训练、8 validation、2预检共430 attempts，最坏native墙钟cap约83.6h，训练GPU cap42h，非实测耗时。顺序为M0→主表→消融；资源不足时报告未完成项。

主要指标为全attempt分母的最终完整任务TRUE率；并报hard violation/FALSE、UNKNOWN、局部verified recovery、guard veto、reset、teacher查询与两时钟成本。12-cell pilot只作go/no-go：配对完整成功差≥15pp、known违规不增、UNKNOWN不以删除分母下降才扩大预注册；报告seed/cell配对差与按world cell聚类的95%bootstrap区间及每图结果，不作广泛task泛化的统计证明。M不优于B3或仅B2改善，分别支持DAgger或外部规则解释。资格不足、全臂拒绝或UNKNOWN高时停止学习结论。

## 3. 下一条可执行原生实验（本轮不执行）

M0先等独立instrumentation收据，核实实际重力/质量、dynamic/constraint边界、目标与机器人force-on-object的符号/单位/coverage、external wrench及学生delivery。当前getter合同仍缺完整backend kinematic/constraint信息；未解决则load-ready保持UNKNOWN，C0只记录机械诊断，不能入成功BC或声称方法实验已通过。

满足gate后在**新的source/protocol/输出目录**做C0两个paired新attempt，seed20261014，原场景安装保持读回一致，仅版本化控制为“持双侧夹持→已验证load-ready dwell200ms→实际张开→稳定释放dwell200ms”，加一次张开前reseat分支。候选门槛为support≥0.9mg、robot≤0.1mg、|v|≤0.005m/s、|ω|≤0.05rad/s、残差≤max(0.1mg,3σ校准)，位置/角度带与校准误差执行前冻结。这些是新合同需求，不能反套旧20。

C0固定原touch→finger_release窗口[0.30,0.80]s、attempt-start绝对D=70s；两次只改应用队列native延迟0/150ms，物理过程在队列等待期间继续推进。若源代码实际冻结physics，则不把墙钟推理耗时称物理latency实验。更大450ms档留主表；已接受不可取消命令不伪造撤回，所有晚APPLIED/effect及拒绝留RAW。预言是门槛可测时0/150ms强规则仍可能完整通过；若缺反馈或窗口已定错，hard失败保持、安全处置单独计。随后才锁定teacher数据池、复现B0/B1/B2/B3、训练M与消融，按validation选择checkpoint，最后一次性揭盲test。

本交付仅将上述设计写为JSON合同并检查一致性；新native/GPU/train/θ更新均0。旧组件32/32、v04 CPU98、C22已有合成权重各按原范围存在，未被称为新event-time recovery算法或真实化学收益的证据。


本版root复核还要求：任何以mg为门槛的承重标签必须先确认对象的active gravity enabled、非零场景重力与完整外力/约束证据。disabled/UNKNOWN不能默认为开启重力，未知卸载不补零。当前原生仪器化产物由另一分支执行且仍在独立验收，本预注册不据此声称DP训练或新控制实验已完成。
