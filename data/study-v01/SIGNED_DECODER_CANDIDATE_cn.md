# Signed selected contact decoder 0.5：纯 CPU 候选

本目录是 **M2 结果后的新解析候选**，没有替换 native adapter。旧0.4、M1/M2原件、legacy normalized INVALID、原门槛与计分全部保留。新增 native / GPU / SDK import / 原读器重跑 / RAW大文件扫描 / 训练准入均为0。

候选的依据是 [NVIDIA Isaac Sim5.1 RigidPrim 接触API官方示例](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim.get_contact_force_data)：count4/start0引用的前四个有效标量是负数，其法向接近+Z。因此“API所有有效scalar必为非负”不成立。官方示例省略dt，默认1可能表示impulse；不能把该例当成经过校准的N数据，也不说明任意负值都物理正确。

`code/signed_selected_decoder.py`只消费已复制的 `PaperBSelectedContactRawEvidence/0.1`。它核对canonical SHA、字段与整数类型、capacity/filter预算、count/start和range一致性、范围非重叠、完整selected point rows、buffer metadata及有限值，再计算 **signed scalar × 原normal**。不abs/clamp、丢弃负点、normal重归一化、重复除dt或以matrix吻合授予资格。负零与tiny negative保留。zero-count pair的start不用于访问point，范围外未引用值不进入诊断。

输出状态为 `DECODED_SIGNED_SELECTED_DIAGNOSTIC_ONLY`，不是force PASS。输入所称的N/world frame仍只属声明；force-on-actor符号、物理单位/坐标系、load_ready、robot_unloaded、torque均UNKNOWN。selected normal点不覆盖friction、完整约束、external wrench或torque；training/RL/OPD资格不被开启。SHA只证明内容身份，不证明测量来源认证或物理正确。外层snapshot/clock/source绑定仍需另行验证。

明确区分两个测试来源：

- 官方符号示例被投影为一个sensor、count4/start0的合成toy。仅四个scalar与共同normal取自示例；point、separation、未引用容量值和单sensor结构是合成的。旧0.4 normalizer仍报 `NEGATIVE_NORMAL_SCALAR`；新候选保留四个selected负点，Z向诊断sum为−490.3139。它不是一次真实物理RED→force PASS。
- M2首TASK点严格来自已封 `PUBLIC_AUDIT.json`（SHA `5146cc63…`）。其scalar为−1.9239716529846191，单点signed product与公共摘录精确一致。此为**后验单点摘录兼容检查**，并非完整evidence或snapshot；原raw/snapshot SHA仅为来源reference，未被沿用成新子集的digest。没有重建全原记录或重新扫描RAW。

实际一次CPU suite有15个针对性checks通过，覆盖上述合法输入，以及篡改/错误external pin、重新hash后的错误metadata/count/range、重叠/溢出、缺失point、selected nonfinite/tag/布尔或字符串、copy incomplete、错误schema/friction、duplicate JSON keys、大小/深度/整数预算与浮点运算overflow。真实CLI toy成功退出0，错误external pin退出2。这些只是解析器契约结果。

安全边界限定为JSON：最多读取4MiB+1 bytes，depth≤12、nodes≤100000、capacity≤4096、filters≤64；不pickle、动态执行、网络请求、调用provider或修改场景。bounds为工程输入预算，不是新的物理阈值。数值乘加采用Python浮点，未承诺原Tensor位模式或高精度物理求解。

`parent_reference/`的两份helper/adapter逐字节复制自已冻结lossless0.4 source release `7adc1e24…`；helper SHA为`7b7e9ae8…`，adapter SHA为`9aaa3667…`。原目录没有修改。`evidence/INPUT_PROVENANCE.json`保留完整SHA与来源。新source/test contract和CPU输出闭合后交root独立审阅；真实native集成、符号/单位/反作用力/载荷校准须另立前瞻协议。

执行候选toy：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python3 -B \
  code/signed_selected_decoder.py \
  --evidence fixtures/OFFICIAL_ACTIVE_NEGATIVE_PROJECTED_EVIDENCE.json
```

本候选没有改变M2的旧合同INVALID；数值解析与物理/学习资格必须保持分离，完整科学验收仍MAJOR_OPEN。
