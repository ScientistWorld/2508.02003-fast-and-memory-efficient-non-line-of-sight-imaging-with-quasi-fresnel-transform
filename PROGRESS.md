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
- The method has previously run successfully inside the packaged container, so `method_runs` remains secure.
- Earlier reported results are considered stale because they were computed on retired experiment definitions and before the HDF5 loader / discretization fixes.
- The scoring contract has been rewritten around the paper's numeric bunny depth MAE figure and Zaragoza runtime/memory claim.
- `python validate.py --compare` still fails because the corrected FFT-based benchmark has not been rerun yet, so `scores.json` remains intentionally cleared pending the next job.

## What Remains
- Run the corrected public bunny benchmark in the container and inspect whether the new loader plus FFT-based separable inversion produce a credible bunny depth MAE and Zaragoza-style efficiency result.
- Repopulate `scoring/raw_results.json` and `scoring/scores.json`; both were intentionally cleared when the benchmark contract changed and have not yet been regenerated.
- Determine whether those corrected public-scene results are strong enough to justify `core_claim`; current status remains `method_runs`.
- Implement the paper's FDH-style path.
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
