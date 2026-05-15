# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The spatial inversion step now uses an FFT-based separable convolution on uniform relay-wall grids, matching the paper's Eq. (5) implementation strategy instead of the earlier dense matrix quadrature.
- The method is packaged behind `scripts/method.sh`, while `scripts/evaluate.sh` now scores a method-produced report artifact without importing `method/`.
- The scorer accepts arbitrary method identifiers as long as they emit the required experiment and metric structure, so future scientist agents do not need to reuse the paper's method name to be evaluated.
- Public Zaragoza confocal samples are packaged in `data/zaragoza/`, `data/zaragoza/public/`, and `data/zaragoza_public/`.
- The evaluation path now separates what can be measured honestly: metric quality on the tracked synthetic Zaragoza-style bunny proxy, and runtime/memory/loading behavior on available public Zaragoza HDF5 measurements.
- The method code now includes both the paper's direct full-histogram integration path and its sequential-loading aggregation path.
- The Zaragoza loader now reads `deltaT`, grid size, and nested HDF5 datasets from the source files, and can derive 2D albedo/depth proxies from stored voxel volumes when available.
- Depth differentiation continues to use the paper's derivative-based extraction rule with a very small `s` perturbation.

## Results Achieved
- The method has run successfully inside the packaged container, so `method_runs` is secure.
- The current scored reproduction uses a corrected synthetic Zaragoza-style bunny scene with the paper's confocal transport model, Quasi-Fresnel time aggregation, FFT separable spatial inversion, and derivative-based depth extraction.
- Previous `scores.json` reports `depth_mae_cm = 0.4936`, `runtime_s = 0.027355`, `memory_mb = 17.22`, `traditional_runtime_order = 1.732778`, `loading_memory_order = 1.916172`, and `loading_depth_consistency_cm = 0.0` from the synthetic proxy path.
- `python validate.py --compare` passes all structural and scoring checks.
- Job `17469bab-217` confirmed that the public Zaragoza HDF5 files load correctly, but do not contain metric 2D albedo/depth ground truth. The benchmark contract has been repaired so those files now support the efficiency side of the claim rather than causing the quality target to fail.

## What Remains
- Submit a CPU container job that runs the split quality/efficiency evaluator and regenerates `raw_results.json`, `scores.json`, `scores_train.json`, and `scores_test.json`.
- Implement the paper's FDH-style acquisition path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The bundled Zaragoza NPZ paired a `32x32x64` transient tensor with unrelated `1024x1024` maps, so it could not support an honest scored quality target.
- Public Zaragoza HDF5 files do not consistently expose 2D ground-truth maps at the root, so the loader has to search nested datasets and fall back to voxel-volume-derived proxies when available.
- Final verification confirmed that the reusable scoring path is in place, but the workspace still cannot be signed off until the corrected split benchmark reruns in the container.
- The earlier dense implementation of Eq. (5) would have overstated the method's computational cost, so the spatial inversion had to be repaired before another efficiency benchmark was worth submitting.
- The previous `core_claim` artifact used the synthetic NPZ benchmark while the scoring descriptions were phrased as public Zaragoza. Job `17469bab-217` then failed because the available public HDF5 files lack the ground truth needed for depth MAE. The scorer now names the synthetic quality proxy explicitly and reserves the public HDF5 files for efficiency metrics.

## Deviations from Paper
- Current packaging still uses a minimum public Zaragoza benchmark rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm and the sequential-loading variant, but not the paper's strongest deployment-oriented path.
- The scored benchmark uses a synthetic Zaragoza-style bunny proxy for metric quality because the public HDF5 measurement files available here lack 2D ground truth; public Zaragoza bunny data is still used for runtime, memory, and loading consistency.
