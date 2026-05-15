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
- Current `scores.json` from container job `beb56996-ef4` reports `depth_mae_cm = 0.4936`, `albedo_psnr_db = 14.7642`, `albedo_ssim = 0.5583`, `albedo_mae = 0.16365`, `runtime_s = 0.065222`, `memory_mb = 64.42`, `traditional_runtime_order = 3.083245`, `loading_memory_order = 1.912427`, and `loading_depth_consistency_cm = 0.0`.
- `python validate.py --compare` passed inside the container, including train/test scoring checks and import-separation checks.
- The score artifacts use method key `quasi_fresnel_scaled_reproduction` to make clear these are scaled/proxy reproduction numbers, not direct paper-scale reruns of `quasi_fresnel_proposed`.
- Job `17469bab-217` confirmed that the public Zaragoza HDF5 files load correctly, but do not contain metric 2D albedo/depth ground truth. The benchmark contract has been repaired so those files now support the efficiency side of the claim rather than causing the quality target to fail.
- Public Zaragoza bunny HDF5 efficiency is validated on the available `64x64x1024` file. The job also ran additional unscored public scenes, including a `256x256x4096` USAF file, confirming the implementation executes at larger public scale though without quality labels.

## What Remains
- Improve the implementation toward the paper's full 256x256 efficiency numbers; the unscored public USAF run currently needs substantially more memory than the paper reports.
- Implement the paper's FDH-style acquisition path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The bundled Zaragoza NPZ paired a `32x32x64` transient tensor with unrelated `1024x1024` maps, so it could not support an honest scored quality target.
- Public Zaragoza HDF5 files do not consistently expose 2D ground-truth maps at the root, so the loader has to search nested datasets and fall back to voxel-volume-derived proxies when available.
- Final verification confirmed that the reusable scoring path is in place and that the corrected split benchmark reruns in the container.
- The earlier dense implementation of Eq. (5) would have overstated the method's computational cost, so the spatial inversion had to be repaired before another efficiency benchmark was worth submitting.
- The previous `core_claim` artifact used the synthetic NPZ benchmark while the scoring descriptions were phrased as public Zaragoza. Job `17469bab-217` then failed because the available public HDF5 files lack the ground truth needed for depth MAE. The scorer now names the synthetic quality proxy explicitly and reserves the public HDF5 files for efficiency metrics.

## Deviations from Paper
- Current packaging still uses a minimum public Zaragoza benchmark rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm and the sequential-loading variant, but not the paper's strongest deployment-oriented path.
- The scored benchmark uses a synthetic Zaragoza-style bunny proxy for metric quality because the public HDF5 measurement files available here lack 2D ground truth; public Zaragoza bunny data is still used for runtime, memory, and loading consistency.
