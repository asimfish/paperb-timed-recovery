2026-10-19: [Native asynchronous loop](native-loop.html). AsyncBridge v0.2 reserves worst-case serialized bytes for every admitted ticket and CASE_END; the retained v0.1 counterexample (start admitted at 5,260 B under 5,360 B, CASE_END refused) was re-run, and v0.2 passes 41 ported + 16 capacity tests (±1-byte boundaries, 6,189-cap sweep, forged-journal replay). One native Isaac case (1,200 ticks, dt 1/240 s) ran the prior P0 engineering checkpoint in a separate CPU process: 149/149 compute intervals overlapped real physics steps, 99 commands applied exactly at their original ticks, 943 submitted targets were rejected as outside joint limits (no clipping), and an independent reader passed 13/13 checks; native camera video included. An independent adversarial review found no reservation violation (2,560 fuzz runs, 31.5k reserved events) but confirmed type/replay-strictness defects and a README overclaim (only CASE_END is unconditional); v0.3 fixes them and the reviewer's own scripts rerun clean on it. Not task, policy-quality, real-time, force, chemistry or M/B3 evidence.

Earlier dated records follow unchanged.

---

2026-10-16: [Actual asynchronous CPU model case](async-collector.html). One prior P0 engineering-model inference ran in a spawned CPU process (11.324489 ms); two owner observations overlapped computation, and eight output rows received CPU FIFO acknowledgments. No new training, native/GPU/hardware/chemical runs or qualified S/F/R. Final-source independent replay/negative checks: 62 pass; behavior tests span versioned sources. Future serialized-byte and CASE_END reservation remains OPEN, so native readiness is not established. Complete small-case raw logs, existing engineering tensors/checkpoint, author source and independent reader archives are published with their scope. The v05 paper remains byte-identical.

Earlier dated records follow unchanged.

---

<!-- calibration delivery 20261015 -->

2026-10-15: [Current calibration and evidence](calibration.html), [current method](CURRENT_METHOD_cn.md), and [ICML research draft v05](research_increments/native_force_event_time_paper_v05_2026-10-15/paperB_verified_clock_v05.pdf). Six v03 native fixtures ran once each: five processing-on conditional passes and one retained processing-off physical failure. Full bounded raw inputs, independent reports and vector figures are available. The clock component passes scoped software checks; actual asynchronous model collection remains open. Main M/B3 learning is UNTESTED, qualified S/F/R admission is zero, and hardware/chemical endpoints remain uncollected.

The v04 draft and prior evidence remain available as historical artifacts. The operational matched-information clarification distinguishes byte-identical shared training/state-matched inputs from independent closed-loop observations, which may diverge. This is a research draft with major experiments outstanding.

For current local acceptance, run `python3 -B check_current_site.py --root .`. It preserves the inherited checker and corrects its stale five-video count against all 14 unchanged video blocks in parent commit `960d9b9`; all other checks remain active.

Earlier dated records follow unchanged.

---

# Paper B: Physical time contracts and verified recovery

Project website: https://asimfish.github.io/paperb-timed-recovery/

The proposed system combines physical event contracts, agentic verified experience, and shared policy absorption. This repository publishes the curated research website, component reports and ICML development notes. It is not a full raw-data or trained-policy release.

Latest increment: 10,800 native mechanical attempts in three separately frozen cohorts (8,640 main, 1,440 reverse extension, 720 stronger-candidate checkpoint). At the saved attempt-two checkpoint, active public history passes 66/180 versus 57/180 for matched reset, with nine paired repairs and no harms. Passive history has no matched-candidate advantage. Active passes match the earlier declared graph's 66 feasible cases, within that finite privileged graph's scope only.

The restricted main controller retains its charged ten-attempt curves. Reverse faults harm six cases at attempt six; two have apparent temporal TRUE only under an altered reference, so the original contract is FALSE. No neural training, real robot, real-time or chemical endpoint claim follows.

Read [current method](CURRENT_METHOD_cn.md), [full report](research_increments/public_history_adaptation_2026-10-13/README_cn.md), [formulation](research_increments/public_history_adaptation_2026-10-13/FORMULATION_cn.md), [ICML note](research_increments/public_history_adaptation_2026-10-13/paper_preview/note.pdf), and [publication source hashes](SOURCE_MANIFEST.json).

The native research source is maintained separately in asimfish/awesome_memory_chem. The public site keeps every prior report and interactive 432-case toy illustration; the latter is separate from native physical evidence.

Deployment uses GitHub Pages from docs/paperb-site at the repository root. Run `python3 check_site.py --root .` for local links and publication hashes, or add `--base-url https://asimfish.github.io/paperb-timed-recovery/` to compare all deployed HTTP bytes. No third-party research implementations or full reference PDFs are redistributed.

Latest video delivery: [five playable experiment / infrastructure videos](https://asimfish.github.io/paperb-timed-recovery/#experiment_videos). New 2,160 native reference-protection attempts: stable 60/180 vs retained 66/180 and reset 57/180; changed faults 114/360 vs retained 100/360. Protection removes 14 original-reference harms but loses six stable passes. The existing SafeLab Isaac robot example is a failed prior infrastructure trial with zero new Paper B credit. See [execution report](research_increments/video_reference_protection_2026-10-13/README_cn.md).

Supplemental maintained research log: [ARIS experiments, continuous clocks and native instrumentation](https://asimfish.github.io/paperb-timed-recovery/aris-research.html). It retains the negative learning-history result and distinguishes simulation clocks, native acquisition and training admission.
