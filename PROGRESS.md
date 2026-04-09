# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The method is packaged behind `scripts/evaluate.sh` and `scripts/reproduce.sh`.
- Public Zaragoza confocal samples are packaged in `data/zaragoza/` and `data/zaragoza/public/`.
- The evaluation path now avoids oracle tuning on the test target and removes misleading baseline claims.
- The method code now includes both the paper's direct full-histogram integration path and its sequential-loading aggregation path.
- The Zaragoza loader now reads `deltaT` and relay-wall size from the source HDF5 files, avoiding stale metadata copied into the older NPZ bundle.
- The evaluation pipeline can benchmark an additional public Zaragoza scene without inventing quality targets when the HDF5 file has no ground-truth maps.

## Results Achieved
- The method has previously run successfully inside the packaged container, so `method_runs` remains secure.
- Earlier reported `core_claim`-style results are now considered stale because they were computed before the `deltaT` metadata fix and before broadening the public-scene evaluation beyond the single bundled bunny sample.
- The next submitted job will regenerate `scoring/scores.json` and `scoring/diagnostics.json` using the corrected HDF5 metadata path and the added public `T` scene benchmark.

## What Remains
- Re-run the packaged evaluation after the metadata fix and scene-expansion changes.
- Determine whether the corrected multi-scene efficiency results are strong enough to justify `core_claim`; current status remains `method_runs`.
- Implement the paper's FDH-style path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The bundled Zaragoza NPZ stored stale timing metadata (`dt=0.003`) while the source HDF5 files declare `deltaT=0.0025`; the evaluator now reads metadata from the HDF5 source.
- Public Zaragoza HDF5 files do not consistently contain ground-truth albedo/depth maps, so they can only be used as efficiency benchmarks unless paired with trustworthy GT from another source.

## Deviations from Paper
- Current packaging still uses lightweight public Zaragoza scenes rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm but not the paper's strongest deployment-oriented path.
- The complexity experiment measures empirical working-memory scaling on synthetic `N x N x N` tensors to validate the Table 1 memory claim; it is a complexity probe, not a physical-scene benchmark.
