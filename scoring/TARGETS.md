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

Auxiliary scored metrics:
- `albedo_psnr_db` — higher is better
- `albedo_ssim` — higher is better
- `albedo_mae` — lower is better

Interpretation:
This is the quality-preservation side of the paper's claim. A faster method that loses bunny depth fidelity or visibly degrades the reconstructed intensity image on the metric-ground-truth proxy should score worse here.

## `zaragoza_efficiency_public_bunny`
Type: Benefit target

What it tests:
Working memory and low-memory path consistency for reconstruction on an available public Zaragoza bunny measurement. The current job path prefers the 64x64 public bunny copy for repeatable CPU validation and falls back to the downloaded 256x256 public bunny file.

Primary metric:
- `memory_mb` — lower is better

Constraint metrics:
- `traditional_memory_order` — lower is better; diagnostic scaling check for the direct full-histogram path.
- `loading_memory_order` — lower is better; checks that the sequential-loading path has near-2D memory growth.
- `loading_depth_consistency_cm` — lower is better; checks that the memory-saving path preserves the reconstruction.

Interpretation:
Scientists should improve quality without inflating working memory or breaking the paper's low-memory reconstruction path. Raw diagnostics may include wall-clock timings for local debugging, but those values do not affect the score.

## Unscored diagnostics
[`scoring/diagnostics.json`](/home/user/scoring/diagnostics.json) may include additional public-scene results and extra quality metrics, but those diagnostics do not affect the score unless their metrics are listed above.
