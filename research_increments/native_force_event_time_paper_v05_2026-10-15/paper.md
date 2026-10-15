# Failure-Preserving Experience for Event-Timed Robot Policies: A Causal Contract and a Predeclared Learning Study

Research draft; **MAJOR_OPEN**. Evidence checkpoint: 15 October 2026. The main VLA comparison remains unexecuted; one bounded engineering checkpoint exists. Physics qualification and native student-collector integration remain open.

## Abstract

Robot experience is difficult to label when a physical operation has a deadline, evidence arrives late, and safe recovery follows an irreversible failure. We specify a causal experience contract that separates occurrence, confirmation, audit arrival, and policy delivery; preserves original deadlines and failures; and distinguishes complete success, correction at actual student states, and executed local recovery. A proposed diffusion policy receives a residual-event ledger derived from a finite public prefix, byte-matched for shared training and state-matched offline checks; independent closed-loop evaluation matches information protocols. Existing controls show scheduler ties and context-memory advantages, without testing this learned hypothesis. Lossless capture preserves historically rejected raw values. Five enabled force fixtures pass conditional calibration, while a disabled-contact negative control retains its measurement failure; robot load and unloading qualification remain open. A bounded CPU prototype produces one engineering checkpoint, and a source-bound actor bridge passes software checks with a complete synthetic 13,995-command trace; neither is a new VLA result or real student rollout. The repository-frozen learning comparison matches data ancestry, information, architecture and budgets, and requires gains retained in shared parameters. This draft establishes the accounting contract and current evidence boundaries, not learned robot or chemical superiority.

## Introduction
A laboratory robot may need to stop heating after a specified duration or complete a transfer within a short interval after another operation. These requirements refer to physical events. Sending a command before a deadline does not show that its effect occurred before the deadline. A later recovery can leave the workspace safe while a time-sensitive experiment remains invalid. This distinction matters when robot agents collect their own experience: a trajectory that ends in a desirable state can still contain an irreversible failure that should not become a successful demonstration.

The difficulty is not simply adding a clock to a policy. Temporal conditioning is already an established direction, including physical-time robot policies such as Chronos [Chronos Policy: Learning Robot Policies on Physical Time (2026)](https://arxiv.org/abs/2610.13929v1). Student-state supervision is established by DAgger [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning (2011)](https://proceedings.mlr.press/v15/ross11a.html); robotics-assisted chemistry twins already combine manipulation, process dynamics, and workflow semantics [MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation (2026)](https://www.nature.com/articles/s43588-025-00924-4). Our question concerns their interface: **can experience preserve the identity and causal status of physical failures while still supplying useful correction and recovery targets to one shared policy?**

Three distinctions make this question concrete. First, event onset, confirmation, and the arrival of an independent audit can have different timestamps. Second, the policy's actual history may omit referee measurements that become available only offline. Third, correcting a student at a visited state and observing an executed recovery are different forms of supervision. Ignoring these distinctions can turn future information into apparent adaptation, treat a teacher proposal as a verified action, or make a missed deadline disappear through relabeling.

We specify an event-time contract and a candidate learning mechanism. The contract preserves original attempts, event occurrences, and hard failures, with explicit TRUE/FALSE/UNKNOWN evidence. The policy uses a deterministic residual ledger derived from the same public facts available to all time-aware baselines. The proposed objective uses typed success (S), correction (F), and recovery (R) pairs, rather than a single pool called successful demonstrations. The proposed learning advantage is the ledger's inductive bias under matched information and data; it is not an extra verifier, a stronger teacher, or a longer execution budget.

Our evidence establishes constraints on that claim, rather than a learned robot improvement. Strong batch scheduling already solves the measured mechanical timing cells. Explicit rule memory is stronger than the tested symbolic learned history. Independent robot trace reading exposes a gap between geometric contact and load-qualified support. Lossless capture preserves values rejected by an older rule, and controlled fixtures qualify a scoped contact representation; robot endpoint qualification remains open. One small CPU checkpoint verifies parameter updates; a synthetic actor trace verifies provenance and capacity. These results constrain agentic learning claims without establishing the proposed policy advantage.

This research draft contributes (i) a failure-preserving causal contract for event-timed robot experience; (ii) a proposed residual-ledger diffusion objective with typed supervision and actor provenance; and (iii) diagnostic evidence and a frozen, falsifiable comparison against TimeDP, an external timer, and same-pool student-state imitation. The third contribution includes presently missing physical and learning gates. We do not claim submission readiness, chemical success, hardware success, or new VLA superiority.

![Figure 1: method_contract](figures/method_contract.svg)

Failure-preserving experience contract and proposed policy study. Local verification/recovery retains the original hard failure; a longer learning loop may absorb legal targets into shared weights. The ledger receives no private referee information. Exact prefix equality applies to shared training and state-matched input checks; independent closed-loop trials match protocols and may diverge. Dashed components are unexecuted learning, not an observed policy improvement.

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

\mathcal{H}_n=\{o_i:s_n\le i<e_n,\;\mathrm{delivered}(o_i)\preceq(\tau_n,n)\}

$$

is the declared finite prefix, with packet indices $s_n\le i<e_n$, containing only observations actually delivered through the public interface. For shared frozen training pairs and state-matched offline checks, its bounds, packet identities and digest are byte-identical for M and B3. In independent closed-loop evaluation, each arm has its own causal prefix; matched interfaces do not force histories to remain equal. Capture time does not prove delivery. Public inputs include RGB, proprioception, task graph, the declared decision clock, allowed event packets, and submitted request identities. Private referee poses, force data, future observations, and offline scores are excluded unless separately exposed to every compared arm through the same interface.

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
The deterministic ledger is $z_n=\Psi(\mathcal{H}_n,G,\tau_n)$, where the decision clock is also public to the matched baseline. For original anchor $[\ell_e,u_e]$, the conservative future action interval is

$$

R_{e,n}=[u_e+L-\tau_n,\;\ell_e+U-\tau_n].

$$

Its bounds summarize remaining time for all qualified onset values. An empty interval means the conservative certificate cannot be obtained from these bounds; it does not alone prove physical failure. The ledger encodes known sampled dwell, original failure type, remaining resources, and pending requests. Unavailable values have explicit uncertainty masks, not zero substitutes.

The ledger adds no sensor information. Shared frozen training pairs and state-matched offline or non-actuating shadow checks use byte-identical prefix bounds, length, packet identities and digest. Independent closed-loop evaluation instead pairs the initial world cell and seed, matching interfaces, modalities, history capacity, delivery/latency protocol, teacher, guards, data and budgets. Actions may induce divergent observations; neither arm receives the other's trajectory, forced future observations or hidden future prefixes. Teacher-supervision payloads and guards are matched separately; private teaching inputs never enter $\mathcal{H}_n$. The ledger cannot summarize discarded earlier evidence. All time-aware arms share the same architecture and reserved ledger channels. Closest baseline B3 zeros the derived channels while retaining the raw facts from which they could be learned. For any eligible fixed input and outcome variable $Y$, determinism gives $I(Y;z_n\mid\mathcal{H}_n,G,\tau_n)=0$: the ledger adds no information conditional on its public inputs. This per-input accounting consequence implies neither equal closed-loop histories nor a learning advantage. The hypothesis concerns how a finite trained model uses those facts, rather than a hidden referee solving the task.

### Typed targets and actor provenance
We separate three forms of experience:

- **S: complete success.** Executed targets with required submit/apply provenance and an independent complete outcome. Future target alignment is explicit; the final outcome is not inserted into an earlier policy history.
- **F: failure-state correction.** An independent failure record binds an actual student visit and applied student action; a frozen teacher supplies a legal corrective target at that state. The target is **supervision, not execution success**. An unexecuted teacher proposal alone is not a qualified F pair, and failed actions are not copied as successes.
- **R: executed recovery.** A recovery tail has actual SAFE_LOCAL_RECOVERY application and an independently qualified local outcome, retaining the original failure lineage and deadline. Post-deadline R requires known original full failure. Teacher takeovers retain privileged actor identity; they are not called student visits.

Admission is type-specific. Unqualified outcome evidence is masked for uses requiring it. Teacher targets can supply correction without proving execution, but do not turn UNKNOWN into a success label. Known failures may serve a separately specified RL objective; unknown reward is never silently zero. The source-bound mixed-actor registry and collector bridge separate observations and administrative transitions from actuation. Original-goal commands, safe local recovery, and safety abort have distinct authorization. An actual unsafe or late state must remain recordable. A safety abort under unknown original outcome supplies neither complete success nor an invented recovery label. Native collector integration and physically qualified labels remain gates.

### Diffusion objective and collector
Let $U^\star$ be an admitted action chunk aligned to desired execution times $T^{\rm exec}$. At diffusion step $k$, we propose

$$
\begin{aligned}

\mathcal{L}(\theta)=\mathbb{E}_{\mathcal{D}}\big[&m\,\|\epsilon-\epsilon_\theta(\alpha_kU^\star+\sigma_k\epsilon,\\
&k,h,G,z,T^{\rm exec})\|_2^2\big],

\end{aligned}
$$

where $\epsilon\sim\mathcal{N}(0,I)$, diffusion step $k$ follows the shared training schedule, and $m$ is a type-specific mask. Admitted pairs have identical per-pair weights across arms. This is the proposed shared-policy TimeDP objective; its scientific learning comparison is unexecuted. A separate tiny CPU reconstruction prototype tests image/action alignment and parameter updates without qualified S/F/R admission.

The collector first selects train-only $U_0$: 512 distinct success state/target pairs, and trains common $\theta_0$. A fixed student then visits states and obtains correction queries or executed recovery tails. Each arm receives identical frozen teacher payload and shared pool. This is one-round state aggregation, not continuous rollout/update OPD. A later distributional distillation stage needs a specified objective, rollout distribution, and estimator. Offline RL and online RL are separate future studies, not evidence obtained by naming pipeline stages.

The candidate must exceed B3 under equal information and caps, then retain the gain without an online teacher or cross-session context. Each policy freezes its own delivered prefix at actual inference start and records return, submit, apply and effect separately. Current-episode history remains available. An external-timer-only gain supports scheduling; explicit-memory gains support context management. Gains that disappear after context removal do not establish parameter absorption.

## Existing Diagnostic Evidence

All results here are existing measurements with distinct scopes. None compares the proposed learned method. They determine which controls and qualification gates the learning study needs.

![Figure 2: negative_controls](figures/negative_controls.svg)

Inherited negative controls. (A) Four controllers tie on primary timing and original mechanism predicates across eight known cells each, without force or full strict-hold acceptance. (B) Native and wall-clock scores differ when physics pauses during real CPU work. (C) Explicit memory exceeds symbolic learned-history recipes. Populations and units differ; these are not pooled as learned-policy results.

### Strong scheduling and two clocks
In a MuJoCo three-rotor component, strong batch scheduling, guarded hierarchical control, event-resource EDF, and interval MPC each achieve primary timing and the original mechanism subset TRUE on 8/8 known cells. These 32 paired native episodes do not show that an agentic controller is necessary. Paired states and independent reading do not create unseen task compositions.

The clock study uses two responses, three actual CPU workloads, three repeats, and three arms: 54 runs and 21,654 native samples. Paused physics yields native TRUE on 18/18 but wall FALSE on 9/18. Continuous blocking yields native and wall TRUE on 9/18. Preinstalled execution yields both on 18/18. These are CPU workloads, not LLM calls, hardware certification, or chemistry. Native and wall outcomes must be reported separately.

### Symbolic adaptation and explicit memory
The inherited adaptation matrix has 69,120 evaluation rows from repeated shared groups, mapping shifts, seeds, and evaluations, not independent tasks. Across the last three retained-history evaluations, learned history scores 23.70%, expert history 29.04%, and explicit rule memory 100%. Cleared learned context scores zero in this fixed split because majority routing cannot resolve the heldout mapping; this is not a general impossibility result for in-context learning.

Both fitted recipes use 9,216 supervised trials. Collection costs differ: 27,033 versus 33,984 environment actions, with 2,313 extra expert-preparation attempts. This symbolic development comparison is not a same-cost physical robot result. It requires an explicit-memory control and separate first-attempt, context-adaptation, and parameter-retention measurements.

### Trace integrity is not physical qualification
Older robot diagnostics have 20 trajectories, including 16 already-seen test configurations; complete timing plus strict hold passes on 0/20. These old failures remain unchanged. One ARIS episode verifies 14,007 task states, 13,995 submitted/applied requests, a 12-request FIFO tail, 28,016 physical snapshots, and 177 RGB/depth captures. Strict sampled hold is FALSE at 11 indices (8028--8038); load readiness is UNKNOWN. Two post-result reader-schema repairs are retained before the eventual base pass. They are neither prospective validation nor additional native episodes. Offline camera capture does not prove student delivery.

The closed force-instrumentation family has three attempts, M0, M1 and M2 (Table 1), with separately preserved protocols. M0 reaches a 700.055 s child timeout, exits by termination, and lacks a complete result. This is a collection-budget failure, not a diagnosis that the robot missed a physical deadline. Its partial export is not a complete force score.

M1 completes in 842.628 s with exit code zero. Its reader, frozen before execution, runs once for 34.012 s and verifies basic task/FIFO/pose/camera integrity, but rejects the force-detail contract. The first rejection is row 9,657, POST step 3,597, callback 4,828, native time 20.125001 s: the producer reports `NEGATIVE_NORMAL_SCALAR`. The offending raw scalar and point range were not exported. Magnitude, sign convention, and cause cannot be reconstructed from that channel. No absolute-value, clipping, or matrix fallback is used. Robot load/unloading, full wrench coverage and force-derived training qualification remain UNKNOWN.

M1's old skill subset and primary joint timing/mechanism are TRUE; the copied full mechanical gate and strict hold are FALSE. Seven sampled indices (8028--8034) miss strict hold. This is fixed expert replay in a development-seen setting, not a heldout skill or learned improvement. M0/M1 retain one complete native collection and zero physical-force admissions. M2 adds a separately censored raw-value diagnostic, not another complete task or a repaired M1 outcome. Increasing the collection wait does not create a learning gain.

Closed instrumentation family. Collection terminal state, raw integrity and physics qualification are different outcomes. M2 is censored, not a complete task.

|  | M0 | M1 | M2 |
| --- | --- | --- | --- |
| Started attempts | 1 | 1 | 1 |
| Child wall (s) | 700.055 | 842.628 | 323.640 |
| Collection terminal | Timeout | Complete | Censored |
| Complete task trace | No | Yes | No |
| Retained task samples | Partial | 14,007 | 3,598 |
| Legacy force gate | -- | Rejected | Rejected |
| Strict sampled hold | UNKNOWN | FALSE | Unscored |
| Physics qualification | UNKNOWN | UNKNOWN | UNKNOWN |
| Scientific admissions | 0 | 0 | 0 |

### Interface and CPU cost evidence
The causal capture v04 suite has 98 CPU checks and 13 independent prefix probes. It rejects future audit knowledge, unapplied recovery labels, and confusion between state labels and execution outcomes. These support interfaces, not learned performance. The new collector bridge adds 27 focused checks and 63 adapted inherited checks, plus six independent API probes. Its externally pinned full case header binds actors, policy-weight declarations, original deadline/clock, task graph/split and source pins. An independent reader examines all 58,145 bridge rows and 56,395 registry events in a synthetic 13,995-command case. Each H8$\times$9 output maps to separate 9D commands; queued applications retain the submitting actor across takeover. This is a CPU data-contract test, with zero native installation, model calls or real student rollouts.

A selective-copy candidate reduces adapter cost in a four-view Torch CPU fixture, capacity 128, with 0/4/16 effective contact points. Median v0.2-to-v0.3 costs are 3.008 to 0.600, 3.298 to 1.046, and 4.305 to 1.876 ms. Twenty equivalence/refusal checks pass. Native SDK time, GPU transfer, and disk flush are excluded. Native speedup is unknown; v0.3 was not mixed into M1. Performance cannot repair a rejected force contract.

### Retained raw values and an engineering training check
M2 is a separate, once-run censored measurement case, not a retry of M1. It ends at 323.640 s and preserves 3,598 task steps, 9,658 force rows, 7,198 physical snapshots, 38 RGB/depth captures, and 12 submitted requests never applied before censoring. The first scalar rejected by the historical nonnegative rule is $-1.92397165$ in API-declared force units at task tick 3,597; its signed selected-point sum differs from the normal pair matrix by norm $2.23\times10^{-8}$ in those declared units. This is representation consistency, not independent physics. The versioned primary API example also includes selected negative scalars; omitted dt uses impulse units [Isaac Sim 5.1.0 Core Prims: Contact Force Data API (n.d.)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim.get_contact_force_data). Neither fact licenses a universal absolute-value correction or certifies arbitrary negative measurements. M1's omitted scalar is not retrospectively reconstructed, and both legacy rejection records remain unchanged.

A separately bounded CPU prototype trains once for 200 updates on eight predetermined fit samples from one known episode. Its CNN and diffusion parameters change; fixed-noise MSE decreases from 0.9345 to 0.8687. Reconstructed action error remains large (seven-arm-joint MSE 0.545 rad$^2$). One engineering checkpoint with 51,432 parameters exists; it has no language encoder and is not a full VLA. There is no heldout episode, qualified scientific S/F/R pool, multitask learned-policy comparison, or deployed student rollout.

### Conditional force-fixture calibration
A separately frozen protocol tests freefall, supported contact and three orthogonal interventions with fixed windows, getter and velocity-difference checks, signed representations and paired dt queries. Version 1 retains one after-result timeout and an unknown reader outcome; its other four cases are unexecuted.

Version 2 closes after two cases. C0 passes conditional freefall checks on all 49 fixed samples. C1 exits normally but fails 98 support checks: near-static bodies report zero contact force instead of approximately 0.981 N. Zero-valued dt and reciprocity consistency cannot certify force measurement. Three other cases remain unexecuted after resource refusal. Figure 4 preserves both outcomes.

Version 3 freezes a process-local contact-processing intervention and six cases before execution. All six exit normally and receive one frozen-reader audit each. Five ON fixtures pass conditional calibration; OFF C1 retains its original measurement failure. Enabled support is approximately 0.981 N, rotates with gravity and doubles with mass (Figure 5). Reversing creation order leaves the observed world product unchanged, but its backend ordering mechanism is inconclusive. These results qualify the tested simulator channels, not robot success, hardware traceability or S/F/R admission. Old rejections and unknowns are unchanged.

## Predeclared Minimal Learning Study

This study is entirely unexecuted. Its contract is predeclared by hash freezing in this repository, not an OSF or other external formal registration. The frozen design is an auditable candidate, not a materialized dataset or completed experiment. Qualification, source/configuration pins, feasibility, and budget review remain prerequisites.

### Comparisons and ancestral accounting
Table 2 has eight systems but seven learned arms: B2 reuses B1's exact weights. B0 removes explicit time; B1 uses success-only TimeDP; B2 adds a timer; B3 supplies student-state correction/recovery without the derived ledger. M changes only those features relative to B3. Three data ablations remove F or R.

All time-aware arms share train-only $U_0=S_{512}$, selected before F/R collection, and 5,000 ancestral updates. Each then receives 10,000 updates, horizon 8, batch 64, 16 denoising steps, and identical optimizer/backbone. The ancestor-plus-adaptation union is at most 1,024 unique **state/target pairs**, not episodes. M/B3 use S512/F256/R256 with $U_0\subset S$; success-only uses S1024; S+F or S+R uses S768 plus 256. This prevents a hidden ancestral-data advantage. Duplicate F/R targets are not double counted.

Unexecuted arms. Counts are unique state/target pairs including ancestral S512, not episodes.

| Arm | S | F | R | Ledger | Change |
| --- | --- | --- | --- | --- | --- |
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
The candidate split has 12 task graphs: eight train, two validation, and two heldout compositions. It holds out goal/dependency/retry structure, not only lighting or position. Windows, failures, recovery tails, and reset descendants of an original attempt stay in one split. Checkpoint selection is fixed before execution: use the final 10,000 adaptation updates after the shared 5,000-update ancestor. The eight validation attempts qualify the collector only; they do not select among 21 learned-run equivalents. Reaching the two-GPU-hour cap before the fixed update count is INCOMPLETE, with no selective extension. Heldout data never select an arm or threshold.

The small two-graph pilot combines queue latencies 0/0.15/0.45 s with a recoverable 2 mm pre-open alignment offset and an irreversible hard-catch negative control. The latter withholds the opportunity until 50 ms after the original latest window. Half the 12 evaluation cells are irreversible negatives, so pooled success has a 50% ceiling. Recoverable and irreversible strata are reported alongside the full denominator. Late safe recovery cannot become full success. These are proposed settings; new task sources and physical feasibility are not established.

There are 180 main, 108 ablation, and 36 common-$\theta_0$ evaluation attempts (324 total). Including collection, validation, and two preflights caps total attempts at 430. The design has nominal 90 s native and 700 s wall caps per attempt, or an 83.61-hour accounting upper bound. Measurement instrumentation has a separate versioned budget namespace; its completed runs do not spend or enlarge this unexecuted learning-study budget. M1's diagnostic 1,000 s wait plus termination handling does not change the learning-study cap.

The primary outcome is complete-task TRUE divided by all planned attempts, including hard negatives, crashes, vetoes, and unknowns. We separately report FALSE, UNKNOWN, local recovery, resets, queries, inference/total wall, native elapsed, and remaining resources. Paired cell/seed effects compare independent attempts, allowing policy-induced history divergence; same-state checks are reported separately. Per-graph rates are primary; a world-cell clustered bootstrap is descriptive. Two heldout graphs do not establish population task generalization.

### Decision rules and extensions
M versus B3 tests novelty. A pilot pooled absolute gain of 0.15 without increased known violations is only a go/no-go for a larger confirmatory study, not a publication threshold. With half the cells irreversible, this requires a 0.30 gain in the recoverable stratum; it must not be represented as a requirement over unconstrained successes. No M--B3 gain means student-state imitation may explain the result. B2-only gain supports scheduling. Loss of gain without retrieval or an online teacher refutes parameter absorption. All-veto/unknown outcomes indicate measurement or feasibility failure.

After qualification, episode 1/2/3/5/10 adaptation should separate context changes, parameter updates, and first-attempt performance. Offline RL, online RL, and actual student-distribution distillation then need distinct objectives, matched budgets, and coverage contracts. The research program is not an already executed training pipeline.

## Limitations and Broader Impact
**Scientific status.**
The method is proposed. The main learned VLA comparison, real OPD student rollouts, chemistry endpoints, and real-hardware trials are unexecuted. The single P0 engineering checkpoint is reported separately; project-wide absence of all trained weights is not claimed. Mechanical, symbolic, interface, and CPU studies supply different evidence levels. They cannot be pooled into robot learning gains. Strong scheduling and explicit memory already explain measured component successes.

**Physical and causal limits.**
Force qualification is open. M1 omitted the scalar needed to explain its rejection; M2 preserves new raw data without reconstructing M1. A signed selected-point decoder passes scoped CPU checks, and primary API examples disprove a universal nonnegative-scalar format rule. Enabled v03 fixtures pass conditional representation, gravity/frame and mass checks; disabled processing retains a measurement rejection. Robot-specific force endpoints, hardware SI traceability, backend constraints, unloading and torque balance remain unqualified. Archived legacy rejections remain unchanged. Sampled contact does not prove continuous support; offline RGB does not prove online delivery. The mixed-actor bridge has software evidence and retained synthetic events, but no actual native student collector.

**Scope and resources.**
The small pilot's task sources are not ready. Instrumentation can exceed a nominal run budget. Claims about an evolving physical world require measured execution while it evolves; virtual decision charges or paused host computation do not certify hardware latency. The contract does not solve a full physical viability set.

**Impact.**
Calling a missed chemical operation successful could propagate invalid demonstrations or unsafe decisions. Preserving uncertainty and failure identities can reduce this risk but is not a safety guarantee. Physical experiments need separately qualified envelopes and endpoints; twin/model agreement is insufficient. Retained calibration and collection failures make exclusions and costs visible.

## Conclusion
The contract preserves original deadlines and failures while permitting useful correction and recovery targets. A same-information residual ledger makes policy absorption a concrete testable hypothesis. Existing controls and rejected force export require scheduling, memory, trace integrity, and physical qualification to be separated. The next milestone is a qualified equal-budget M--B3 experiment with retained shared-weight improvements; that result is not yet available.

## Evidence Levels and Reproducibility
The current source bundle binds its inputs in `INPUT_EVIDENCE_PIN_V05.json`. A prospective operational clarification distinguishes byte-identical shared training/state-matched checks from protocol-matched independent closed-loop attempts. It predates the unexecuted learning comparison and changes no number, budget or sealed D01 record. The sealed v04 manuscript and earlier v03 source provenance remain under `parent_provenance`; their hashes identify the parent, not the revised manuscript. Writing reads curated summaries, not large native traces. Source releases, reader failures, and denominators are unchanged. Draft generation adds no native run, GPU experiment, policy update, or hardware measurement.

Scope accounting. Rows, frames, repeated evaluations, and reset descendants are not independent successful tasks.

| Unit | Denominator | Interpretation |
| --- | --- | --- |
| Paired32 | Four controllers by eight known mechanical cells | Development equality; no heldout learned policy |
| Clock54 | Two responses by three CPU loads by three repeats by three arms | Actual CPU workloads; neither LLM calls nor hardware certification |
| Adaptation | 69,120 repeated rows; 256 shared groups, two mapping shifts, three seeds | Symbolic negative control; memory 100%, not physical robot learning |
| ARIS | One episode; 14,007 task states, 28,016 physical rows, 177RGB/depth captures | Base accepted after two post-result schema repairs; strict false, load unknown |
| M0 | One started attempt, 700.055s wall; no complete result | Retained budget failure; no complete force score |
| M1 | One complete collection, 842.628s wall; one prospective reader execution | Base integrity accepted; legacy force rejected; qualification unknown |
| M2 | One censored native case, 323.640s wall; 3,598 task samples | Selected raw preserved; legacy rejection unchanged; no complete score |
| P0 | One CPU training run, 200 updates, eight tiny fit samples | One engineering checkpoint; no language encoder or heldout episode |
| Force v02 | Two native cases; 49 fixed samples per case | Freefall conditional pass; support measurement fails 98 checks; other 3 not run |
| Force v03 | Six native cases; 49 fixed samples per case | Five ON conditional passes; OFF measurement failure retained; no S/F/R |
| G1 bridge | 90 current CPU tests; 6 independent probes; 13,995 synthetic commands | Complete journal audited; no native installation or real student rollout |
| Main learning | Zero main VLA runs/real OPD student rollouts/new heldout learned evaluations | Proposed study only; no method advantage |

## M1 Rejection and Preserved Unknowns
M1 has 15,237 controlled steps: 1,200 warmup, 30 transient, and 14,007 task steps. Its 30,476 force rows comprise one BEGIN, one END, 15,237 PRE, and 15,237 POST. Structural diagnosis after the original rejection inventories 18,438 invalid outer rows and 20,558 rejected normal-point channels. These are status counts, not force magnitudes, independent trials, or all-channel numeric acceptance. The prospective reader's original rejection is retained.

The first rejected object-partition channel uses a precursor-object sensor with balance and both finger actor filters. Its rejected scalar, normal, point range, and effective point data are not saved. The sign cause is unknown and unrecoverable from that channel. Matrix data cannot recreate the omitted point. No M1 support-force/unloading plot or reconstructed M1 force series is presented; later independent calibration is a separate experiment.

All 425 regular case files are hashed. The 13,995 submit/apply pairs, 12 FIFO tail requests, and 14,007 exact post poses pass base integrity. The 177 RGB/depth captures yield 176 offline future image/action pairs and one terminal image without a target. Source video frames number 168; a final repeated encoded display frame is not another source capture. These records do not establish image delivery to a newly trained student; the capture native clock is also not a certified sensor exposure clock.

Allocated GPU wall upper bounds are 0.19446 h for M0 and 0.23406 h for M1; utilization is unmeasured. M1 retains M0 control, physical deadlines, scheduling, and adapter v0.2. Its child wait increases from 700 to 1,000 s, with at most 30 s termination waits and observed cleanup separately accounted. This is not a hard 1,000 s total wall cap or learned efficiency gain.

## M2, P0 and G1 Evidence Boundaries
M2 ends after 3,598 task steps and 4,828 controlled steps including warmup and restore. It preserves 9,658 force rows, 7,198 physical snapshots, 38 camera captures and exact post poses. Of 3,598 submitted commands, 3,586 are APPLIED and 12 remain pending at censoring; unsubmitted future commands are not executed actions. The first retained negative value occurs at POST task tick 3,597, absolute callback 4,828. Its 20.125001 s timestamp includes the preceding warmup/restore origin and is not task elapsed time. The selected signed sum and normal matrix agree numerically within the declared interface, not against an independent physical standard. Original full task, robot unload/load and chemistry outcomes are unscored or unknown.

P0 uses a source-bound partition of a single known native episode. Image/proprioception and future actual 9D APPLIED targets are aligned; normalizers use the fit block only. Training is restricted to eight predetermined examples and 200 updates, with one checkpoint and changed parameter digests. Fixed-noise MSE changes from 0.9344666 to 0.8687106; reconstructed seven-joint MSE is 0.5451352 rad$^2$ and two-gripper MSE is 0.00019793 m$^2$. Later segments from that same episode are descriptive, not an unseen-episode test. Behavior reconstruction requires action provenance, but does not qualify scientific success, failure or recovery. Figure 3 shows the complete retained training trace and fixed-noise probe.

![Figure 3: p0_actual_cpu_training](figures/p0_actual_cpu_training.svg)

One engineering CPU training run. (a) All 200 unsmoothed optimizer losses. (b) The same fixed noise and eight fit examples at initialization and the final checkpoint. These are two views of one run, not statistical replicates or a heldout test; action reconstruction error remains large. No task success or main-method learning improvement is inferred. The previously sealed figure is included byte for byte.

The G1 bridge binds a full externally pinned case header rather than only source pins or a self-hashed journal. A capacity-only successor retains the sealed v02 causal rules while declaring an explicit event cap. The synthetic long case allows 56,479 registry events; its actual 56,395 events and 58,145 bridge rows include 13,995 proposal/submit/APPLIED triples, 14,008 states, 177 packets and visits, 16 teacher-target fixture rows and 32 actor transitions. The remaining 84 declared slots are reserved capacity, not additional executed actions. H8$\times$9 maps to 1,750 chunks, with only three valid rows in the last chunk; padding is never submitted.

The first CPU build/replay retained only full-content hashes and edge samples. A reviewer-required deterministic trace reconstruction subsequently retains both complete journals with exact equality to those original hashes; the first result and retention gap remain recorded. There is one original semantic replay and one trace reconstruction, not two scientific/native attempts. Independent stream inspection verifies complete row correspondence and source/owner/FIFO lineage. These records are invented CPU fixtures and contain no actual student policy rollout or teacher-model call. The serialized CPU writer does not validate inference-start input history, inference-end arrival, and current-state submission while physics continues. Native integration must retain those clocks and the actual model input prefix separately; regenerating a later prefix is not evidence of the earlier input. A separate prefix-clock v02 component has 24 author CPU checks and eight independent probes. It guards accepted-clock high-water marks and event-chain writes, preserving them on rejection. It is not integrated with the G1 asynchronous proposal schema. The inherited ticket-return registry can mutate before a later rejected event; whole-API atomicity, actual concurrency and physical clock authenticity are not established.

## Typed Admission Examples
**Correction.** A student visits a failed alignment state at prefix $n$. A privileged frozen teacher returns a legal target, state hash, query time, and actor. F admission additionally requires an independent failure record bound to the actual visited state and APPLIED student action. The corrective target is supervision, not proof of its own application or original success. Querying an undelivered future state is not a valid student visit.
**Recovery.** A reseat is submitted/applied and independently verified at prefix $n'$. The R label becomes known at $n'$ and retains the original failure. A missed hard deadline remains false. Teacher takeover remains privileged execution, not an on-policy student rollout.
**Final scoring.** A late audit can determine an offline final outcome without entering earlier history. Label prefix and target execution time are separate. Unknown evidence masks uses that require it; it is not zero reward, safe success, or physical failure. Original identity links descendants for grouping and denominators.

## Calibration and Shutdown Accounting
The first force-fixture version retains one started C0 case with a written result but a 300.022 s child timeout and exit $-15$. Its prospectively frozen reader rejects the lifecycle boundary before admitting a calibrated series; physics remains unknown. The other four v01 cases are unexecuted. This namespace is separate from the closed M0/M1/M2 collection family and the unexecuted learning study.

A once-run shutdown diagnostic also times out: 300.032495 s, exit $-15$. Its independent audit passes only boundary capture, not physics. Eleven stack dumps place SDK close inside USD stage close, with an Isaac Lab stop callback rendering while the application is not playing. Complete RESULT fsync occurs at 129.116 s and close entry at 129.118 s. Observed Replicator state is STOPPED, queued count zero, triggers empty; a pending Replicator job or incomplete result write is not the observed cause.

Version 2 uses a separately frozen source/reader and releases the owned public simulation context only after complete END/RESULT, before default application close. Two native cases exit zero with empty owned process groups. C0 takes 125.464556 s (allocated-wall upper bound 0.0348513 GPU h) and 120 controlled steps; C1 takes 16.208581 s and 1,049 steps. Different GPU selection and a warm cache preclude a speedup claim. Both retain nine lifecycle markers and the stop-subscription handle changing from present to None. No AFTER_APP_CLOSE marker is emitted: a Python-level return from default close and fresh clocks after context release remain unknown. These observations establish normal process termination for these cases, not a general SDK fix.

C0's once-run independent reader returns conditional fixture pass. All 49 fixed POST ticks 71--119 span 0.2 s; maximum acceleration errors are $1.14441\times10^{-5}$ m/s$^2$ for the getter and $1.04904\times10^{-5}$ m/s$^2$ for velocity differences. Reported contact normal force is zero. This checks gravity/inertia with a zero signal; it does not establish nonzero contact sign, units, full constraint coverage, robot loading or hardware traceability.

C1's once-run reader returns conditional fixture measurement failure. At fixed POST ticks 1000--1048, both getter and velocity-difference Newton residuals fail at every one of 49 samples: 98 failed checks in one epoch, not 98 trials. The near-static supported body reports zero contact net and pair force and zero selected counts; its declared mass/gravity imply about 0.981 N support. Zero-valued signed, reciprocal and dt consistency cannot establish that this channel measures physical force. This is a measurement rejection, not evidence that the simulated world violates Newton's law or a robot-failure training label.

![Figure 4: signed_force_calibration_v02](figures/signed_force_calibration_v02.svg)

Observed v02 force-fixture calibration, copied byte for byte from the independent-reader-bound figure. C0 freefall passes conditional gravity checks; C1 supported contact reports zero instead of the declared approximately 0.981 N and fails both Newton checks. The lower panels retain the actual vector residuals against frozen tolerances. Each case has one native epoch and 49 unsmoothed fixed-window samples over 0.2 s; points are not independent trials. No series is invented for the three unexecuted cases. These outcomes do not admit robot S/F/R data or establish force SI traceability.

The first C0 allocation is refused at 23,214 MiB available against a 24,576 MiB gate; a fresh resource choice with 31,723 MiB permits its actual epoch. C2 is refused at 22,675 MiB, and C3/C4 are not launched after the resource stop. Refusals are administrative events, not additional native epochs or failed physical tasks. The closed v02 batch has two actual epochs, 1,169 controlled steps and three unexecuted cases; with v01 its calibration family has three actual epochs. Shutdown diagnosis and the three M0/M1/M2 collections remain separate.

Pinned installed source sets `/physics/disableContactProcessing=True` in the simulation context (line 705); ContactSensor initialization sets it false (line 79). Direct tensor views bypass that sensor initialization. Version 2 did not capture the runtime setting, so its source inspection alone cannot identify the actual causal state. Version 3 freezes a worker-local intervention after context construction and before reset: OFF requests true, ON requests false. Actual Boolean readbacks are checked throughout all controlled RAW steps and lifecycle boundaries; source inspection is not substituted for observed values.

### Observed v03 intervention
The separately source/reader-frozen v03 batch executes OFF C1 followed by ON C0--C4. Its six distinct native epochs and six once-run independent readers finish normally; all 5,365 controlled steps are retained. The five positive cases pass conditional fixture calibration under unchanged numeric tolerances and windows. Disabled-processing C1 reports zero support and fails both Newton checks at all 49 samples. Its original FAIL is preserved as an expected negative-control outcome, not turned into positive force qualification or a failed robot trajectory. Figure 5 shows all six actual series, each one epoch and 49 fixed-window samples; no point is an independent trial.

Enabled C1 has mean pair world force approximately $(0,0,0.981000033)$ N. Rotation C2 moves it to approximately $(0.980999989,0,0)$ N; doubled mass C4 gives world $z$ force 1.962000061 N, a C4/C1 ratio 1.999999995. These are finite conditional simulator tests, not hardware SI calibration. C1 contains selected signed values as low as $-0.320711970$ N and up to four negative points. The signed-vector sum agrees with its filtered matrix within $3.57628\times10^{-7}$ N, and the paired dt impulse check has maximum error $1.03998\times10^{-9}$ N s. This supports preserving signed scalar/normal products in the tested channels, not taking absolute values or repairing M1's missing raw record.

C3 reproduces C1's world product under reversed scene creation, but complete backend shape order is unobserved; its ordering mechanism remains inconclusive. Output equality does not prove internal order changed. Robot load/unload, torque, chemical endpoints, full constraints and hardware SI remain open. All v03 cases lack AFTER_APP_CLOSE: Python return is unknown despite exit zero. Cache/resource histories preclude speedup claims.

![Figure 5: signed_force_calibration_v03_paper](figures/signed_force_calibration_v03_paper.svg)

Observed v03 conditional calibration, with the exact reader-bound samples and a paper-specific layout. Five enabled fixtures pass their frozen checks; disabled processing retains zero support and 98 failed Newton checks. Rotation changes the measured world-force direction; doubled mass doubles support. Creation-order output equality does not establish the unobserved backend ordering mechanism. Each panel contains all 49 unsmoothed samples from one distinct native epoch over its fixed 0.2 s window. These six cases are not statistical replicates, robot successes or learned-policy evaluations. Frozen tolerances are retained and no predecessor outcome is rewritten; the original six-panel figure and the layout-only source diff are preserved.

The v03 cap is exhausted at six actual epochs and 5,365 controlled steps. A retained pre-launch resource refusal is administrative, not a seventh epoch. Calibration-family actual count is nine: one failed v01 case, two v02 cases and six v03 cases. The separate shutdown diagnostic is one additional epoch; this calibration/shutdown phase totals ten epochs and 6,774 controlled steps, with no model call or training. The older M0/M1/M2 namespace remains three closed attempts. Conditional calibration admits zero robot S/F/R pairs and does not execute M--B3. Publication does not authorize additional calibration or alter these denominators.

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
- [Isaac Sim 5.1.0 Core Prims: Contact Force Data API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html#isaacsim.core.prims.RigidPrim.get_contact_force_data) (n.d.).

Primary-source metadata is supplied in [refs.bib](refs.bib) and [citation_support.json](citation_support.json).

