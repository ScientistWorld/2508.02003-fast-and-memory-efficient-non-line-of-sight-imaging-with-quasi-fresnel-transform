# Evaluation

The packaged benchmark has two complementary targets:

- `zaragoza_bunny_depth_error`: depth reconstruction quality on a tracked Zaragoza-style bunny proxy with metric ground truth.
- `zaragoza_efficiency_public_bunny`: working-memory behavior on the packaged public Zaragoza bunny confocal measurement.

`scripts/method.sh` writes prediction artifacts under `outputs/` and records their paths in `scoring/raw_results.json`. `scripts/evaluate.sh` then recomputes quality metrics from those artifacts against fixed data in `data/`; it does not trust method-reported quality scores.

`depth_mae_cm` is the primary quality metric. Lower values mean the recovered surface geometry is closer to the reference depth map.

`memory_mb` is the primary efficiency metric. Lower values mean the reconstruction can run with less peak working memory on the fixed public-scene input. Wall-clock runtime is kept only in raw diagnostics because it depends on hardware and is not part of the scored objective.

Additional public Zaragoza scenes are treated as diagnostics unless they also expose trustworthy ground truth through the HDF5 metadata.
