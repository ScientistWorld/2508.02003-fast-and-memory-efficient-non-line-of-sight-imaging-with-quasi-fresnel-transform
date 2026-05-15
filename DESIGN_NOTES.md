# Design Notes - Designer Stage 2

## What I checked

- Read `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. Train invokes `eval/train/score_nlos_train.py` and writes `scoring/scores_train.json`; test invokes `eval/test/score_nlos_test.py` and writes `scoring/scores_test.json`.
- Checked the train/test scorers for method detachment. Both read method-produced `scoring/raw_results.json` plus `scoring/diagnostics.json`; neither imports or reruns `method/`.
- Grepped for train/test cross-imports and found none.
- Checked `scoring/reference.json` for paper-agreement metrics. I found no metric whose objective is matching a published number.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` are absent.
- Ran `bash -n` on both train/test shell entrypoints only.

## Changes made

- Added `albedo_mae` to both train and test quality slices so the visible PSNR target and held-out SSIM target are both constrained by absolute albedo error.
- Fixed `albedo_mae` in `scoring/reference.json`: `higher_is_better` is false and the coefficient is now negative.
- Added the missing `description` field for `depth_mae_cm`.
- Removed wall-clock runtime from the train/test split's nonzero scoring schema. The efficiency experiment now uses `memory_mb` as primary and scores `traditional_memory_order`, `loading_memory_order`, and `loading_depth_consistency_cm` as the anti-shortcut checks.
- Retained `runtime_s` and `traditional_runtime_order` in `scoring/reference.json` with `coefficient: 0.0` so existing artifacts validate without making wall-clock runtime part of the scored objective.
- Changed the held-out efficiency scorer from `runtime_s` / `traditional_runtime_order` to `memory_mb` / `traditional_memory_order` / `loading_depth_consistency_cm`, using existing diagnostics artifacts.

## Split design

The split remains metric-triangulation rather than a new scene partition. That fits this paper because the core claim combines reconstruction quality with low-memory direct reconstruction behavior, and the available public Zaragoza HDF5 measurements do not include 2D albedo/depth ground truth.

Train now exposes depth MAE, albedo PSNR, albedo MAE, low-memory peak memory, and loading memory scaling. Test reuses depth MAE and albedo MAE for calibration, but holds out albedo SSIM, direct-path memory scaling, and loading-vs-direct depth consistency. A method tuned only to the visible quality or low-memory path should have a harder time preserving structure and avoiding hidden direct-path memory growth.

## Runtime concerns for the next iteration

- I did not run the Python evaluators or regenerate score files, per the Designer instructions. The runner should execute both scorers against current artifacts.
- `scoring/reference.json` still preserves `runtime_s` and `traditional_runtime_order` as zero-weight compatibility diagnostics, but no nonzero scored metric uses wall-clock runtime.
- The split still depends on `diagnostics.json` containing `quality_scene.traditional.quality.albedo_mae`, `complexity_scaling.loading.memory_order`, `complexity_scaling.traditional.memory_order`, and `primary_public_scene.loading.consistency_vs_traditional.depth_mae`. The current artifact has these fields; future methods should emit the same diagnostics contract.
- `loading_depth_consistency_cm` may saturate at zero for faithful implementations because loading and direct paths compute the same reconstruction. It remains useful as a constraint metric for methods that break the low-memory path.
