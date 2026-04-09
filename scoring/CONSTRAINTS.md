# Scientist Constraints

## Data
- Keep the scored real-sample benchmark fixed to the packaged Zaragoza artifact:
  - `data/zaragoza/bunny_conf64.hdf5`
  - ground-truth proxy maps paired in `data/zaragoza/bunny_conf64.npz`
- Keep the complexity benchmark fixed to the packaged synthetic cubic-tensor sweep used by [`scripts/evaluate_nlos.py`](/home/user/scripts/evaluate_nlos.py):
  - sizes `32, 64, 96, 128`
  - `dt=0.003`
  - `k=4`
- Do not replace the scored real sample with easier synthetic data.

## Compute / comparison setup
- Keep the scored experiment structure fixed to the two entries already present in [`scores.json`](/home/user/scoring/scores.json):
  - `zaragoza_efficiency_real_sample`
  - `complexity_scaling_cubic_measurements`
- Keep metric definitions fixed:
  - `runtime_s`
  - `memory_mb`
  - `memory_order`
- Keep the scoring entrypoint fixed to [`scripts/evaluate.sh`](/home/user/scripts/evaluate.sh), which expects a method-produced report matching [`scoring/raw_results.json`](/home/user/scoring/raw_results.json).

## Fairness rules
- Do not oracle-tune `s` or other scene-specific parameters against test ground truth.
- Do not claim improvement by changing hardware allocation, dropping the scored sample, or changing the tensor sizes used for the scaling fit.
- Do not substitute a generic learned predictor or add external supervision unavailable in this workspace.
