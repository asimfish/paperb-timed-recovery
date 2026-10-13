# 时间合同、可验证经验与共享策略：当前方法和证据边界

当前最有价值的发现是：**正确地定义与验收时间合同，和证明新的机器人学习算法有优势，是两件不同的事。**我们已经得到真实原生积分的开发证据：外部事件发生后，受控过程遇到故障、等待共享资源，最终仍可满足原事件上的合同。但一个使用合法公开模型推断和两次冗余停止的强规则batch，已经解出v2全部8个名义条件。因此，这组结果不能证明agentic算法、额外history query或策略权重更新的必要性。

这份说明覆盖已封存的资格、开发和v2组件。机器人A-r7的4校准、16测试有独立执行与验收路线，结果由主agent另行汇总；本稿没有导入运行中的结果，不把v2开发witness计为正式32方法试验。图全部来自既有RAW，不是生成视频或VLA rollout。

## 1. 背景与研究问题

实验室操作经常有过程时间合同，例如端点出现后必须在短窗口内停止滴加、实际搅拌需维持规定时长、某个后续操作必须相对已经发生的加料事件完成。机器人“发出停止命令”并不等于阀门已经停止流动或电机已经停止运动；设备关闭也未必意味着化学反应已经终止。资源排队、执行延迟、观测陈旧和失败重试都会改变实际终点。

需要区分四种时间：观测捕获/交付时间、策略计算与通讯时间、实际动作发生时间、化学过程终点。动作序列流畅、推理快或最终任务完成，都不能单独证明满足物理期限。当前position-target FIFO只延迟这一条目标通道，即时重力补偿和guards未一起延迟；其结果不能推广成全部通讯或大模型推理实时性。

我们希望检验的完整问题是：**在继续演化的实验过程中，经过独立原合同验收的成功、失败和修复经验，能否被共享策略吸收，并在相同信息与资源预算下提高未见任务的有效完成率？**Agent的候选职责是任务编译、数据与失败选择、修复建议和数字孪生维护；低层执行器负责实际运动；独立referee负责标签与准入。DP、offline/online RL、OPD是待验证的训练选择，不是串联即可成立的贡献。

## 2. 核心参照已做到了什么

[MATTERIX](https://www.nature.com/articles/s43588-025-00924-4)已经提供化学数字孪生、多设备/机器人工作流、HSM与等待primitive、并发执行、过程语义和workflow verification。用户提供的PDF在p75记录加热器关闭后反应继续演化，因此“设备off不同于过程终点”不是我们的新发现。它的原生机器人/化学流程与本文机械rotor不能直接比较成功率。我们可以复用其场景/设备/skill接口思想，但exact原运行时复现和本组件adaptation必须分开。

用户提供的Auto-Engineering实际文章描述机器人接入、技能组合、仿真数据、BC/DAgger、部署诊断与工程资产复用；它是[General Robotics公司报告](https://www.generalrobotics.company/post/introducing-auto-engineering-for-robotics)及所给微信转写，不是本地独立复现的匹配基线。工程经验、代码/校准复用和actor权重吸收不能混为同一结果。

时间方向的近邻也很明确。[Chronos](https://arxiv.org/html/2610.13929)研究捕获/查询执行时间条件和物理时间policy；[Time as a Control Dimension](https://arxiv.org/html/2511.07654)覆盖准点、remaining-time、扰动恢复和协调。[RoboRSI](https://arxiv.org/html/2610.12424)已有task/skill contracts、修复以及执行经验训练ACT的机制；[GPT-Policy](https://arxiv.org/html/2609.19138v1)研究冻结模型的上下文/工具策略结构。我们没有复现并击败这些算法。“没有VLA关注时间”“首次agentic闭环”“首次把经验写入策略”都不是当前证据支持的主张。

有希望的增量是把**实际发生的原事件、独立物理终点、资源/依赖合同、经验准入和权重吸收的归因**连接成一个可反驳的研究问题，并证明其收益不能被强同信息规则控制、更多覆盖或外部stack更新解释。目前只完成其中的组件。

## 3. 当前真正执行的机制

A-r7路线保留固定瓶操作技能，统一安装候选K1600，并用独立校准的经验延迟区间比较调度；这是工程参数与规则调度，不是DP/VLA或权重训练。夹持资格、三时间项、原机械条件、strict sampled hold与joint_with_hold分别报告。新机器人测试不得从单条资格结果借用时间成功率。

单条三转子开发组件使用CPU MuJoCo真实积分：B独立运动，其首次q=2跨越是已经发生的原事件；A/C经过真实串行事务ACK切断motor torque；一次A-stop事务被消耗但未切drive；B任务和C事务会占用共享通道。每10ms保存实际q/qvel/next ctrl、捕获/交付packet、submit/service/ACK与原事件证据。初始化后不写qpos/qvel/时钟；重复停止不能把已经发生的B事件撤回。

Actor只收合法延迟公开packet、ACK、公共合同、资源预约和预声明的nominal模型。ACK表示事务已处理，不证明物理效果；RAW referee读取的事件/故障终点不会进入actor。默认公开捕获间隔50ms、交付延迟100ms。原粗B事件[.40,.45]在.55s到达，记录保持不变。所有强基线都可从已收到的前后q/v及同一公开模型条件重建同事件[.44,.45]；这不是新的锚点，也不是把RAW oracle输给控制器。模型兼容性检查没有拟合参数，且不能单独证明模型真实支持。

v2候选用B预约start.65s、A原事件后[1.8,D]、C[D±.15]和40ms依赖边；图方向×Bbusy50/450ms×D2.8/3.1独立交叉，质量固定，不再绑定D。一个强公开batch使用允许给所有控制的两次A盲冗余，覆盖none/first-drop两种结果。八条12s轨迹均由RAW验收通过，原作者八次与第三方另外八次命令重积分state/time误差均为0。合计24个不同角色积分epoch、28,824样本，主witness分母仍为8。第三独立审查已[通过](../research_design/independent_prospective_v2_witness_review/PUBLIC_AUDIT.json)，它是已见开发结果后的独立复算，不冒充执行前冻结的prospective审计。没有query、fit、GPU、LLM或新权重。第二动作真实修复了故障后的原合同，但动作在故障反馈前安排，因此不是postfailure诊断或自适应学习证据。

图见[实际事件时间线](../figures/physical_event_timeline.svg)、[实际速度](../figures/raw_velocity_traces.svg)和[21点确认](../figures/confirmation_samples.svg)。一次开发轨迹展示反馈retry与C实际等待；v2轨迹展示预先冗余和非空图边。图中4.2s视窗只是显示裁剪，完整12s/1201样本原件保持。

## 4. 数学合同与可达性

令任务包含事件图G、时间/维持合同Φ、公开观测规则O、允许动作和资源容量R。独立事件发生区间为I_e=[l_e,u_e]，带明确原生epoch；确认时刻另存。对于从a到b的目标D，误差区间为

\[
I_{\rm err}=[l_b-u_a-D,\;u_b-l_a-D].
\]

全包含于[-eps,eps]才为TRUE；完全不相交为FALSE；部分重叠为UNKNOWN。缺失、左删失、无效时钟不能成功。联合结果还须满足实际机械/过程条件、原事件、图边、资源和保护条件。多合同仍只计一个episode；失败/拒绝/UNKNOWN/超时和预算耗尽留分母。尚未launch的资源门槛slot另报未执行，不用成功complete-case分母。

物理stop需有先前moving样本，随后|qvel|≤.1持续至少200ms的采样跨度；10ms下是21个正样本、20个间隔。发生区间和确认时刻不同，逐tick成立也不证明点间连续性。瓶释放同样必须保留原8点supported/unloaded/stable-window onset，不等价第一卸载时间，不能事后更换终点让严格hold失败消失。

在C窗口D±eps、A upper U_A、C→A gap g的box证明中，设原事件宽w、C事件box宽c、A可能结果box宽a。由

\[
c_L\ge b_U+D-\epsilon,\quad a_U\le b_L+U_A,\quad
a_U\ge c_L+c+g+a
\]

得到必要条件

\[
w+c+g+a\le U_A-D+\epsilon.
\]

它不是充分的物理可达性条件，资源容量、因果观测和primitive都要另外检查。未知none/drop且两A ACK相隔50ms时，A结果联合box可约60ms；合法torque反馈后可缩到单事件约10ms，不能永远把a锁死。粗w50ms时某证书类不足，公开模型合法细化w10ms后可通过，因此没有“不可约公有信息下界”的证明。真正下界需要两种物理后果兼容同一合法历史的aliasing证据，本轮没有。

## 5. 三类已发现的失败

第一类是**资格/终点语义失败**。旧单条资格的原机械条件通过，但三项时间均EARLY、主joint为FALSE；strict hold也为FALSE。11个缺双侧接触样本7448–7458在open7440之后、composite release7459之前。运输fraction≈.998767不证明整个区间维持；raw supported/unloaded点7455与稳定窗口7459不能互换。

第二类是**联合可行性失败**。单项窗口、图边和实际server分别看似合理，组合仍可没有合法ACK路径。旧1.50s预约草案有6/8条件的资源支撑缺口，原warning保留；新合同下的.75s候选仍有C→A/highbusy/D2.8不可达model下界：C若在预约前结束则太早，预约后最早stop end3.21，而A截止3.24减去gap/样本宽只允许C end≤3.19。拒绝本身不是infeasibility证明；每个原条件需要正witness或明确动作域内的独立负下界。

第三类是**证书与创新归因失败**。物理witness、某个coarse-box证书和真正公有信息可达性不同。粗观测不能自动变成不可约信息缺失；强基线可利用同样的模型、反馈和合法冗余。本轮一个强batch已解全8，直接削弱“必须新agentic算法”的解释。工程参数K、observer/model、harness或coverage改进也不能直接当成actor theta吸收。

## 6. 强基线已解释的范围与还不能解释的范围

已解释的范围是：已知、无噪声、预声明线性nominal模型中的8个固定机械配置，原事件可经公共历史条件估计，有限一次A-drop可用两次冗余覆盖，资源预约已知。没有hidden physics域泛化、化学终点、真实RGB/VLA、未见故障、真实大模型等待或weights学习证据。

这8配置已经development可见。若后续32复用相同配置，它只能是冻结四控制的固定配对机制比较，不能称从未见过的heldout图或随机seed泛化。正式方法要共享同一public estimator、合法反馈和冗余动作权限、同一模型/观测/预算，不能为了让某个方法赢而削弱基线。预先规定可达性、条件信息和不可达sentinel分层；主失败/拒绝/UNKNOWN保持完整分母。当前八条不是正式32已完成。

## 7. 真正待证明的learning问题

首先完成独立物理接口准入：C5需要实际flow/valve与端点信号，C6需要加载电机/RPM与实际停止，C13需要真实材料转移的开始/结束；加热需区分设备off、温度和反应终点。现有颜色变化、TCP到达、直接写angular velocity或刚性瓶proxy不能替代这些合同。原benchmark定义保持，不借机械rotor验收作化学成功。

然后固定外部K、observer、模型和harness版本，分别检验theta固定/更新×上下文清空/保留。清空上下文且取消在线expert后仍改善，才能支持参数吸收；冻结theta、只保留合法历史的跨episode改善是上下文适应。前处理或twin更新应单独归因，不把工程知识库K和策略memory M都记成theta学习。

共享DP/时间条件输入需要同backbone/data/optimizer，比较合法时间、捕获/执行时间和history reset/shuffle；不能把时钟访问差异当结构增益。学生状态标签需与offline expert imitation匹配teacher、总labels、更新、native交互和compute，并设student-state DAgger强基线。若只是硬标签聚合，应称DAgger式监督；OPD要另明确occupancy、teacher权限和蒸馏objective。offline/online RL只有在失败credit或适应假设清楚时才开展，不是必须依次跑的仪式。

最终要求是未见完整实例、任务依赖/资源组合、物理漂移与故障的严格split，独立原合同和预算验收，全部失败保持。Agentic经验引擎的收益可另测数据准入准确率、有效恢复覆盖、总工程成本和跨版本复用；这些不自动证明VLA参数增益。当前强规则已解释的8个名义配置应作为负创新性发现保留，下一阶段需要更真实且能分辨这些假设的实验，而不是继续累加toy数量。

来源细节与封存receipt见本increment的 research_design/、research_design/prospective_v2/，以及相邻 scene_methods_expansion_2026-10-13/core_reference_alignment/。本稿只梳理现有证据，没有重新运行physics或修改原合同/源码。
