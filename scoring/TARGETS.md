# Evaluation Targets

Each scored target below corresponds to one experiment in [`scores.json`](/home/user/scoring/scores.json).
Run all scored targets with:

```bash
bash scripts/evaluate.sh /home/user/scoring/raw_results.json /home/user/scoring/scores.json
```

The paper implementation that produces the raw report artifact is run with:

```bash
bash scripts/method.sh
```

## `zaragoza_bunny_depth_error`
Type: Quality target

What it tests:
Depth accuracy for the Zaragoza Stanford bunny Fig. 5 comparison. The scored gym target uses the tracked synthetic Zaragoza-style bunny proxy in `data/bunny/bunny_64x64.npz`, because the public HDF5 measurement files available here do not contain metric 2D albedo/depth ground truth.

Primary metric:
- `depth_mae_cm` — lower is better

Interpretation:
This is the quality-preservation side of the paper's claim. A faster method that loses bunny depth fidelity on the metric-ground-truth proxy should score worse here.

## `zaragoza_efficiency_public_bunny`
Type: Benefit target

What it tests:
Runtime and working memory for the paper's FDH-style aggregated Quasi-Fresnel reconstruction on an available public Zaragoza bunny measurement. The current job path prefers the 64x64 public bunny copy for repeatable CPU validation and falls back to the downloaded 256x256 public bunny file.

Primary metric:
- `memory_mb` — lower is better

Compatibility metric:
- `runtime_s` — lower is better, retained for comparison with paper artifacts but not included in the composite score because wall-clock measurements depend on hardware

Interpretation:
Scientists should improve runtime without inflating working memory. The score rewards the low-memory aggregated path emphasized by the paper, while diagnostics also compare it against the full-histogram and sequential-loading paths on the same public scene.

## Unscored diagnostics
[`scoring/diagnostics.json`](/home/user/scoring/diagnostics.json) may include additional public-scene results, loading-path consistency, and extra quality metrics, but those diagnostics do not affect the score.
