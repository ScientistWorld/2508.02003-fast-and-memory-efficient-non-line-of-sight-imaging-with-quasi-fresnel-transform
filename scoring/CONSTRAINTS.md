# Scientist Constraints

## Method
Keep the paper's Quasi-Fresnel reconstruction pipeline:
- time aggregation of the transient histogram into a complex 2D field
- spatial deconvolution in the relay-wall plane
- albedo/depth extraction from the recovered complex field

Replacing the method with a different NLOS reconstruction paradigm is out of scope.

## Data
Use the packaged confocal sample in `data/zaragoza/` for the paper-aligned efficiency benchmark.
Synthetic data may be used only as a sanity check, not as a relabeled replacement for the paper's public datasets.

## Evaluation
Use `scripts/evaluate.sh` / `scripts/evaluate_nlos.py`.
Do not oracle-tune the parameter `s` on the test target.
