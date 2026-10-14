# Failure-Preserving Experience for Event-Timed Robot Policies: A Causal Contract and a Predeclared Learning Study

Research draft; **MAJOR_OPEN**. Evidence as of 14 October 2026. The proposed learning study is unexecuted; new VLA weights and force-qualified admissions are zero.

## Abstract

Robot experience is difficult to label when a physical operation has a deadline, observations arrive late, and a safe recovery occurs after the original requirement has already failed. A successful cleanup is useful experience, but is not evidence that the missed event occurred on time. We specify a causal event-time contract that separates physical onset, confirmation, audit arrival, and policy delivery; retains immutable attempt and deadline identities; and admits typed success, student-state correction, and executed recovery supervision. We then propose a diffusion policy conditioned on a deterministic residual-event ledger computed from the same public history supplied to its baselines. Existing diagnostics motivate the necessary controls: four schedulers tie across 32 known development episodes; a 54-run CPU study distinguishes native from wall-clock success; and explicit rule memory exceeds a symbolic learned-history baseline. A new full robot-simulation collection passes basic trace integrity but fails its prospective force-detail contract, leaving physical load qualification unknown. No new VLA weights or heldout learning gains are reported. An equal-data, equal-information study is specified to test whether the ledger and typed experience improve shared policy weights beyond student-state imitation.

## Introduction
A laboratory robot may need to stop heating after a specified duration or complete a transfer within a short interval after another operation. These requirements refer to physical events. Sending a command before a deadline does not show that its effect occurred before the deadline. A later recovery can leave the workspace safe while a time-sensitive experiment remains invalid. This distinction matters when robot agents collect their own experience: a trajectory that ends in a desirable state can still contain an irreversible failure that should not become a successful demonstration.

The difficulty is not simply adding a clock to a policy. Temporal conditioning is already an established direction, including physical-time robot policies such as Chronos [Chronos Policy: Learning Robot Policies on Physical Time (2026)](https://arxiv.org/abs/2610.13929v1). Student-state supervision is established by DAgger [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning (2011)](https://proceedings.mlr.press/v15/ross11a.html); robotics-assisted chemistry twins already combine manipulation, process dynamics, and workflow semantics [MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation (2026)](https://www.nature.com/articles/s43588-025-00924-4). Our question concerns their interface: **can experience preserve the identity and causal status of physical failures while still supplying useful correction and recovery targets to one shared policy?**

Three distinctions make this question concrete. First, event onset, confirmation, and the arrival of an independent audit can have different timestamps. Second, the policy's actual history may omit referee measurements that become available only offline. Third, correcting a student at a visited state and observing an executed recovery are different forms of supervision. Ignoring these distinctions can turn future information into apparent adaptation, treat a teacher proposal as a verified action, or make a missed deadline disappear through relabeling.

We specify an event-time contract and a candidate learning mechanism. The contract preserves original attempts, event occurrences, and hard failures, with explicit TRUE/FALSE/UNKNOWN evidence. The policy uses a deterministic residual ledger derived from the same public facts available to all time-aware baselines. The proposed objective uses typed success (S), correction (F), and recovery (R) pairs, rather than a single pool called successful demonstrations. The proposed learning advantage is the ledger's inductive bias under matched information and data; it is not an extra verifier, a stronger teacher, or a longer execution budget.

Our evidence establishes constraints on that claim, rather than a learned robot improvement. Strong batch scheduling already solves the measured mechanical timing cells. Explicit rule memory is stronger than the tested symbolic learned history. Independent robot trace reading exposes a gap between geometric contact and load-qualified support. The latest complete collection reveals a force-export contract rejection. These results are retained because they rule out several easy interpretations of agentic improvement.

This research draft contributes (i) a failure-preserving causal contract for event-timed robot experience; (ii) a proposed residual-ledger diffusion objective with typed supervision and actor provenance; and (iii) diagnostic evidence and a frozen, falsifiable comparison against TimeDP, an external timer, and same-pool student-state imitation. The third contribution includes presently missing physical and learning gates. We do not claim submission readiness, chemical success, hardware success, or new VLA superiority.

![Figure: method_contract](figures/method_contract.svg)

Failure-preserving experience contract and proposed policy study. Local verification/recovery retains the original hard failure; a longer learning loop may absorb legal targets into shared weights. The ledger receives no private referee information. Dashed components are unexecuted learning, not an observed policy improvement.

## Related Work
**Physical time and expressive policies.**
Diffusion Policy models action sequences through conditional diffusion [Diffusion Policy: Visuomotor Policy Learning via Action Diffusion (2023)](https://www.roboticsproceedings.org/rss19/p026.html). Chronos explicitly frames robot policies on physical time [Chronos Policy: Learning Robot Policies on Physical Time (2026)](https://arxiv.org/abs/2610.13929v1); neither temporal action conditioning nor the first time-aware VLA is a defensible novelty claim here. OneDP studies fast generation through diffusion distillation [One-Step Diffusion Policy: Fast Visuomotor Policies via Diffusion Distillation (2024)](https://arxiv.org/abs/2410.21257v1). Fast inference and correct physical timing are separate: a fast model can still act from a stale anchor or misqualified endpoint. Our candidate addresses original-event residuals and causal label admission.

**Agents, student states, and distillation.**
GPT-as-Policy investigates numerical actions, hybrid control, and feedback-driven adaptation; its locomotion latency example pauses simulator physics during inference [Systematically Exploring the Capabilities of GPT-6 Astra as Embodied Policies (2026)](https://arxiv.org/abs/2609.38537v1). This motivates reporting the clock on which constraints are scored. DAgger aggregates supervision on policy-visited states [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning (2011)](https://proceedings.mlr.press/v15/ross11a.html). GKD obtains feedback on student-generated sequences [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes (2024)](https://proceedings.iclr.cc/paper_files/paper/2024/hash/5be69a584901a26c521c2b51e40a4c20-Abstract-Conference.html). FA-OPD couples teacher action targets with a reward channel and PPO on student rollouts [Adversarial Dual On-Policy Distillation from Expressive Teacher (2026)](https://arxiv.org/abs/2605.27095v2). Our minimal study is one-round student-state aggregation followed by supervised diffusion training. It is not implemented distributional OPD or RL. Teacher samples support denoising or regression; they do not by themselves define an arbitrary teacher density or KL objective.

**Twins and temporal verification.**
MATTERIX provides chemistry-laboratory twins with multiscale dynamics, rendering, and workflow semantics [MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation (2026)](https://www.nature.com/articles/s43588-025-00924-4). Such infrastructure is a starting point for the measurement problem, not evidence that a new policy succeeded. Bounded temporal operators and trace monitoring are established [Monitoring Temporal Properties of Continuous Signals (2004)](https://link.springer.com/chapter/10.1007/978-3-540-30206-3_12). We use interval and sampled-time semantics; monitoring one trace does not prove exhaustive safety, and sampled dwell does not establish uninterrupted contact without additional assumptions.

The proposed contribution is consequently narrow. It joins immutable physical failure, prefix-limited evidence, typed recovery targets, and a same-information learning test. Each ingredient has close predecessors. The learning claim survives only if the policy exceeds a capable equal-pool student-state baseline and retains that gain in its parameters.

## Causal Event-Time Formulation
### Attempts, clocks, and observations
An attempt is $a=(\mathrm{id},G,B,\mathrm{epoch})$, where $G$ is a task graph and $B$ the remaining resource budget. Its identifier, original anchors, and epoch remain fixed. A reset opens a new attempt; it does not delete the failed one from evaluation.

Let $\tau$ denote native physical/simulation time and $w$ monotonic wall time. We record both. A simulator that pauses during computation can satisfy a native-time deadline while failing a wall-time requirement. Different native epochs are never subtracted. At decision $n$,

$$

\mathcal{H}_n=\{o_i:\mathrm{delivered}(o_i)\preceq(\tau_n,n)\}

$$

contains only observations actually delivered through the public interface. Capture time does not prove delivery. Public inputs include RGB, proprioception, task graph, allowed event packets, and submitted request identities. Private referee poses, force data, future observations, and offline scores are excluded unless separately exposed to every compared arm through the same interface.

An occurrence $e$ has an immutable identifier, onset interval $I_e=[\ell_e,u_e]$, confirmation time, audit-arrival time, and source provenance. A command separately records decision, submit, apply, and effect. An accepted queued request is not an already completed operation. A noncancellable request remains a pending commitment after a plan changes.

### Three-valued temporal evidence
With qualified onset intervals, event $j$ occurs $L$ to $U$ seconds after event $e$ when

$$

I_j-I_e=[\ell_j-u_e,\;u_j-\ell_e]

$$

is contained in $[L,U]$. The relative predicate is TRUE if contained, FALSE if disjoint, and UNKNOWN otherwise. Missing, unqualified, or boundary-straddling evidence remains UNKNOWN. An absolute deadline $D$ is TRUE when $u_j\le D$, FALSE when $\ell_j>D$, and otherwise UNKNOWN. The time origin and deadline belong to the original contract, not a recovery's restart time.

For samples $t_0,\ldots,t_m$, dwell requires every required predicate to be qualified TRUE, span $t_m-t_0\ge d$, and the specified maximum sample gap. The candidate permits at most two nominal ticks between required samples. At regular 240 Hz, 49 samples span 48 intervals, or 0.2 s. This is sampled evidence. Between-sample continuity needs a validated assumption or additional measurement.

Let $q_k(n)\in\{\mathsf{T},\mathsf{F},\mathsf{U}\}$ be clause $k$'s prefix verdict. The task conjunction is FALSE if any required clause is FALSE, TRUE if all are TRUE, and UNKNOWN otherwise. For hard clauses, define

$$

H_{n+1}=H_n\lor\mathbf{1}[\exists k\in K_{\rm hard}:q_k(n+1)=\mathsf{F}].

$$

Once $H_n=1$, the original full task remains FALSE. Later safe handling may be a verified local recovery; it cannot erase a hard miss. Uncertainty alone does not set $H_n$. This is an accounting invariant, not a proof that all physical constraints were sensed.

**Delayed evidence is not delayed occurrence.**
Suppose the physical deadline is $D=3.00$ s. At that time no confirming packet has arrived, so the prefix verdict is $\mathsf{U}$, not $\mathsf{F}$. At 3.20 s an independent audit establishes onset $[2.98,2.99]$ s. The final physical-deadline verdict is $\mathsf{T}$ without changing $D$; the earlier history remains uncertain. In contrast, an onset interval $[3.01,3.02]$ s gives a known physical violation, which a later recovery cannot erase. A separate requirement that a receipt itself arrive by 3.00 s may fail, but must be explicitly declared and is not substituted for the physical deadline. Thus $\tau>D$ plus ``not yet verified'' is insufficient to set $H$.

### Evidence arrival and qualification
A label known at prefix $n$ must use evidence whose audit arrived by that prefix. An offline final verdict may use later evidence but belongs to a separate namespace. Required action provenance must also have arrived: a teacher target is not an applied command, and an unapplied command is not executed recovery. Source hashes, epochs, actors, and endpoint schemas accompany these distinctions.

Physical endpoint qualification is independent. Geometry, contact existence, stationary pose, and command acknowledgement do not establish load-bearing support or robot unloading. Units, signs, coverage, clocks, and raw retention must be valid before a force endpoint is admitted. A rejected getter leaves the endpoint UNKNOWN. A fallback cannot silently replace a frozen predicate.

## Proposed Failure-Preserving Policy Absorption
### A same-information residual ledger
The deterministic ledger is $z_n=\Psi(\mathcal{H}_n,G)$. For original anchor $[\ell_e,u_e]$, the conservative future action interval is

$$

R_{e,n}=[u_e+L-\tau_n,\;\ell_e+U-\tau_n].

$$

Its bounds summarize remaining time for all qualified onset values. An empty interval means the conservative certificate cannot be obtained from these bounds; it does not alone prove physical failure. The ledger encodes known sampled dwell, original failure type, remaining resources, and pending requests. Unavailable values have explicit uncertainty masks, not zero substitutes.

The ledger adds no sensor information. All time-aware arms receive identical public history and facts, the same architecture, and reserved ledger channels. Closest baseline B3 zeros the derived channels while retaining the raw facts from which they could be learned. The hypothesis is an inductive bias in using those facts, not a hidden referee solving the task.

### Typed targets and actor provenance
We separate three forms of experience:

- **S: complete success.** Executed targets with required submit/apply provenance and an independent complete outcome. Future target alignment is explicit; the final outcome is not inserted into an earlier policy history.
- **F: failure-state correction.** A frozen teacher supplies a legal new target at a state actually visited by the designated student collector. Its label is **teacher target, not execution success**. Failed actions are not copied as successful demonstrations.
- **R: executed recovery.** A recovery tail has actual action provenance and an independent local outcome, retaining the original failure and attempt. Teacher takeovers retain privileged actor identity; they are not called student visits.

Admission is type-specific. Unqualified outcome evidence is masked for uses requiring it. Teacher targets can supply correction without proving execution, but do not turn UNKNOWN into a success label. Known failures may serve a separately specified RL objective; unknown reward is never silently zero. The current logger has a single-actor header; a complete mixed-actor takeover registry remains an implementation gate.

### Diffusion objective and collector
Let $U^\star$ be an admitted action chunk aligned to desired execution times $T^{\rm exec}$. At diffusion step $k$, we propose

$$
\begin{aligned}

\mathcal{L}(\theta)=\mathbb{E}_{\mathcal{D}}\big[&m\,\|\epsilon-\epsilon_\theta(\alpha_kU^\star+\sigma_k\epsilon,\\
&k,h,G,z,T^{\rm exec})\|_2^2\big],

\end{aligned}
$$

where $\epsilon\sim\mathcal{N}(0,I)$, diffusion step $k$ follows the shared training schedule, and $m$ is a type-specific mask. Admitted pairs have identical per-pair weights across arms. This is a proposed TimeDP instantiation; no new trained TimeDP implementation is claimed.

The collector first selects train-only $U_0$: 512 distinct success state/target pairs, and trains common $\theta_0$. A fixed student then visits states and obtains correction queries or executed recovery tails. Each arm receives identical frozen teacher payload and shared pool. This is one-round state aggregation, not continuous rollout/update OPD. A later distributional distillation stage needs a specified objective, rollout distribution, and estimator. Offline RL and online RL are separate future studies, not evidence obtained by naming pipeline stages.

The candidate must exceed B3 under equal information and caps, then retain the gain without an online teacher or cross-session context. Current-episode history remains available. An external-timer-only gain supports scheduling; explicit-memory gains support context management. Gains that disappear after context removal do not establish parameter absorption.

## Existing Diagnostic Evidence

All results here are existing measurements with distinct scopes. None compares the proposed learned method. They determine which controls and qualification gates the learning study needs.

![Figure: negative_controls](figures/negative_controls.svg)

Inherited negative controls. (A) Four controllers tie on primary timing and original mechanism predicates across eight known cells each, without force or full strict-hold acceptance. (B) Native and wall-clock scores differ when physics pauses during real CPU work. (C) Explicit memory exceeds symbolic learned-history recipes. Populations and units differ; these are not pooled as learned-policy results.

### Strong scheduling and two clocks
In a MuJoCo three-rotor component, strong batch scheduling, guarded hierarchical control, event-resource EDF, and interval MPC each achieve primary timing and the original mechanism subset TRUE on 8/8 known cells. These 32 paired native episodes do not show that an agentic controller is necessary. Paired states and independent reading do not create unseen task compositions.

The clock study uses two responses, three actual CPU workloads, three repeats, and three arms: 54 runs and 21,654 native samples. Paused physics yields native TRUE on 18/18 but wall FALSE on 9/18. Continuous blocking yields native and wall TRUE on 9/18. Preinstalled execution yields both on 18/18. These are CPU workloads, not LLM calls, hardware certification, or chemistry. Native and wall outcomes must be reported separately.

### Symbolic adaptation and explicit memory
The inherited adaptation matrix has 69,120 evaluation rows from repeated shared groups, mapping shifts, seeds, and evaluations, not independent tasks. Across the last three retained-history evaluations, learned history scores 23.70%, expert history 29.04%, and explicit rule memory 100%. Cleared learned context scores zero in this fixed split because majority routing cannot resolve the heldout mapping; this is not a general impossibility result for in-context learning.

Both fitted recipes use 9,216 supervised trials. Collection costs differ: 27,033 versus 33,984 environment actions, with 2,313 extra expert-preparation attempts. This symbolic development comparison is not a same-cost physical robot result. It requires an explicit-memory control and separate first-attempt, context-adaptation, and parameter-retention measurements.

### Trace integrity is not physical qualification
Older robot diagnostics have 20 trajectories, including 16 already-seen test configurations; complete timing plus strict hold passes on 0/20. These old failures remain unchanged. One ARIS episode verifies 14,007 task states, 13,995 submitted/applied requests, a 12-request FIFO tail, 28,016 physical snapshots, and 177 RGB/depth captures. Strict sampled hold is FALSE at 11 indices (8028--8038); load readiness is UNKNOWN. Two post-result reader-schema repairs are retained before the eventual base pass. They are neither prospective validation nor additional native episodes. Offline camera capture does not prove student delivery.

The new force-instrumentation batch has two attempts, M0 and M1 (the force-instrumentation table). M0 reaches a 700.055 s child timeout, exits by termination, and lacks a complete result. This is a collection-budget failure, not a diagnosis that the robot missed a physical deadline. Its partial export is not a complete force score.

M1 completes in 842.628 s with exit code zero. Its reader, frozen before execution, runs once for 34.012 s and verifies basic task/FIFO/pose/camera integrity, but rejects the force-detail contract. The first rejection is row 9,657, POST step 3,597, callback 4,828, native time 20.125001 s: the producer reports `NEGATIVE_NORMAL_SCALAR`. The offending raw scalar and point range were not exported. Magnitude, sign convention, and cause cannot be reconstructed from that channel. No absolute-value, clipping, or matrix fallback is used. Load, unloading, sign/unit calibration, full wrench coverage, and force-derived training qualification remain UNKNOWN.

M1's old skill subset and primary joint timing/mechanism are TRUE; the copied full mechanical gate and strict hold are FALSE. Seven sampled indices (8028--8034) miss strict hold. This is fixed expert replay in a development-seen setting, not a heldout skill or learned improvement. Across the two attempts there is one complete native collection, zero force-contract passes, and zero new policy admissions. A larger collection wait did not create a learning gain.

| Measurement | M0 | M1 |
|---|---:|---:|
| Started attempts | 1 | 1 |
| Child/cleanup wall (s) | 700.055 | 842.628 |
| Complete native collection | No | Yes |
| Base complete trace accepted | No | Yes |
| Force-detail gate | Not reached | Rejected |
| Strict sampled hold | UNKNOWN | FALSE |
| Load/force qualification | UNKNOWN | UNKNOWN |
| New weights/admissions | 0/0 | 0/0 |

### Interface and CPU cost evidence
The causal capture v04 suite has 98 CPU checks and 13 independent prefix probes. It rejects future audit knowledge, unapplied recovery labels, and confusion between state labels and execution outcomes. These support interfaces, not learned performance.

A selective-copy candidate reduces adapter cost in a four-view Torch CPU fixture, capacity 128, with 0/4/16 effective contact points. Median v0.2-to-v0.3 costs are 3.008 to 0.600, 3.298 to 1.046, and 4.305 to 1.876 ms. Twenty equivalence/refusal checks pass. Native SDK time, GPU transfer, and disk flush are excluded. Native speedup is unknown; v0.3 was not mixed into M1. Performance cannot repair a rejected force contract.

## Predeclared Minimal Learning Study

This study is entirely unexecuted. Its contract is predeclared by hash freezing in this repository, not an OSF or other external formal registration. The frozen design is an auditable candidate, not a materialized dataset or completed experiment. Qualification, source/configuration pins, feasibility, and budget review remain prerequisites.

### Comparisons and ancestral accounting
the proposed-arms table has eight systems but seven learned arms: B2 reuses B1's exact weights. B0 removes explicit time; B1 uses success-only TimeDP; B2 adds a timer; B3 supplies student-state correction/recovery without the derived ledger. M changes only those features relative to B3. Three data ablations remove F or R.

All time-aware arms share train-only $U_0=S_{512}$, selected before F/R collection, and 5,000 ancestral updates. Each then receives 10,000 updates, horizon 8, batch 64, 16 denoising steps, and identical optimizer/backbone. The ancestor-plus-adaptation union is at most 1,024 unique **state/target pairs**, not episodes. M/B3 use S512/F256/R256 with $U_0\subset S$; success-only uses S1024; S+F or S+R uses S768 plus 256. This prevents a hidden ancestral-data advantage. Duplicate F/R targets are not double counted.

| Arm | S | F | R | Ledger | Change |
|---|---:|---:|---:|---|---|
| B0 | 1024 | 0 | 0 | No | No explicit time |
| B1 | 1024 | 0 | 0 | No | TimeDP |
| B2 | 1024 | 0 | 0 | No | External timer |
| B3 | 512 | 256 | 256 | No | Student-state imitation |
| M | 512 | 256 | 256 | Yes | Candidate |
| A0 | 1024 | 0 | 0 | Yes | Success only |
| AF | 768 | 256 | 0 | Yes | No R |
| AR | 768 | 0 | 256 | Yes | No F |

The source pool is S1024/F256/R256. Collection caps are 96 train attempts, 8 validation attempts, 1,536 teacher queries, and 16 queries per attempt. Shortages return `DATA_NOT_READY`; no extra selective collection or uncertainty imputation is allowed. Three seeds yield 21 learned-run equivalents, at most 2 GPU hours each (42 total). Actual common-training reuse is reported; ancestral updates are equally charged.

### Task compositions and outcomes
The candidate split has 12 task graphs: eight train, two validation, and two heldout compositions. It holds out goal/dependency/retry structure, not only lighting or position. Windows, failures, recovery tails, and reset descendants of an original attempt stay in one split. Checkpoints are chosen by validation complete-task TRUE, then known violation, then earliest update. Heldout data never select an arm or threshold.

The small two-graph pilot combines queue latencies 0/0.15/0.45 s with a recoverable 2 mm pre-open alignment offset and an irreversible hard-catch negative control. The latter withholds the opportunity until 50 ms after the original latest window. Late safe recovery cannot become full success. These are proposed settings; new task sources and physical feasibility are not established.

There are 180 main, 108 ablation, and 36 common-$\theta_0$ evaluation attempts (324 total). Including collection, validation, and two preflights caps total attempts at 430. The design has nominal 90 s native and 700 s wall caps per attempt, or an 83.61-hour accounting upper bound. M0/M1 require a separate versioned instrumentation-budget review before execution. M1's diagnostic 1,000 s wait plus termination handling does not change the learning-study cap.

The primary outcome is complete-task TRUE divided by all planned attempts, including hard negatives, crashes, vetoes, and unknowns. We separately report FALSE, UNKNOWN, local recovery, resets, queries, inference/total wall, native elapsed, and remaining resources. Paired cell/seed effects and per-graph rates are primary; a world-cell clustered bootstrap is descriptive. Two heldout graphs do not establish population task generalization.

### Decision rules and extensions
M versus B3 tests novelty. A pilot absolute gain of 0.15 without increased known violations is only a go/no-go for a larger confirmatory study, not a publication threshold. No M--B3 gain means student-state imitation may explain the result. B2-only gain supports scheduling. Loss of gain without retrieval or an online teacher refutes parameter absorption. All-veto/unknown outcomes indicate measurement or feasibility failure.

After qualification, episode 1/2/3/5/10 adaptation should separate context changes, parameter updates, and first-attempt performance. Offline RL, online RL, and actual student-distribution distillation then need distinct objectives, matched budgets, and coverage contracts. The research program is not an already executed training pipeline.

## Limitations and Broader Impact
**Scientific status.**
The method is proposed. New VLA weights, OPD student rollouts, chemistry endpoints, and real-hardware trials are zero in this increment. Mechanical, symbolic, interface, and CPU studies supply different evidence levels. They cannot be pooled into robot learning gains. Strong scheduling and explicit memory already explain measured component successes.

**Physical and causal limits.**
Force qualification is open. M1 omitted the raw scalar needed to explain rejection. A new capture candidate must preserve rejected values and independently justify signed-force semantics before a prospective experiment; it cannot retrospectively repair M1. A source-only capture candidate passes 81 CPU checks and a synthetic rejection/retention probe by preserving finite values in selected effective ranges while still rejecting negative normal scalars; it has no native execution and does not change M1 or qualify force. Backend constraints, external wrenches, unloading, and torque balance remain unknown. Sampled contact does not prove continuous support; offline RGB does not prove online delivery. A mixed-actor takeover registry is not implemented.

**Scope and resources.**
The small pilot's task sources are not ready. Instrumentation can exceed a nominal run budget. Claims about an evolving physical world require measured execution while it evolves; virtual decision charges or paused host computation do not certify hardware latency. The contract does not solve a full physical viability set.

**Impact.**
Calling a missed chemical operation successful could propagate invalid demonstrations or unsafe decisions. Preserving uncertainty and failure identities can reduce this risk but is not a safety guarantee. Physical experiments need separately qualified envelopes and endpoints; twin/model agreement is insufficient. Retained calibration and collection failures make exclusions and costs visible.

## Conclusion
The contract preserves original deadlines and failures while permitting useful correction and recovery targets. A same-information residual ledger makes policy absorption a concrete testable hypothesis. Existing controls and rejected force export require scheduling, memory, trace integrity, and physical qualification to be separated. The next milestone is a qualified equal-budget M--B3 experiment with retained shared-weight improvements; that result is not yet available.

## Evidence Levels and Reproducibility
The source bundle binds inputs in `INPUT_EVIDENCE_PIN_V03.json` and retains the prior pending-M1 checkpoint. Writing reads curated summaries, not large native traces. Source releases, reader failures, and denominators are unchanged. Draft generation adds no native run, GPU experiment, policy update, or hardware measurement.

| Scope | Denominator and boundary |
|---|---|
| Paired32 | 32 development episodes; no heldout learned policy |
| Clock54 | 54 actual CPU trials; not LLM or hardware |
| Adaptation | 69,120 repeated symbolic evaluation rows; not independent tasks |
| ARIS | One episode; base accepted after two schema repairs; strict FALSE/load UNKNOWN |
| M0 | One started attempt, 700.055 s, incomplete collection |
| M1 | One complete collection, 842.628 s, force audit rejected |
| New learning | Zero new VLA weights, student OPD rollouts, or heldout learning evaluations |

## M1 Rejection and Preserved Unknowns
M1 has 15,237 controlled steps: 1,200 warmup, 30 transient, and 14,007 task steps. Its 30,476 force rows comprise one BEGIN, one END, 15,237 PRE, and 15,237 POST. Structural diagnosis after the original rejection inventories 18,438 invalid outer rows and 20,558 rejected normal-point channels. These are status counts, not force magnitudes, independent trials, or all-channel numeric acceptance. The prospective reader's original rejection is retained.

The first rejected object-partition channel uses a precursor-object sensor with balance and both finger actor filters. Its rejected scalar, normal, point range, and effective point data are not saved. The sign cause is unknown and unrecoverable from that channel. Matrix data cannot recreate the omitted point. No support-force/unloading plots or force success curves are presented.

All 425 regular case files are hashed. The 13,995 submit/apply pairs, 12 FIFO tail requests, and 14,007 exact post poses pass base integrity. The 177 RGB/depth captures yield 176 offline future image/action pairs and one terminal image without a target. Source video frames number 168; a final repeated encoded display frame is not another source capture. These records do not establish image delivery to a newly trained student; the capture native clock is also not a certified sensor exposure clock.

Allocated GPU wall upper bounds are 0.19446 h for M0 and 0.23406 h for M1; utilization is unmeasured. M1 retains M0 control, physical deadlines, scheduling, and adapter v0.2. Its child wait increases from 700 to 1,000 s, with at most 30 s termination waits and observed cleanup separately accounted. This is not a hard 1,000 s total wall cap or learned efficiency gain.

## Typed Admission Examples
**Correction.** A student visits a failed alignment state at prefix $n$. A privileged frozen teacher returns a legal target, state hash, query time, and actor. This is F supervision, not proof of application or original success. Querying an undelivered future state is not a valid student visit.
**Recovery.** A reseat is submitted/applied and independently verified at prefix $n'$. The R label becomes known at $n'$ and retains the original failure. A missed hard deadline remains false. Teacher takeover remains privileged execution, not an on-policy student rollout.
**Final scoring.** A late audit can determine an offline final outcome without entering earlier history. Label prefix and target execution time are separate. Unknown evidence masks uses that require it; it is not zero reward, safe success, or physical failure. Original identity links descendants for grouping and denominators.

## Gates Before Learning Execution
Execution requires a versioned source that preserves rejected raw data; justified sign/unit/coverage semantics; prospective readers and independent endpoints; feasible task configurations; a mixed-actor registry when needed; train-only $U_0$ and shared teacher-pool manifests; exact architecture/optimizer pins; and separately frozen budgets informed by instrumentation overhead. Software checks alone cannot close these gates.

Minimum contrasts are M--B3 for the ledger, M--A0/AF/AR for typed data, B1--B2 for a timer, and learned weights versus common $\theta_0$ with online teacher and cross-session context disabled. Complete tasks, known violations, unknowns, and all attempts remain visible. A negative result narrows the claim, rather than triggering unreported threshold or collection changes.

## References

- [Diffusion Policy: Visuomotor Policy Learning via Action Diffusion](https://www.roboticsproceedings.org/rss19/p026.html) (2023).
- [Chronos Policy: Learning Robot Policies on Physical Time](https://arxiv.org/abs/2610.13929v1) (2026).
- [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://proceedings.mlr.press/v15/ross11a.html) (2011).
- [One-Step Diffusion Policy: Fast Visuomotor Policies via Diffusion Distillation](https://arxiv.org/abs/2410.21257v1) (2024).
- [On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes](https://proceedings.iclr.cc/paper_files/paper/2024/hash/5be69a584901a26c521c2b51e40a4c20-Abstract-Conference.html) (2024).
- [MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation](https://www.nature.com/articles/s43588-025-00924-4) (2026).
- [Systematically Exploring the Capabilities of GPT-6 Astra as Embodied Policies](https://arxiv.org/abs/2609.38537v1) (2026).
- [Adversarial Dual On-Policy Distillation from Expressive Teacher](https://arxiv.org/abs/2605.27095v2) (2026).
- [Monitoring Temporal Properties of Continuous Signals](https://link.springer.com/chapter/10.1007/978-3-540-30206-3_12) (2004).

Full primary-source metadata is supplied in [refs.bib](refs.bib) and [citation_support.json](citation_support.json).

