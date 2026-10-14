# G1 v02 接入边界（不是当前源码故障）

独立源码与 CPU 语义验收不能改写为“原生混合主体采集已经可用”。G1 仍是 `NOT_READY_FOR_NATIVE_INTEGRATION`：生产行、实际 student rollout、model/GPU/native 调用、训练准入和新权重均为 0。

这个候选的 event cap 为 8192，action dimension 为 1–64。M1 有 13995 个实际 APPLIED driver command；若每个原生 tick 都登记 state、proposal、submit、application 和监督事件，无法直接装进这个上限。未来 collector 必须先声明事件量与记录层级，并在新源码闭包及前瞻 reader 中校验；不能静默删除、丢弃或截短轨迹、失败记录或 B3 历史以适配容量。

P0 的动作块是 horizon8 × driver9D，即 72 个标量，不能未经新 schema 或映射便当作此接口的一个 flat target（最大 64D）。未来接入应明确 chunk decision 与逐 9D command 的关联，保留每个实际控制的来源、owner、submit/APPLIED 状态、时钟与全部 RAW。该说明不授权或实现新的 chunk→driver 展开。

还需实际 collector/channel/安全 authorizer/verifier 的独立来源与事实核验。当前 source pin、hash chain、semantic replay 和合成 CPU TRUE 标签不能证明物理安全、force 资格、完整任务成功、化学终点或学习效果。超出容量、维数或单 writer 假设时，应建立独立的新协议、源码和前瞻读器；不能改写已封 G1 v01/v02、v04 或原生旧日志。

构造器的外部 `expected_pins` 不包含 actors、原目标 deadline/clock 与 split 内容的全部预期值。这些值由起始 HEADER 声明，hash/replay 检查相对该 HEADER 的后续一致性，不能识别“整体重写 HEADER 并把全链重封 hash”。当前软件验收以调用方提供的 case/header 可信为条件。未来 collector/root reader 必须绑定完整 expected-header hash，或逐项比较 independently frozen protocol 中 student/teacher 来源与权重、原 goal D/clock、task graph/group/split 等值，不能宣称 v02 单独阻止起始 HEADER 伪造。
