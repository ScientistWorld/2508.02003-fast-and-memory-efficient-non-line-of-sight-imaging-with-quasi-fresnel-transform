# Scientist Constraints

## Data
- Keep the scored public-scene benchmark fixed to the packaged Zaragoza Stanford bunny confocal HDF5 when it is available:
  - [`data/zaragoza_public/bunny_simple_256_conf.hdf5`](/home/user/data/zaragoza_public/bunny_simple_256_conf.hdf5)
- If that file is unavailable, use the packaged fallback bunny HDF5 selected by [`scripts/evaluate_nlos.py`](/home/user/scripts/evaluate_nlos.py), but do not replace the scored scene with easier synthetic data.
- Additional public Zaragoza scenes may be used for diagnostics, but they do not replace the scored bunny target.

## Compute / comparison setup
  - Keep the scored experiment structure fixed to the two entries already present in [`scores.json`](/home/user/scoring/scores.json):
  - `zaragoza_bunny_depth_error`
  - `zaragoza_efficiency_public_bunny`
- Keep metric definitions fixed:
  - `depth_mae_cm`
  - `runtime_s`
  - `memory_mb`
- Keep the scoring entrypoint fixed to [`scripts/evaluate.sh`](/home/user/scripts/evaluate.sh), which expects a method-produced report matching [`scoring/raw_results.json`](/home/user/scoring/raw_results.json).

## Fairness rules
- Do not oracle-tune `s` or other scene-specific parameters against test ground truth.
- Do not change the scored scene, metric units, or evaluation interface to make the benchmark easier.
- Do not substitute a generic learned predictor or add external supervision unavailable in this workspace.
