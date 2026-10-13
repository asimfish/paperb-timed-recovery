# 可发布的机械时间组件稿与RAW图

[统一方法说明](METHOD_EXPANSION_cn.md)覆盖背景、核心参照、当前实际机制、合同数学、三类失败、强规则已解释的范围及待证明learning问题。[两页ICML稿](COMPONENT_NOTE.pdf)复用已有ICML2026 style，未改字体/页边。

主CPU分母是8条development witness；原作者8次与第三方8次重积分另外验收，24epochs/28,824rows不是24个成功主试验。第三审查PASS是已见结果后的独立复算，非prospective审计。8配置已被development看到，未来32复用不能称unseen holdout。强公开规则batch解释全部8，不证明agentic/query/权重更新必要性。

figures/physical_event_timeline_compact.{svg,pdf,png}用于嵌网页和稿件；标准高版、actual RAW速度与21点确认另外保存。全部图只显示既有机械RAW，不生成RGB或伪frame。完整1201样本/12s记录见原封存bundle，4.2s只是图显示裁剪。

复现排版：在 source/ 用pdflatex -no-shell-escape 两轮编译component.tex。从increment根目录，图仅用系统渲染环境 `PYTHONNOUSERSITE=1 /usr/bin/python3 figures/build_raw_figures.py`，不改变运行中的MuJoCo/NumPy或GPU环境。

robot_supplement/ 是独立原生机器人结果模板，Pending预览不含结果；只从root全部16审计后的最终报告生成，不覆盖本CPU稿、主论文或旧source。
