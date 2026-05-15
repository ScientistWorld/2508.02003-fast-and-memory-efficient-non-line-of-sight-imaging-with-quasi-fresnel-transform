# Evaluation Targets

Each scored target below corresponds to one experiment in [`scores.json`](/home/user/scoring/scores.json).
Run all scored targets with:

```bash
bash scripts/evaluate.sh /home/user/scoring/raw_results.json /home/user/scoring/scores.json
```

The provided reference method produces the raw report artifact with:

```bash
bash scripts/method.sh
```

## `zaragoza_bunny_depth_error`
Type: Quality target

What it tests:
Depth accuracy for the Zaragoza Stanford bunny target. The scored gym target uses the tracked synthetic Zaragoza-style bunny proxy in `data/bunny/bunny_64x64.npz`, because the public HDF5 measurement files available here do not contain metric 2D albedo/depth ground truth.

Primary metric:
- `depth_mae_cm` — lower is better

Interpretation:
This is the quality-preservation side of the paper's claim. A faster method that loses bunny depth fidelity on the metric-ground-truth proxy should score worse here.

## `zaragoza_efficiency_public_bunny`
Type: Benefit target

What it tests:
Working memory for reconstruction on an available public Zaragoza bunny measurement. The current job path prefers the 64x64 public bunny copy for repeatable CPU validation and falls back to the downloaded 256x256 public bunny file.

Primary metric:
- `memory_mb` — lower is better

Interpretation:
Scientists should improve quality without inflating working memory. Raw diagnostics may include wall-clock timings for local debugging, but those values do not affect the score.

## Unscored diagnostics
[`scoring/diagnostics.json`](/home/user/scoring/diagnostics.json) may include additional public-scene results, loading-path consistency, and extra quality metrics, but those diagnostics do not affect the score.
