# Scientist Constraints

## Method
Stay within the paper's fast direct-reconstruction family for confocal NLOS surface recovery.
Do not switch to a fundamentally different paradigm such as a generic learned black-box predictor, a full 3D volumetric pipeline, or a method that relies on extra supervision unavailable in this workspace.

## Data
Use the packaged confocal sample in `data/zaragoza/` for the paper-aligned efficiency benchmark.
Synthetic data may be used only as a sanity check, not as a relabeled replacement for the paper's public datasets.

## Evaluation
Use `scripts/evaluate.sh` with a report matching the packaged experiment/result structure.
Do not oracle-tune the parameter `s` on the test target.
