# 机器人机械时间组件：ICML source 模板

当前仅模板；未读取运行中的16条score，没有填入或推测任何结果。预编译PDF显式标TEMPLATE，Pending不是分数。

只有root的 robot_results/PUBLIC_SUMMARY.json 在全部16 terminal且独立PASS后生成，才可运行 `python3 manuscript/robot_supplement/build_from_final_report.py`。该生成器仅读root公开summary、全部16行CSV、已生成矢量误差图和独立旧读回更正，不读取worker或private RAW。先验证source/calibration SHA、16完整分母、每方法4行、4校准另计及CSV逐行一致，再生成源；失败保持不生成结果稿。

执行后在 generated/ 产生绑定input SHA的tex/receipt/表格；正式PDF须从 source/ 编译 robot_supplement_template.tex，未通过生成前缺input会报错。预览用 `pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=../build '\def\TemplatePreview{1}\input{robot_supplement_template.tex}'`；此模式强制Pending占位，即使日后generated存在也不读取分数。

主表同前台并列primary、strict sampled hold、primary+hold；动作FIFO仅位置目标，参数前/后/末三快照，不宣称逐tick增益；经验范围不是支持保证，4固定实例不是随机seeds。中点与精确grid如计数相同自动说明未证明额外收益，不称学习或化学实验。旧readback更正保留完整链接与SHA。
