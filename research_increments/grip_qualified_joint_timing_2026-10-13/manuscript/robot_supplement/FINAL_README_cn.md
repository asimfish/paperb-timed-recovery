# 全16条机械时间测试：两页ICML补充稿

最终稿 [ROBOT_TIMING_SUPPLEMENT.pdf](ROBOT_TIMING_SUPPLEMENT.pdf) 已两轮编译并逐页查看；[canonical LaTeX](source/robot_timing_supplement.tex)、生成宏、纸稿矢量图与完整16行CSV一同绑定最终root报告。原CPU稿及其8-member archive保持不变。

主机械条件16/16；primary T/F/U=8/2/6。nominal 0/2/2，FIFO prior 0/0/4，calibrated midpoint与exact joint各4/0/0。未知保留完整分母，不是确定物理失败。两个先验合计contact/gap各8项INDETERMINATE，仅release2项LATE；gap上界约25.00094ms触及冻结25ms边界，不重设eps、不以理想dt改判，不宣传巨大实际迟到改善。中点和精确求解当前计数相同，未证明额外收益。

strict sampled hold与primary+hold均0/16；每条11个张开后至复合稳定释放前的负双侧点保持。释放仍是supported/unloaded/stable8点窗口onset，不能改成first unload或可容忍fraction。

新4校准另计；mass/inertia是无量纲倍率：校准.8/1.2，测试.9/1.1插值。4固定条件，无随机seeds/CI；D随mass、H随FIFO绑定，不能独立归因。K/D/force前/后/末三完整快照，不是逐tick遥测；FIFO只位置目标，不是整个通讯/LLM延迟。观测cal范围contact/release各16/16 CONTAINED仍是经验范围，不是支持保证。旧1200-step warmup实际参数读回更正明确保留，旧source与失败不改。

测试/校准样本224132/53732，合计277864；RGBD816/36合计852，四预定视频672帧另记，不添加episode/native steps。GPU-wall owned上界test1.1707272459961113h+cal0.3011841987363813h=1.4719114447324926h；不是GPU kernel消耗或学习训练。

本公开稿包提供最终报告、完整结果CSV、独立public summary、版本与校验receipt、纸稿图和排版源；全部机器人RAW及native执行证据另由root管理，不声称本包公开全套RAW。方法仍是原生IsaacLab/PhysX机械组件和规则调度，非真机/化学终点/VLA学习。

源包解压到空目录后，在 manuscript/robot_supplement/source/ 用pdflatex -no-shell-escape两轮编译robot_timing_supplement.tex。结果来自已完整验收的root公开报告；排版/作图没有新增physics、GPU、fit或参数更新。
