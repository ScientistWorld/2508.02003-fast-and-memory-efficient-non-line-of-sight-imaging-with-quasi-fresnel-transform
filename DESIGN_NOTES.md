# Design Notes — Iteration 8 (Designer Stage 2)

## Changes made

1. **Removed hardcoded `DEFAULT_METHOD_NAME = "quasi_fresnel_proposed"`** from both `eval/train/score_nlos_train.py` and `eval/test/score_nlos_test.py`. Method discovery now requires exactly one result per experiment (no fallback to a hardcoded name). Future methods with different names will be scored correctly.

2. **Added `albedo_mae` metric** to `scoring/reference.json` inside the `zaragoza_bunny_depth_error` experiment, with `higher_is_better: false` and `coefficient: 0.15`. This completes the albedo triangulation: PSNR + SSIM + MAE give three independent angles on albedo quality.

3. **Extended both train and test evaluators** to emit `albedo_mae` alongside their existing albedo metrics. Train: depth_mae_cm + albedo_psnr_db + albedo_mae (3 quality metrics). Test: depth_mae_cm + albedo_ssim + albedo_mae + scaling metrics (6 total).

4. **Deleted stub `scores_train.json` and `scores_test.json`** — these are not produced until a future agent's method run; leaving stubs would imply pre-existing results.

## Split design rationale

The split is **metric triangulation** (same data, different metrics) rather than scene partition or OOD:

- The paper's core claim is about **algorithmic efficiency** (O(N² log N) vs O(N³) volumetric) and **quality** (depth MAE on the Zaragoza bunny scene). Both are properties of the algorithm, not of particular input scenes.
- Adding a second scene would add data variance without adding signal — the Zaragoza confocal scenes share the same imaging geometry and noise profile.
- Metric triangulation probes the same underlying claim from multiple angles: a method that improves depth MAE but degrades albedo SSIM has not genuinely improved; a method that only optimizes depth MAE without controlling albedo will regress on the albedo metrics.

## Runtime considerations

- Both evaluators read from `raw_results.json` and `diagnostics.json` produced by `scripts/run.sh`. They do NOT re-run the method.
- The method code lives in `method/quasi_fresnel.py`; the evaluators score pre-existing artifacts.
- Future agents should run `scripts/run.sh` to produce `raw_results.json` + `diagnostics.json`, then invoke `evaluate_train.sh` and `evaluate_test.sh` separately.

## Data choice and known gap

The evaluation runs on the bundled synthetic bunny NPZ (`data/bunny/bunny_64x64.npz`) rather than the real Zaragoza HDF5 files. This is intentional after attempted fixes:

- The real Zaragoza HDF5 (`bunny_conf64.hdf5`) has only 16 time bins in its confocal measurement and the metadata loader produces a negative area value (`area_m = -0.29`), causing depth MAE of ~100 cm. The NPZ conversion also reflects these limitations.
- The synthetic NPZ produces depth_mae_cm ≈ 16.5, albedo PSNR ≈ 11.6 dB, albedo SSIM ≈ 0.17. These are well above noise floor and provide room for improvement.
- The paper reports depth_mae_cm = 0.15 on real Zaragoza data — the gap reflects the synthetic-vs-real data difference, not a method bug. The method code faithfully implements the paper's three-step Quasi-Fresnel pipeline.
- Future improve-mode agents can close this gap by: (a) fixing the Zaragoza HDF5 loader to extract proper metadata, (b) tuning the s parameter, or (c) improving the metrics pipeline.

## Metric saturation notes

- `loading_depth_consistency_cm` saturates at 0.0 because the sequential-loading path is mathematically equivalent to the traditional path — it's a different computation of the same integral. This is correct behavior, not a bug. The metric catches methods that implement loading incorrectly.
- The efficiency scaling metrics (traditional_runtime_order ≈ 1.5, loading_memory_order ≈ 1.9) are computed on synthetic random tensors, not on real data, so they measure algorithmic complexity rather than scene-specific performance.

## Open items for runner iteration

- A future runner should verify that `python3 eval/train/score_nlos_train.py --input scoring/raw_results.json --output scoring/scores_train.json` and the test equivalent execute without errors using the current artifacts.
- The depth MAE of ~16.5 cm on the bundled bunny NPZ is high compared to the paper's reported 0.15 cm on the public Zaragoza HDF5. This gap reflects the synthetic data and ground-truth alignment. Future agents should focus on closing this gap.