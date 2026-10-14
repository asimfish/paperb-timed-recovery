M1 的原生采集完整，但独立 force 验收未通过。worker COMPLETE/exit0/no timeout，实际wall842.6282066509593s，allocated GPU wall上界0.23406339073637758h；这不是GPU利用率测量。1000s只是child采集预算，最多30s终止等待和实际cleanup另计。

前瞻f8a读器一次CPU执行退出1，原始RED audit为cba2f6f0988488abb2045b22c7dd1772bb8b64e90951532ad6dcede510cc363d。20源码与门/阈值均未改，也未重跑native/GPU或完整reader。累计M0失败1＋M1尝试1＝2尝试，完整原生采集1、force门通过0、成功训练准入0、权重更新0；原ARIS和M0失败原样保留。

通过的分项：task14007、submit/apply各13995、12FIFO尾步、physical28016、POSTpose逐RAW exact14007、warmup1200/transient30/总native15237、177RGBD/168 sourcevideo帧、176未来image pair＋1terminal image。全部12 physical getter类别28016次OBSERVED。当前是已见fixed expert replay/native RGB仿真数据，不是新学到的机器人技能、heldout、真实硬件、化学或VLA/agentic优势。

同旧固定机械规则重算：机制与主时间联合TRUE；完整copied机械gate仍FALSE（not_diagnostic FALSE）；严格sampled hold FALSE0/1，缺7点8028..8034，jointwithhold FALSE。旧ARIS缺11点8028..8038单独保留，未被本episode替换；不能声称连续tick间接触。

force全部30476行已保存：PRE/POST各15237、BEGIN/END各1。只读RED结构诊断发现18438外层行有至少一个被拒通道；object normal_points被NEGATIVE_NORMAL_SCALAR拒15034次，support reciprocal拒5524次，总20558通道。首次拒绝line9657/POSTtick3597/source3393/native20.12500104960054/callback4828。producer在拒绝时只导出INVALID/reason，没有原scalar/point data，故不能判负值大小、浮点噪声或符号正确性，不能CPU恢复。所有snapshot摘要与同刻clock诊断不一致0，但这不覆盖被丢弃的数值，也不取代原force RED。

force sign/unit、49点两阶段校准、数值候选、完整constraints、全friction/externalwrench覆盖、torque、loadready、robotunloaded均UNKNOWN/未接受。未采用abs、clamp、丢负值或matrix fallback，未生成通过图。训练0。

完整425 regular case成员共1597868840bytes逐hash绑定；731666896byte force大RAW只保留摘要，不放入交付归档。归档只包含独立reader源码/CPU合同、原RED结果、拒绝记录定位、分项公开审计及固定谱系。新增RED诊断是在结果后只读定位，不冒充前瞻新force验收。其初版optional task_pass字段不存在而为null的报告值已用原NATIVE的gate_pass FALSE纠正，初版保留；20前瞻源码和原RED数据不变。
