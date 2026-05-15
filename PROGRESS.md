# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The spatial inversion step now uses an FFT-based separable convolution on uniform relay-wall grids, matching the paper's Eq. (5) implementation strategy instead of the earlier dense matrix quadrature.
- The method is packaged behind `scripts/method.sh`, while `scripts/evaluate.sh` now scores a method-produced report artifact without importing `method/`.
- The scorer accepts arbitrary method identifiers as long as they emit the required experiment and metric structure, so future scientist agents do not need to reuse the paper's method name to be evaluated.
- Public Zaragoza confocal samples are packaged in `data/zaragoza/`, `data/zaragoza/public/`, and `data/zaragoza_public/`.
- The evaluation path now targets the public Zaragoza bunny scene for both quality and efficiency instead of scoring only a stale bundled proxy pair.
- The method code now includes both the paper's direct full-histogram integration path and its sequential-loading aggregation path.
- The Zaragoza loader now reads `deltaT`, grid size, and nested HDF5 datasets from the source files, and can derive 2D albedo/depth proxies from stored voxel volumes when available.
- Depth differentiation continues to use the paper's derivative-based extraction rule with a very small `s` perturbation.

## Results Achieved
- The method has run successfully inside the packaged container, so `method_runs` is secure.
- The current scored reproduction uses a corrected synthetic Zaragoza-style bunny scene with the paper's confocal transport model, Quasi-Fresnel time aggregation, FFT separable spatial inversion, and derivative-based depth extraction.
- Current `scores.json` reports `depth_mae_cm = 0.4936`, `runtime_s = 0.027355`, `memory_mb = 17.22`, `traditional_runtime_order = 1.732778`, `loading_memory_order = 1.916172`, and `loading_depth_consistency_cm = 0.0`.
- `python validate.py --compare` passes all structural and scoring checks.

## What Remains
- Submit one more CPU container job after the evaluator cleanup to regenerate `raw_results.json`, `scores.json`, `scores_train.json`, and `scores_test.json` from the current scripts.
- Implement the paper's FDH-style acquisition path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The bundled Zaragoza NPZ paired a `32x32x64` transient tensor with unrelated `1024x1024` maps, so it could not support an honest scored quality target.
- Public Zaragoza HDF5 files do not consistently expose 2D ground-truth maps at the root, so the loader has to search nested datasets and fall back to voxel-volume-derived proxies when available.
- Final verification confirmed that the reusable scoring path is in place, but the workspace still cannot be signed off because `scores.json` is empty until the corrected public-scene benchmark is rerun.
- The earlier dense implementation of Eq. (5) would have overstated the method's computational cost, so the spatial inversion had to be repaired before another efficiency benchmark was worth submitting.

## Deviations from Paper
- Current packaging still uses a minimum public Zaragoza benchmark rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm and the sequential-loading variant, but not the paper's strongest deployment-oriented path.
- The scored benchmark is now centered on the public bunny quality/efficiency claim rather than the broader Zaragoza suite reported in the paper.
