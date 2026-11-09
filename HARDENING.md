# Hardening report (iteration 11)

**Verdict.** In the audit, better results now score higher, worse ones lower, and every major red-team shortcut fails or ties.

The old test let the method choose its own ground-truth files, read memory numbers the method wrote, and fell back to visible data. It also scored on a 64 x 64 scene where the reference lost to a peak-picking baseline and brute force won. The test was rebuilt around one principle: **the evaluator runs each method itself on inputs it controls, and measures everything it scores.** The reference method is unchanged (the paper's three Quasi-Fresnel steps). Two things changed around it:

- its reading of the histogram is now the paper's own sequential-loading variant;
- its free parameter `s` is chosen on the visible train scenes.

Evidence: `redteam/hardening/summary.md` (all tables), `redteam/hardening/scores_{train,test}_cohort.json` (raw scores with per-scene `_details` and `_status`), `redteam/hardening/logs/`, `redteam/hardening/run_audit.sh` (the exact job). Jobs:

| Job | What it did |
|---|---|
| `12a2cee6-5bd` | Exposed the tiny container `/tmp` and memory contamination |
| `0afbe2f3-634` | Intermediate audit at `s = 0.025`, kept in `redteam/hardening/intermediate_s0p025/` |
| `5ef43463-5be` | Final audit; all numbers below |

## What the test is now

- **Method contract.** A method is a command registered in `scoring/methods.json`. For every scene the evaluator runs `<command> --scene <dir> --output <pred.npz>` as a fresh process. It reads only the `albedo` and `depth` arrays. `scripts/evaluate_test.sh` (no arguments) scores every registered method, and so does `scripts/evaluate_train.sh`, through the same interface.
- **Hidden test inputs and answers live only in `eval/test/`.**
  - The 12 hidden scenes are 10 at 256² and 2 at 512². Each is a surface object at 1 m x 1 m wall scale with 512 bins of 1.5 mm one-way distance (3 mm of photon path per bin, as in the paper's Zaragoza setting).
  - They are generated from private seeds and rendered at test time with a confocal three-bounce model: Lambertian wall and object, inverse-square falloff on each leg, Poisson shot noise.
  - Rendering goes into a scratch directory that is deleted after each scene. Ground truth never leaves the evaluator process.
  - `eval/test/` imports nothing outside itself.
- **Visible train data.** The 6 train scenes (five 256², one 384²) come from the public generator `data/nlos_scenes.py`. Train ground truth is recomputed from that generator, never read from files.
- **Every scored number is recomputed by the evaluator.**
  - Depth MAE is computed on object pixels.
  - Albedo is scored by Pearson correlation and by PSNR after a least-squares scale fit.
  - **Peak memory is measured from `/proc`.** It is the larger of the per-process high-water mark (`VmHWM`) and the summed resident memory of the process tree, sampled every 3 ms. It is reported at 4 MB resolution.
  - Wall-clock time is logged but never scored.
- **Constraints.** A run fails if any of these hold:
  - wrong shape, non-finite values, negative or constant albedo, or depth outside [0, 0.768] m on any scene;
  - more than 256 MB on any scene (the process is killed);
  - more than 300 s on a scene;
  - task not solved: mean depth MAE above half the best-constant-depth error, or mean albedo correlation below 0.2.

  A failed run gets bounded values on every metric: the best-constant depth error, correlation 0, the empty-image PSNR, and 256 MB. Any valid run is at least as good on every metric and strictly better on depth and correlation, so **a failing run can never outrank a valid one** under any positive normalisation.

## Do better results score higher?

ΔR is the specified rank: Σ weight·|coef|·direction·(candidate − reference)/population std. "Honest" means the population of the reference, its rerun, the variants and the baselines. "Valid" means the runs that pass. Paired values are per-scene differences over the 12 hidden scenes, as mean ± standard error.

| Variant (hidden test) | Before (red team, ΔB) | After: depth cm / NCC / PSNR dB / MB | ΔR honest | ΔR valid | Paired |
|---|---:|---|---:|---:|---|
| reference `quasi_fresnel` | 0 | 0.399 / 0.956 / 26.29 / 148 | 0 | 0 | — |
| reference rerun (noise) | 0 (identical) | identical; raw memory 147.4 vs 147.9 MB | 0.000 | 0.000 | memory jitter 0.37 ± 0.11 MB/scene |
| **better:** lean memory (same algorithm, chunked FFT, in-place sums) | +0.220 (`stronger_exact_sums`) | 0.399 / 0.956 / 26.29 / **68** | **+0.488** | +0.809 | memory +29 ± 7 MB/scene (+82 MB at the 512² peak) |
| **better:** depth smoothing (albedo-weighted) | — | **0.257** / 0.956 / 26.29 / 148 | +0.080 | +0.434 | quality ΔR/scene +0.080 ± 0.021 (t = 3.9) |
| **better:** lean + smoothing | — | 0.257 / 0.955 / 26.13 / 64 | **+0.585** | +1.269 | quality t = 3.2, memory +29 MB/scene |
| tradeoff: average over 0.9s, s, 1.1s | — | 0.238 / 0.959 / 26.39 / 180 | −0.097 | +0.183 | quality t = 4.1, memory −14 MB/scene |
| **weaker:** no spatial deconvolution | −1.845 | fails task gate (3.40 cm) | −3.186 | — | — |
| **weaker:** full-histogram loading (paper's "Traditional") | — (scored identically before) | exceeds 256 MB (804 MB uncapped at 256²) | −3.186 | — | — |
| weaker: `s = 0.025` | — | 0.771 / 0.955 / 25.11 / 148 | −0.258 | −1.220 | quality t = −3.4 |
| weaker: paper's Zaragoza `s = 0.02` | — | fails task gate (1.93 cm) | −3.186 | — | — |
| simple baseline: photon energy + peak bin | +0.034 (beat the reference on depth) | 0.824 / 0.470 / 17.55 / 48 | **−0.402** | −2.308 | quality t = −11.6 |
| volumetric LCT (paper's comparison class) | not runnable | exceeds budget (3.27 GB uncapped at 256²) | −3.186 | — | — |
| brute-force voxel backprojection | −0.234 / +1.060 (solved depth to 0.09 cm) | exceeds budget on the first 512² scene; O(N⁴M) work | −3.186 | — | — |

- **Reruns.** Quality is deterministic, so a rerun of the reference reproduces every quality value exactly. Memory jitters by under 1 MB, which the 4 MB resolution absorbs (the rerun's ΔR is exactly 0).
- **Before vs after.** Before, the honest memory gain was crushed to ΔA = +0.000001 by impossible values in the population, and the evaluator could not see quality-preserving improvements. Now the genuine improvements win by more than the paired noise.
- **Train/test consistency.** The same orderings hold on the visible train split (`summary.md`): lean +0.401, lean + smoothing +0.456, baseline −0.936.

## Major shortcuts: fix and score before / after

"Before" is ΔA / Δ(B + case) from `REDTEAM.md`. "After" is ΔR in the full population from the final hidden-test run. All after-runs are in `redteam/hardening/shortcuts.py` and went through `bash scripts/evaluate_test.sh` with no arguments.

| Red-team shortcut | Before | Fix | Re-run as | After |
|---|---|---|---|---|
| copy visible answers | +1.763 / +1.823 | Test inputs and labels exist only inside `eval/test/` at test time; the method must answer the scene it is given | `sc_copy_train_answer` (outputs a visible train label) | fails: depth 28.7 cm, NCC 0.16 → −2.956 |
| move ground truth (report points GT at predictions) | +1.763 / +1.823 | Evaluator reads no path from the method; ground truth is computed in-process | `sc_gt_redirect` (registry carries GT-path fields) | fails → −2.956 |
| replace fixed truth files | +1.763 / +1.823 | No ground-truth file is read; train truth is regenerated, test truth never written | `sc_overwrite_truth` (overwrites visible truth at run time) | fails → −2.956 |
| visible-contract labels + zero efficiency | +1.763 / +2.271 | Both of the above, and memory is measured | `sc_copy_train_answer`, `sc_forge_memory` | fail / tie |
| forged efficiency (zeros) | +0.000004 / +0.448 | Memory measured by the evaluator from `/proc`; nothing self-reported is read | `sc_forge_memory` (writes 0 / −10⁶ MB and perfect quality claims) | **0.000** (tie: measured 148 MB, its real reconstruction) |
| impossible negative efficiency | +2.937 / +2.036 | Same; measured memory is non-negative and bounded by the budget | `sc_forge_memory` | 0.000 |
| constant depth | +0.075 / +0.067 | Task gate on depth (any constant is ≥ 1× the best-constant error) | `sc_constant_depth` | fails (6.55 cm) → −2.956 |
| 1×1 output | +0.813 / +1.038 | Exact shape required; no resizing of truth | `sc_one_pixel` | fails → −2.956 |
| blank scene / zero output | +0.208 / +0.235; +0.010 / −0.027 | Constant albedo invalid; correlation gate; SSIM on max-normalised images (which rewarded blank backgrounds) removed | `sc_blank`, `sc_zero` | fail → −2.956 |
| drop held-out fields (train fallback) | +1.068 / +1.202 | No fallback: the test always uses hidden scenes, and a missing output fails | `sc_no_output` | fails → −2.956 |
| write `scores_test.json` / stale artifact replay (tie) | 0 / 0 | Evaluator writes scores last; methods run on freshly rendered hidden inputs, so no stale artifact matches | `sc_write_scores` | fails (its answer is blank) → −2.956 |
| NaN output | accepted, NaN scores | Finiteness check | `sc_nan` | fails → −2.956 |
| empty output | evaluator crash | Clean failure | `sc_empty` | fails → −2.956 |
| (new) one-pixel spike to exploit max-normalisation | — | Scale-invariant correlation and LS-aligned PSNR | `sc_spike` | fails (NCC 0.001) → −2.956 |

## Shortcuts left, and why

These are for the separate shortcut grader. `scoring/CONSTRAINTS.md` forbids all of them.

1. **Reading evaluator internals at test time.** Method processes run on the same filesystem as `eval/test/`. A method that deliberately imported `eval/test/test_scenes.py` could regenerate the hidden ground truth. Without a mount sandbox, which the job environment does not offer, this cannot be blocked from inside the evaluator. It requires reading the hidden evaluator's code, so I left it to the grader.
2. **Hiding memory outside the measured tree.** The evaluator does not count work handed to a daemon started beforehand or to a double-forked process that leaves the session, and it can miss a peak within the last ~3 ms before exit. All of these need deliberate evasion; ordinary multi-process methods are counted through the summed tree RSS.
3. **Caching across hidden-test runs.** Hidden inputs exist only during a test run. Caching is therefore impossible before the official run, but a method could replay its own outputs if the hidden test were rerun in the same workspace.
4. **Visible train labels.** Copying a public train label scores perfectly on that one train scene. This is train only; on test it fails.

## Reference score before and after

- **Before (old metrics):**
  - hidden depth MAE 14.626 cm, PSNR 12.913 dB, SSIM 0.1448, albedo MAE 0.1808;
  - memory 1.129 MB (self-reported), memory orders 2.704 / 1.912, consistency 0 cm.
- **After:**

| Split | Depth MAE | Albedo NCC | Albedo PSNR | Peak memory (raw) | Valid |
|---|---:|---:|---:|---:|---|
| Hidden test | 0.3994 cm | 0.9557 | 26.292 dB | 148 MB (147.9) | yes |
| Visible train | 0.2623 cm | 0.9662 | 27.154 dB | 116 MB (117.2; set by the 384² scan) | yes |

The metric set changed, so the two rows are not directly comparable. The old SSIM, albedo MAE, scaling-order and loading-consistency metrics are gone: they were self-reported, saturated at the bound, or rewarded blank output. `scoring/scores_test.json` and `scores_train.json` were regenerated from the reference runs alone (`s = 0.03`). The simple baseline's visible-scene scores are in `scoring/baseline_scores_train.json`.

## Headroom check

| Scored metric | Reference (test) | Bound | At bound? | Shown reachable |
|---|---:|---|---|---|
| depth_mae_cm | 0.399 | 0 | no | 0.257 with smoothing; 0.07–0.08 with LCT (over budget) |
| albedo_ncc | 0.956 | 1 | no | 0.959 (3-s average) |
| albedo_psnr_db | 26.29 | — | no | 26.39 (3-s average) |
| peak_memory_mb | 148 | ~29 MB (interpreter + numpy floor) | no | 68 (lean), 64 (lean + smoothing) |

The reference sits at the bound of no metric. What I added comes from where the paper's method falls short:

- **Shot noise and Lambertian shading.** At 256², the paper's `s = 0.02` aliases under these and fails the task gate.
- **Larger 512² scans.** The memory score is set by these, and at this size the full histogram alone fills the budget.

Brute force no longer works: exhaustive voxel backprojection, which solved the old test in 18 s, cannot even hold its volume within the budget, and needs O(N⁴M) work.

## Is the paper's claim reproduced in its direction?

- **Memory: yes.** On the same 256² scenes with no budget, the reference peaks at 60 MB. The paper's own full-histogram variant needs 804 MB and volumetric LCT 3,273 MB (54×). On the hidden 512² scans the reference fits in 148 MB, while both volumetric paths are killed at the 256 MB budget.
- **Quality: partly.** The reference beats the simple baseline on every quality metric (paired t = −11.6 for the baseline) and fails no gate. Its albedo correlation and PSNR match LCT (0.966 / 27.0 dB vs 0.954 / 26.5 on `train_256_a`). **Its depth error does not match the paper's "lowest depth error" claim: LCT reaches 0.07–0.08 cm against the reference's 0.30–0.35 cm on the same two scenes.** The paper reports 0.15 vs 0.16 cm on its noise-free Zaragoza bunny. These paper numbers are kept unchanged in `scoring/reference.json` under `_paper_*` keys as context, not targets.
- **Operating point `s`.** The paper fixes `s` per dataset (0.02 for its noise-free Zaragoza simulations, up to 0.10 for the noisy Stanford captures) and links its range to sampling density and SNR. The reference uses `s = 0.03`, picked by `method/select_s.py` on the visible train scenes from {0.02, 0.025, 0.03, 0.035, 0.04, 0.05}; the result is recorded in `method/qf_params.json`.
  - **Disclosure.** The intermediate job's selection also counted memory, whose sub-MB jitter (divided by a near-zero spread) decided the pick (0.025). I saw that job's hidden-test grid results before correcting the rule to use quality metrics only, the only ones `s` can change. The corrected rule, on train only, ranks 0.03 first (2.776 vs 2.726 for 0.035).
  - On the hidden test, 0.035 and 0.04 score marginally above 0.03 (ΔR +0.05 / +0.04, paired t = 1.5 / 0.8: within noise).

## Weights

The experiment weights stay at 0.6 for reconstruction quality and 0.4 for memory: the paper claims both, and quality is the constraint the memory saving must not break. Within quality:

- depth MAE has |coefficient| 1.0, because it is the paper's only quantitative quality result (Fig. 5);
- albedo correlation 0.6 and aligned PSNR 0.3, because the paper compares albedo images only visually.

Memory has |coefficient| 1.0. All coefficients are positive, and direction comes only from `higher_is_better`.

## What I could not fix, plainly

- The paper's depth advantage over LCT does not reproduce on these noisy scenes (above).
- The paper's literal `s = 0.02` fails the hidden task gate, so the reference uses a train-selected `s`.
- **Memory resolution has edges.** At 4 MB resolution, a method whose raw peak sits within ~0.5 MB of an odd multiple of 2 MB can move by one 4 MB bin between runs. For example, lean scored 68 MB (raw 66.1) and lean + smoothing 64 MB (raw 65.9). The reference sits at 147.9 MB, well inside its bin.
- **Uncapped comparison is small.** The LCT comparison covers only two visible 256² scenes, because LCT needs gigabytes.
- **Validator warning.** `validate.py` prints a heuristic warning that `eval/test/test_scenes.py` "looks detached". It is a false positive: the file renders hidden inputs by design, and `eval/test/test_harness.py` scores the method's predictions. All validator checks pass.
- **Population dependence.** ΔR depends on which attempts form the population. The failure values are bounded, which keeps them from blowing up the spread, but populations with many failed runs still compress valid runs' differences (compare the honest and valid columns).
