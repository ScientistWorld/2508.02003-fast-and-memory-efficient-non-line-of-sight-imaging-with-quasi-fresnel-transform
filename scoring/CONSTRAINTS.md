# Scientist Constraints

## Fixed by the benchmark (do not change)
- The evaluators (`eval/`), the scene generator (`data/nlos_scenes.py`), the acquisition geometry, noise model, scene lists and seeds.
- Metric definitions, gates, the 256 MB memory budget, the 300 s per-scene limit, experiment names and `scoring/reference.json`.
- The method contract: `<command> --scene <dir> --output <file.npz>` registered in `scoring/methods.json`; scored through `scripts/evaluate_train.sh` / `scripts/evaluate_test.sh` with no arguments.

## Fairness rules
- A method may only use the measurement and metadata in the scene directory it is given. It must not read ground truth (`data/train_scenes/*/ground_truth.npz`, the scene generator's internals) or anything under `eval/` at run time, and must not cache answers across runs.
- Parameters may be tuned on the visible train scenes only.
- Memory is measured on the method's own process tree; do not hide work in processes outside that tree (daemons, servers started earlier, other sessions) or in precomputed artifacts that depend on the scenes.
- No training on external labelled data; no learned black-box predictor substituted for reconstruction from the given measurement.
