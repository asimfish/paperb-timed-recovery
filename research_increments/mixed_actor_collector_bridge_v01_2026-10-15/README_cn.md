G1 混合 actor collector 软件桥：完整 case header、H8×9 映射与前瞻容量

本增量只交付 CPU 可执行软件候选，不修改 sealed v02、v04 或旧 native RAW。当前 native/GPU/模型推理/训练/真实 student rollout 均为 0；不构成独立 physical verifier、安全 authorizer 程序、S/F/R 准入或主方法收益。

已实现：

- `code/collector_bridge.py` 的 `CollectorBridge(header, expected_header_path=..., expected_header_sha256=..., directory=...)` 在写文件前读取调用方独立冻结的完整 header，并要求 byte SHA 与所有字段精确一致。完整 header 绑定原 deadline/clock/failure anchor、task graph/split、student/teacher source、显式权重类型与 SHA、policy config、旧 source pins 和本 bridge source。`readback` 与 `replay_bridge` 再次要求外部完整 header，内层 registry header 也必须一致。仅 journal self-hash 或旧 `expected_pins` 不足以替代该检查。
- `record_chunk` 保存真实声明的 H8×9 output；每个有效 row 用同一个 chunk ID 与 step index 关联独立 9D proposal、SUBMITTED、CHANNEL_RESULT。72D flatten 拒绝，terminal valid_steps 明示，padding 不产生 command。输出、submit 和 APPLIED 不互相替代。
- 每个 chunk 在产生任何部分 command 前同时预留 proposal、submit、result 容量。append 将预留逐项消费，实际状态/包/访问/切换/标签也按 kind 计数。容量不足立即前瞻拒绝，已采 RAW 与 pending commands 保留；不静默丢命令、丢 APPLIED 或缩短 B3 prefix。
- `successor_source/code/mixed_actor_registry.py` 是 v02 的独立复制版本。精确 diff 仅涉及 header schema 0.3、新增 `event_cap` 字段及 1…100,000 校验、原 8,192 常量改为已绑定的 header cap。其他因果、deadline、三值、安全和 actor 归属代码保持原件。`SUCCESSOR_DIFF_CONTRACT.json` 与 loader 对该 diff 逐字检查；sealed v02 27 件原件仍核对原 hash。
- 实际 unsafe/post-D observation、student visit 与行政切换继续可记录。ORIGINAL_GOAL、SAFE_LOCAL_RECOVERY、SAFETY_ABORT 的命令继续使用 v02 逐动作 authorization；晚 F 保留，UNKNOWN abort 只能成为 APPLIED behavior，不自动变成 R/S。先前接受的 FIFO command 在 actor 切换后保留原 author/source/purpose。

前瞻长 case 容量（CPU 示例，不是已运行的 native case）：

| kind | cap | 来源 |
|---|---:|---|
| OBSERVED_STATE | 14,010 | 14,007 task steps + initial 1 + terminal reserve 2 |
| PROPOSAL / SUBMITTED / CHANNEL_RESULT | 各 13,995 | 每个有效 command 各一件，不复用或截断 |
| PUBLIC_PACKET / STUDENT_VISIT | 各 177 | 有限公开 history，最多 512，不滑掉历史 |
| TEACHER_TARGET / ACTOR_TRANSITION | 16 / 32 | 每次 query 的 takeover + return 预算 |
| VERIFICATION | 66 | 64 declared audits + terminal reserve 2 |
| FULL_TASK_FAILURE / RESET | 16 / 0 | 独立失败声明；本例无 reset |
| 合计 | **56,479** | writer 与 reader 从同一个完整 plan 精确导出 |

旧 v02 的 8,192 容量拒绝测试仍运行并保留。新 successor 不是只把常量改大：完整 header 的 per-kind plan、精确总 cap、外部 SHA、source diff 与实际 13,995-command build/replay 一起形成软件证据。

调用方挂点顺序：真实 readback → `append('OBSERVED_STATE', ...)`；实际公开包交付 → `PUBLIC_PACKET`；真正 student 访问 → `STUDENT_VISIT`；策略输出 → `record_chunk`；逐 row 实际 proposal/accepted driver command → `append` 加 `{chunk_id, step_index}`；channel 实际结果 → 同样 origin。新 `bridge.jsonl` 与内层 `registry/registry.jsonl` 必须逐行一一对应；reader 拒绝缺失内层事件。旧 v04 单 actor 日志须按真实 actor 段另行挂接，本候选没有冒充该 native 接通。

源码中的 policy weights SHA 和 safety authorization 是外部可信调用方声明的绑定值；本桥没有加载或核对真实权重原件，没有执行安全 authorizer，也没有验证物理事件。部署时仍要由独立 case-source/模型加载收据和 native reader证明这些事实。单进程可信 writer，可变进程内对象和有写权限的程序不受本桥隔离；hash 不是签名或发布者认证。

实际 CPU 结果见 `CPU_RESULT.json` 与 `cpu_checks/long_fixture_v01/LONG_CPU_RESULT.json`。首次长 fixture 在内存真实建立并语义 replay 所有事件，只保存内容 SHA、字节数与首尾样例；未保留全量 journal 的缺口也保留原样。独立审查指出该证据缺口后，进行一次明确的 deterministic CPU trace reconstruction：collector/registry source、header 和固定输入不变，两种完整 trace SHA 必须与原先实际 replay 的 SHA 精确匹配，完整 journal 写入 `cpu_checks/long_fixture_retained_v02/retained_case`。该调用不再次跑 replay、不制造新的科学/native outcome；首次 replay 与重构结果分开记账。它测软件事件归属/容量/目标映射，不测运行时间准确度、连续物理执行或长期原生采集性能。长 fixture 的 1,750 chunks 最后一个有 3 valid rows，不把 5 个 padding 当执行目标。所有实验用 invented CPU input，并没有真实 teacher 调用。

复现：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:tests python3 -B -m unittest discover -s tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=successor_source/code:successor_source/tests python3 -B -m unittest discover -s successor_source/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:tests python3 -B code/run_long_cpu_fixture.py --output-directory <new-owned-directory>
```

所有已有目录与 sealed evidence 均不得覆盖；long fixture CLI 对已存在 output directory 拒绝。日志保留初次 setup 目录创建失败及修复、第一版 25 tests 和 journal aggregate-bound 补强后的 27 tests。未放宽旧 deadline/safety 规则。
