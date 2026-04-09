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
Type: Constraint / quality target

What it tests:
Depth accuracy on the public Zaragoza Stanford bunny confocal scene, matching the paper's Fig. 5 comparison.

Primary metric:
- `depth_mae_cm` — lower is better

Interpretation:
This is the quality side of the paper's claim. A faster method that loses bunny depth fidelity should score worse here.

## `zaragoza_efficiency_public_bunny`
Type: Benefit target

What it tests:
Runtime and memory usage for the public Zaragoza bunny reconstruction, matching the paper's reported public-dataset efficiency claim.

Primary metric:
- `runtime_s` — lower is better

Constraint metric:
- `memory_mb` — lower is better

Interpretation:
Scientists should improve runtime without inflating working memory. The score rewards speed only when memory remains controlled.

## Unscored diagnostics
[`scoring/diagnostics.json`](/home/user/scoring/diagnostics.json) may include additional public-scene results, loading-path consistency, and extra quality metrics, but those diagnostics do not affect the score.
