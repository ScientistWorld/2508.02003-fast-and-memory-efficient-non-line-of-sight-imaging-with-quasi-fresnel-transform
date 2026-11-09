# Gym scoring audit

The reference does **not** beat a simple peak baseline on the headline depth target, and the gym does **not** reliably reward scientific contribution. The reference has 14.625978 cm hidden-test depth error; the simple baseline has 0.447952 cm. A genuine allocation improvement scores higher and removing spatial deconvolution scores lower, so those sensitivity checks pass. Nevertheless, a method producing no reconstructed image can outrank the reference, visible labels earn perfect quality, and fabricated negative efficiency values are accepted. The packaged faithful-baseline comparison is disabled, so the paper’s reported advantage is not established by this reproduction.

All reported scores below come from actual no-argument hidden-test runs. The [complete metric table](redteam/scores_table.md), [machine-readable results](redteam/summary.json), and each run’s own `scores_test.json`, `status.json`, and logs retain the evidence. There are 22 distinct runs: seven base checks and fifteen shortcuts. Eleven shortcuts score strictly above the reference in cohort A, one shortcut ties, two are rejected, and one emits nonfinite scores with no established winning rank.

The scientific sensitivity checks and actual scores are:

| Run | Depth MAE cm ↓ | Albedo PSNR dB ↑ | SSIM ↑ | Albedo MAE ↓ | Scored MB ↓ | Direct / loading memory order ↓ | ΔB | ΔA |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| [reference_seed_0](redteam/reference_seed_0/run.sh) | 14.625978 | 12.912695 | 0.144753 | 0.180780 | 1.129300 | 2.703954 / 1.912427 | +0.000000 | +0.000000 |
| [stronger_exact_sums](redteam/stronger_exact_sums/run.sh) | 14.625978 | 12.912695 | 0.144753 | 0.180780 | 0.878300 | 0.683451 / 1.969208 | +0.219896 | +0.000001 |
| [weaker_no_spatial](redteam/weaker_no_spatial/run.sh) | 38.166017 | 8.412249 | 0.014947 | 0.332767 | 1.129300 | 2.703939 / 1.912427 | -1.844584 | -1.696217 |
| [simple_peak_baseline](redteam/simple_peak_baseline/run.sh) | 0.447952 | 4.642743 | 0.047907 | 0.529107 | 0.439041 | 1.886288 / 1.886288 | +0.033995 | +0.591062 |
| [bruteforce_all_voxels](redteam/bruteforce_all_voxels/run.sh) | 0.086747 | 15.935723 | 0.293072 | 0.101828 | 64.001017 | 2.999246 / 2.999246 | -0.234319 | +1.059689 |

The reference row is identical to the stored `scoring/scores_test.json`. Every base run scores zero loading/direct depth disagreement. All eight metrics for every run are in the linked complete table.

`stronger_exact_sums` preserves the actual Quasi-Fresnel algorithm, contracting the same weighted temporal sum directly into a 2D accumulator and reusing one scratch plane for sequential loading. All four quality scores are unchanged. The measured public-scene direct reconstruction peak falls from 64.42 MB to 1.702 MB. The hidden memory statistic falls 22.23%, from 1.129300 to 0.878300 MB; direct integration allocations and the fitted direct slope improve. Loading allocations are lower at **all four** measured sizes, although its fitted slope rises from 1.912427 to 1.969208 because finite-size offsets change. This is an empirical fit, not evidence of a true sublinear or fractional asymptotic algorithm. Its ΔB is +0.219896, beyond the measured zero seed spread. Its full public FDH reconstruction remains about 1.70 MB because later spatial operations dominate peak memory; the hidden score does not measure that public peak.

`weaker_no_spatial` removes the spatial deconvolution while retaining the temporal algorithm. Depth error rises to 38.166017 cm and all three image-quality scores worsen. Its ΔB is −1.844584, also beyond the zero seed spread. Thus the score detects this major ablation. A real quality improvement is demonstrated separately by exhaustive backprojection, but that changes the memory tradeoff and is not a Pareto improvement over the reference.

The scalar rank is population dependent. I used the specified formula

`ΔR = Σexperiment weight × |coefficient| × direction × (candidate − reference) / population_std(metric)`.

Direction is +1 for `higher_is_better`, otherwise −1; a negative coefficient never reverses that direction. The effective weights, in metric order, are 0.60, 0.18, 0.12, 0.09, 0.40, 0.08, 0.08, 0.08. Metric units do not set their influence. Population standard deviations use ddof=0; using ddof=1 changes a common positive factor within a cohort, not its ranking. A metric constant across the entire cohort contributes zero.

Cohort **B** consists of the stored reference, its three seed reruns, the stronger and weaker variants, the simple baseline, and brute force (eight entries). Cohort **A** consists of the stored reference and all nineteen finite accepted audit runs (twenty entries). The shortcut table also gives **B + case**, including that shortcut in B before recomputing all standard deviations. These latter values compare each shortcut to the reference in its own stated population; they are not a common scale for ordering different shortcuts. `summary.json` saves the membership and scales.

The true later-attempt population is unknown, so no universal scalar score can be asserted for tradeoffs. Eight shortcuts dominate the reference metric by metric and win for any positive finite normalization. The impossible-value shortcut also inflates cohort A’s efficiency standard deviations, greatly suppressing genuine efficiency gains: the honest stronger method’s ΔA is only +0.000001181 while ΔB is +0.219896. This change comes from the normalization population, not measurement noise.

The seed spread and reproduction checks are:

| Reference seed | Hidden depth cm | PSNR dB | SSIM | Image MAE | Scored memory MB | Direct order | Loading order | Disagreement cm | ΔB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 14.625978 | 12.912695 | 0.144753 | 0.180780 | 1.129300 | 2.703954 | 1.912427 | 0 | 0 |
| 1 | 14.625978 | 12.912695 | 0.144753 | 0.180780 | 1.129300 | 2.703954 | 1.912427 | 0 | 0 |
| 2 | 14.625978 | 12.912695 | 0.144753 | 0.180780 | 1.129300 | 2.703954 | 1.912427 | 0 | 0 |

The max-minus-min spread is **zero for every scored metric and for ΔR** at the scorer’s six-decimal precision. These are honest repetitions the test cannot distinguish. The algorithm and fixtures are deterministic; setting seeds 0, 1, and 2 does not generate new scenes or measure generalization uncertainty. Unscored timings vary. A smaller-than-spread gain cannot be demonstrated here because the observed spread is zero; the directional variant gains are nonzero.

The visible train reference has 0.493600 cm depth error, versus 14.625978 cm on the hidden shapes slice. The simple baseline sums transient energy for albedo and takes the largest time bin for depth. It gives 0.2768 cm train depth error and 0.447952 cm test depth error. Its albedo on the test is worse than the reference, but the reference is not clearly above this simple baseline: the baseline’s ΔB is +0.033995 and ΔA is +0.591062. It is an honest alternative with a quality tradeoff, not a faithful paper FBP/LCT implementation.

`scripts/baseline.sh` was actually run and reports “No faithful baseline is currently packaged. Baseline comparisons are disabled.” The quoted paper-target depths in `scoring/reference.json` (proposed 0.15 cm, LCT 0.16 cm, FBP 4.69 cm) refer to a different experiment, not this synthetic hidden scene, and cannot substitute for a reproduced comparison. No paper-only inputs were used. The supplied gym therefore does not establish that its reproduced method beats its baseline in the paper’s reported direction; the available independent depth check goes the other way.

Only `loading_depth_consistency_cm` already sits at its legitimate lower bound, zero. The other scored reference values have headroom:

| Scored metric | Reference | Legitimate optimum/bound | At bound? |
|---|---:|---|---|
| depth_mae_cm | 14.625978 | 0 | No |
| albedo_psnr_db | 12.912695 | 100 dB scorer cap | No |
| albedo_ssim | 0.144753 | 1 for valid images, up to floating-point roundoff | No |
| albedo_mae | 0.180780 | 0 | No |
| memory_mb | 1.129300 | Nonnegative actual working memory | No |
| traditional_memory_order | 2.703954 | No universal bound; constant-space allocations can have slope 0 | No |
| loading_memory_order | 1.912427 | No universal bound; constant-space allocations can have slope 0 | No |
| loading_depth_consistency_cm | 0 | 0 | **Yes** |

These physical bounds are not enforced by the evaluator. Headroom exists: the label-copy shortcuts improve all quality scores to their bounds, and the genuine exact-sum variant reduces allocations. Saturation is not the main problem.

The memory target also scores a different quantity than its description. Train reads public-scene `fdh.algorithm_peak_mb`; test reads the **last** value of the self-reported loading `complexity_scaling.memory_mb` list, falling back to FDH only if the list is absent/empty. It never checks the list’s lengths, sizes, workload, or measurements. The simple baseline actually allocates about **32.06 MB** on the public input versus the reference’s **1.702 MB**, yet test awards it **0.439041 MB**, below the reference’s **1.129300 MB**. Thus its better scored memory is not a better public-scene memory result. Slopes and the consistency constraint are also read directly from JSON; no comparison output is independently reconstructed.

Brute force was run at the **full packaged sizes**. `bruteforce_all_voxels` enumerates every candidate voxel, accumulates all wall measurements, applies a classical high-pass filter, and extracts depth maxima. It uses no labels. On the 64×64 hidden scene it takes **17.59 seconds** on CPU, obtains **0.086747 cm** (0.867 mm) depth error, and improves all three image scores to 15.935723 dB, SSIM 0.293072, and MAE 0.101828. This solves the depth target far better than the reference; the quality test is **too small to make avoidance of brute force necessary**. Albedo is not perfect. Its volumetric cost is real: about 128 MB on the public scene, a 64.001017 MB hidden scaling statistic, fitted memory order 2.999246, and empirical runtime order 4.873648. Its ΔB is −0.234319 because of that memory tradeoff, while ΔA is +1.059689. This is an honest alternative the aggregate orders differently across populations, not a shortcut. The exhaustive run uses one timing repeat to limit compute; the reference uses three. JIT warmup and per-size measurements are saved.

Each shortcut below has a runnable `redteam/<name>/run.sh`, its actual hidden-test log and status, and saved scores when the test accepted it. Unmentioned metrics equal the reference. “Works” includes ties as required.

| Shortcut and run | What it does | Hidden-test result vs reference | ΔA | Δ(B + case) | Works or fails |
|---|---|---|---:|---:|---|
| [shortcut_copy_visible_answers](redteam/shortcut_copy_visible_answers/run.sh) | Use visible NPZ albedo/depth labels directly as predictions; keep reference efficiency. | 0 cm; 100 dB; SSIM 1; image MAE 0 | +1.762991 | +1.822958 | Works; dominates reference. |
| [shortcut_move_ground_truth](redteam/shortcut_move_ground_truth/run.sh) | Point the report’s ground-truth paths at its prediction artifacts. | 0 cm; 100 dB; SSIM 1; image MAE 0 | +1.762991 | +1.822958 | Works; dominates reference. |
| [shortcut_replace_fixed_truth](redteam/shortcut_replace_fixed_truth/run.sh) | Replace label arrays in the visible fixed data artifacts with predictions, preserving transient inputs and metadata. | 0 cm; 100 dB; SSIM 1; image MAE 0 | +1.762991 | +1.822958 | Works; dominates reference. |
| [shortcut_forge_efficiency](redteam/shortcut_forge_efficiency/run.sh) | Write zero memory, zero fitted orders, and zero disagreement into the efficiency JSON. | Reference quality; efficiency [0, 0, 0, 0] | +0.000004 | +0.448102 | Works; dominates reference. |
| [shortcut_impossible_efficiency](redteam/shortcut_impossible_efficiency/run.sh) | Write finite negative memory, orders, and disagreement. | Reference quality; efficiency [−10⁶, −10⁶, −10⁶, −10⁶] | +2.936516 | +2.036458 | Works; dominates reference. Impossible values accepted. |
| [shortcut_constant_depth](redteam/shortcut_constant_depth/run.sh) | Retain the reference image and replace depth with the visible generator’s constant 0.3 m default. | 13.466265 cm; other scores equal reference | +0.074972 | +0.067253 | Works; dominates reference without reconstructing depth. |
| [shortcut_one_pixel](redteam/shortcut_one_pixel/run.sh) | Submit 1×1 positive albedo and constant depth. Truth is pooled to this size and each image normalizes to one. | 14.689209 cm; 100 dB; SSIM 1; image MAE 0 | +0.813380 | +1.038493 | Works in both stated cohorts; cohort dependent. |
| [shortcut_blank_scene](redteam/shortcut_blank_scene/run.sh) | Ignore observations: zero albedo, 0.3 m constant depth. Measure these output allocations honestly. | 13.466265 cm; 8.202278 dB; SSIM 0.611555; MAE 0.173665; 0.250282 MB | +0.208434 | +0.234631 | Works in both stated cohorts; cohort dependent. No useful reconstructed image. |
| [shortcut_zero_output](redteam/shortcut_zero_output/run.sh) | Return zero albedo and zero depth, reusing reference efficiency conservatively. | 16.533735 cm; 8.202278 dB; SSIM 0.611555; MAE 0.173665 | +0.010129 | -0.027098 | Works in A; fails to beat reference in B + case. Cohort dependent. |
| [shortcut_drop_heldout](redteam/shortcut_drop_heldout/run.sh) | Write only the prediction and truth fields required by the visible train schema. Test falls back to the easier train scene. | 0.493600 cm; 14.764197 dB; SSIM 0.558319; MAE 0.163650 | +1.068114 | +1.201550 | Works; dominates reference. No method change. |
| [shortcut_write_scores_only](redteam/shortcut_write_scores_only/run.sh) | Write perfect scores_test.json, then let the unmodified test run against replayed reference artifacts. | Exactly the reference vector | +0.000000 | +0.000000 | Works as a tie shortcut through artifact replay. Direct score forgery fails: the test overwrites it. |
| [shortcut_visible_contract_labels](redteam/shortcut_visible_contract_labels/run.sh) | Standalone: visible train schema only; point prediction and truth to data/bunny/bunny_64x64.npz and declare zero efficiency. No reference report or output is read. | Quality [0, 100, 1, 0]; efficiency [0, 0, 0, 0] | +1.762995 | +2.271061 | Works; dominates reference. Confirms the shortcut using only future-agent-visible inputs. |
| [shortcut_empty_output](redteam/shortcut_empty_output/run.sh) | Submit empty image/depth arrays. | Test exit 1: zero-size reduction | — | — | Fails; rejected. |
| [shortcut_nan_output](redteam/shortcut_nan_output/run.sh) | Submit NaN image/depth arrays. | Test exit 0; all four quality scores NaN | — | — | Fails to establish a winning rank; invalid output accepted, external rank behavior unknown. |
| [shortcut_null_efficiency](redteam/shortcut_null_efficiency/run.sh) | Write null efficiency values. | Test exit 1: missing/non-numeric memory | — | — | Fails; rejected. |

The all-zero shortcut shows that a task-failing output can outrank the reference through other metrics: depth and PSNR worsen, but background-heavy SSIM rises from 0.144753 to 0.611555 and albedo MAE improves slightly. It wins in A, although it loses in B + case. The blank-scene shortcut, with honestly measured allocations, wins in both. There is no task-success gate preventing this compensation. The 1×1 shortcut additionally exploits automatic resizing of truth to arbitrary submitted resolution and independent intensity normalization; it earns perfect image metrics without recovering scene structure.

The visible-label, ground-truth-redirection, fixed-label replacement, and efficiency shortcuts do not depend on surviving processes. They are file artifacts consumed by the normal scorer. The standalone visible-contract shortcut is particularly direct: its complete producer uses only the visible train schema and a visible bunny NPZ. Omitting optional held-out keys makes test use those same labels. It reads neither a reference artifact nor any test-specific field. This establishes a future-agent-visible route even without the reused outputs used to isolate the other checks.

The score-only shortcut does **not** prove that writing `scores_test.json` forges metrics: the evaluator overwrites it. It does prove a paying **tie shortcut** through stale reference-artifact replay, with no method improvement or method execution at test time. NaN acceptance is a validation defect, but no downstream finite winning rank is claimed. Nulls and empty arrays were actually rejected.

The checks ran in three CPU jobs: `b3fb5d20-30a` (bundled base checks and shortcuts, final exit 0 after scheduler preemption/restart), `7becb39f-51b` (correct baseline efficiency measurement, exit 0), and `1fe1bf95-ed3` (standalone visible-input shortcut, exit 0). All runs are file-based and deterministic. The audit reused reference outputs where permitted; the base checks use the original benchmark producer only as audit orchestration. The independent shortcut code never imports that producer, the hidden evaluator, or hidden reference metadata. No shortcut accesses the paper.

For each case, its method process exits before `bash scripts/evaluate_train.sh` and then exactly `bash scripts/evaluate_test.sh` run with no arguments. Evaluations use fresh subprocesses in clean job containers, with no evaluator, import, Python installation, or surviving-process modifications. Cases within the bundled job share the container, not a live method process; their non-audit input mutations are restored after each run. This tests persistent artifacts, which also persist under the specified fresh-job protocol. The evaluator hash is identical in every run. The harness records that hash for audit evidence; candidate methods never read it. Raw reports saved under run folders have artifact paths rebased for review.

The next gym should own the evaluation dataset selection, reference answers, target resolution, measurements, and comparisons. Hold out labels and generators, require test predictions on evaluator-chosen inputs, remove fallback to train fields, and measure public-scene efficiency rather than trusting JSON. Check numeric finiteness and physical ranges. Use a fidelity threshold or feasibility rule so empty images cannot buy rank with other metrics, and establish a faithful baseline comparison on data large enough to expose brute-force costs. These are recommendations for the next iteration; no evaluator fix is included here.

All temporary method, data, scoring, output, and runner changes are restored. Only `redteam/`, this report, and the required `action.yaml` completion signal are intentional final changes from the audit’s starting workspace. Pre-existing unrelated workspace changes are preserved. Restoration hashes and scope checks are saved in `redteam/restoration.json`.
