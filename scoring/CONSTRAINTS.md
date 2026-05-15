# Scientist Constraints

## Data
- Keep the scored quality benchmark fixed to the tracked metric proxy:
  - [`data/bunny/bunny_64x64.npz`](/home/user/data/bunny/bunny_64x64.npz)
- Keep the scored public-scene efficiency benchmark fixed to the packaged Zaragoza Stanford bunny confocal HDF5:
  - [`data/zaragoza/bunny_conf64.hdf5`](/home/user/data/zaragoza/bunny_conf64.hdf5)
- If the lightweight HDF5 fixture is unavailable, `scripts/download.sh` can fetch the larger public 256x256 bunny file as a fallback, but do not replace the scored scene with easier synthetic data.
- Additional public Zaragoza scenes may be used for diagnostics, but they do not replace the scored bunny target.

## Compute / comparison setup
- Keep the scored experiment structure fixed to the packaged public-bunny benchmark contract:
  - `zaragoza_bunny_depth_error`
  - `zaragoza_efficiency_public_bunny`
- Keep metric definitions fixed:
  - `depth_mae_cm`
  - `memory_mb`
  - `traditional_memory_order`
  - `loading_memory_order`
  - `loading_depth_consistency_cm`
- Keep the scoring entrypoint fixed to [`scripts/evaluate.sh`](/home/user/scripts/evaluate.sh), which expects a method-produced report matching the structure of [`scoring/raw_results.json`](/home/user/scoring/raw_results.json).

## Fairness rules
- Do not oracle-tune `s` or other scene-specific parameters against test ground truth.
- Do not change the scored scene, metric units, or evaluation interface to make the benchmark easier.
- Do not substitute a generic learned predictor or add external supervision unavailable in this workspace.
