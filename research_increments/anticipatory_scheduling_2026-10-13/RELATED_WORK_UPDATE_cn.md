# 时间约束与 Agentic Robot：近邻核验更新

本轮下载并核对四篇 arXiv 原始论文，PDF 身份见 `primary_sources/SOURCE_RECEIPT.json`。以下是论文内容与我们的研究判断，不能据此声称已证明原创性。搜索中出现的 RecurDyn 二手介绍没有找到可核对的作者正式入口，因此未纳入核心证据。

| 原始研究 | 已有机制 | 对我们方案的约束 |
| --- | --- | --- |
| [Real-Time Execution of Action Chunking Flow Policies](https://arxiv.org/abs/2506.07339) | 在推理延迟下异步生成动作块，并处理与已提交动作的衔接。 | 必须加入推理延迟强基线；提高控制频率不能自动证明事件后的实际效果及时。 |
| [Temporal Logic Guidance for Action-Only Diffusion Policies with World Models](https://arxiv.org/abs/2606.22729) | 使用世界模型展开动作、计算 STL 满足度并指导扩散去噪；展示搬运时保持物体朝向的约束，长时程约束仍是讨论方向。 | “给扩散策略加入时间逻辑”已有近邻。我们需要比较同世界模型的约束指导，并单独验证独立物理终点、失败后的剩余时间及多操作恢复。 |
| [An Unexpected Robot Policy: Early Evaluations of GPT-6 Astra on RoboDojo and Beyond](https://arxiv.org/abs/2609.24170) | 评估 LLM 直接选择机器人干预；语义任务与精细、动态控制的表现不同，单次示范没有带来整体 ICL 提升。 | Agent 作为直接策略应成为对照；自身行动后果驱动的多次适应，需要与单次示范、固定技能和上下文重置分别比较。 |
| [Enhancing Diffusion Policy with Classifier-Free Guidance for Temporal Robotic Tasks](https://arxiv.org/abs/2510.09786) | 以时间步条件表达任务进度，并通过条件／无条件模型指导动作，减少重复动作等顺序任务问题。 | 必须区分轨迹进度与物理事件参照的截止时间；不能将已有时间条件策略写成完全不考虑时间。 |

我们的优势目前是待验证的假设：经独立计量的时间合同，加完整失败分支、多个必要操作和共享资源的恢复，产生可吸收的经验；共享策略在条件改变后仍能使用这些经验。运行时预测不等于裁判测量，工程工件复用、上下文适应与参数吸收分别归因。

本轮确定性提前调度已经带来改善。因此当前数据无法支持“必须用 VLA／RL 才能解决”或“agentic 学习优于控制”的结论。后续学习比较应使用同信息、同世界模型、同保护层和匹配教师／执行预算，并保留可达性与未知结果。
