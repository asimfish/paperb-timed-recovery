# C5：更早预测的命令与物理停止权衡

2026-10-11。接续[冻结预测器的标定迁移](../c5_baseline_transfer_2026-10-11/README_cn.md)，实际新增 **32 条闭环控制仿真轨迹、10272 张 RGB**，复用16条基线来源。场景/延迟与公开参考色保持相同；原始2秒窗口、停止动作和连续相机权限均未扩展。这是看到上轮失败之后的开发选择，不是独立确认实验，CT-C1 MAJOR_OPEN。

## 完整结果

[参数与cohort](PROTOCOL.json)在新轨迹之前冻结。原基线为已标定的5帧线性预测，激活门槛为阈值的0.6；早期线性组只将门槛降为0.1；二次组在早期线性基础上增加正斜率、正曲率、历史残差受限的局部二次预测，拟合不合格时仍使用早期线性。三者都保留普通两帧视觉反馈兜底。5帧数量、2秒预测范围、150 ms探索性保护余量与控制接受延迟不变。

| 策略 | 原命令计时 TRUE / FALSE / UNKNOWN | 流量计时 TRUE / FALSE / UNKNOWN | 两项计时同时 TRUE / FALSE / UNKNOWN |
|---|---:|---:|---:|
| 已标定原线性基线（复用） | 16 / 0 / 0 | 14 / 2 / 0 | 14 / 2 / 0 |
| 更早激活的线性预测 | 16 / 0 / 0 | 14 / 2 / 0 | 14 / 2 / 0 |
| 局部二次预测＋线性兜底 | 10 / 6 / 0 | 15 / 1 / 0 | 10 / 6 / 0 |

两项计时的合取是诊断指标，**不是完整化学任务的联合成功**。所有策略的完整化学成功认证均为0，独立化学任务标签仍UNKNOWN。流量终点是低于 `0.005 mL/s` 并持续0.2秒，不是最后一滴。

所有零视频交付延迟设置都满足两项计时。1秒交付延迟下，降低线性门槛仍不能解决快显色与组合场景的流量超时。二次预测使这两例的流量间隔降为 `[1.96,1.98] s`，但同时造成其余6例的命令早于实际触发：名义条件提前 `[0.57,0.58] s`，慢显色提前 `[3.63,3.64] s`。慢显色的低流量停止也比颜色触发提前 `[2.07,2.09] s`。所有提前/超时结果均保留。

相对基线，更早线性在两项计时合取上改善0例；二次改善2例、损害6例，带符号的TRUE差为−4。不能只报流量TRUE从14升到15而称为总体收益；本轮也没有显著性、置信区间或VLA/RL优越性结论。快响应二次预测的物理停止上界仅比时限早20 ms，这不是实机抗延迟保证。

## 方法与机制上的收获

本轮显示了一个具体的失败链：弱颜色证据的点预测可以较早提交，但局部拟合残差小不代表未来时间区间可信；过早停止还会改变材料加入和后续颜色终点。慢显色二次组的实际触发相对原基线后移 `[1.14,1.16] s`。因此不能用原基线视频中的触发时刻给新策略计算反事实成功，必须核对每条实际新控制轨迹。

[机制与区间条件](TIMING_MECHANISM_cn.md)整理了保留C5命令约束时的可行提交范围，明确其假设和适用范围。它是基础区间推导，不作为新颖性或实机保证。当前更明确的后果预测目标包括：在所选动作后任务终点是否仍存在、命令接受、实际物理完成及独立任务成功。这个目标尚未完成学习验证。

Agentic 下一步应检验有真实代价的信息/控制选择如何改变可用时间、预测区间、执行尾流及任务完成，先与同权限的完整公共历史预测、设备/流程标定和普通MPC/规则调度比较。此次固定ROI、无付费工具的比较不证明需要大模型、agentic或RL，也未排除更充分的普通控制基线。

## 独立验收与证据边界

48条不同来源轨迹全部完成独立核对：32条新轨迹和16条复用来源。审计没有导入新预测器或生产运行器，以保存的PNG重新提取ROI分数，以另一套NumPy最小二乘/求根实现重建预测与停止决策，并用闭式动力学复核测量、体积、颜色、控制事件、区间计分与完整cohort。10项针对性单元检查通过。

32对“基线/新方法”比较在第一次接受动作分歧之前，物理轨迹、相机时刻与**策略实际读取的ROI像素严格相同**。全幅RGB仍未完全相同：共179次成对帧比较在ROI外有最多1灰度级差异，计数是帧比较次数，不是独立样本或唯一帧数；同一基线帧可能被两组比较。沿用上轮未解决的全幅渲染边界，结论为 `PASS_SCOPED_ROI_BASELINE`，不能迁移为全幅VLA精确配对主张。没有改写原始图片来通过检查。

所有策略只接收已到达的分数、公开时间戳和参考阈值，不接收场景名称、私有流量、过程tau/width、裁判触发、未来帧或事后尾流。MuJoCo与颜色过程继续耦合运行；没有用固定视频替代新控制。主机推理/渲染耗时单独测量，没有推进模拟时间；声明的交付/控制等待会推进过程，因此未得出真实推理预算下的部署结论。

## 文件与复现

- [独立审计](development_v1/independent_audit.json)、[完整原始结果](development_v1/development_results.json)、[逐轨迹时序分解](development_v1/timing_tradeoffs.json)。
- [结果与时序图 PDF](figures/c5_early_tradeoffs_v2.pdf)，同名SVG/PNG可编辑或预览；v2使用两排布局增大论文宽度下的字号，旧v1保留。
- [实际编译的两页 ICML 增量预览 PDF](paper_preview_v3/paper_note.pdf)与[构建收据](paper_preview_v3/build_receipt.json)。最终v3保留较大字号并修正大图浮动分页；旧v1/v2保留，正式主论文未替换。
- [ICML结果段落](paper_result_note.tex)、[机制条件](TIMING_MECHANISM_cn.md)、[下一步执行合同](NEXT_EXECUTION.json)、[状态与身份清单](COMPONENT_STATUS.json)、[交付核对](DELIVERY_VERIFICATION.json)。

在仓库根目录运行，输出目录须不存在：

```bash
python3 -B -m unittest discover -s papers/paperB/research_increments/c5_early_color_baselines_2026-10-11 -p 'test_*.py'
MUJOCO_GL=egl python3 -B papers/paperB/research_increments/c5_early_color_baselines_2026-10-11/run_early.py --out /tmp/c5_early_new
python3 -B papers/paperB/research_increments/c5_early_color_baselines_2026-10-11/audit_early.py --data /tmp/c5_early_new
python3 -B papers/paperB/research_increments/c5_early_color_baselines_2026-10-11/analyze_early.py --data /tmp/c5_early_new
python3 -s -B papers/paperB/research_increments/c5_early_color_baselines_2026-10-11/plot_early.py --data /tmp/c5_early_new --stem /tmp/c5_early_new/figures/tradeoffs
python3 -B papers/paperB/research_increments/c5_early_color_baselines_2026-10-11/build_preview.py --out /tmp/c5_early_note_new
```

启动时保存8份源码身份；后来新增的分析/绘图/编译文件另记在状态清单，不冒充启动快照。父数据/源码与Paper A未修改。本增量保存新的论文材料、图件与ICML预览，未改写主论文PDF，也未发布线上网页。
