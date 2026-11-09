# Evaluation Targets

Every target below is an experiment in `scoring/scores*.json` and in `scoring/reference.json`.

Register a method in `scoring/methods.json` (contract: `briefing/evaluation.md`), then:

```bash
bash scripts/method.sh            # registers the reference method
bash scripts/evaluate_train.sh    # visible scenes  -> scoring/scores_train.json
bash scripts/evaluate_test.sh     # hidden scenes   -> scoring/scores_test.json
```

## `surface_reconstruction` (weight 0.6) — benefit and constraint
- `depth_mae_cm` (primary, lower is better, |coefficient| 1.0)
- `albedo_ncc` (higher is better, |coefficient| 0.6)
- `albedo_psnr_db` (higher is better, |coefficient| 0.3)

Paper context (not targets; different scenes): Zaragoza bunny depth MAE 0.15 cm for the paper's method, 0.16 cm LCT, 0.31 cm f-k / phasor, 4.69 cm FBP.

## `working_memory` (weight 0.4) — benefit
- `peak_memory_mb` (primary, lower is better, |coefficient| 1.0): evaluator-measured peak resident memory, maximum over scenes.

Paper context (not targets): under 50 MB for the paper's method vs over 13 GB for prior volumetric methods on Zaragoza.

## Constraints (any violation fails the run; failure values are bounded and worse than any valid run)
- valid `albedo`/`depth` arrays of the scene's shape on every scene; finite; albedo ≥ 0 and not constant; depth in `[0, 0.768]` m;
- peak memory ≤ 256 MB on every scene; ≤ 300 s per scene;
- mean depth MAE ≤ 0.5 x best-constant-depth MAE; mean albedo correlation ≥ 0.2.

## Reference
`quasi_fresnel` (the reproduced method) is the reference every attempt is ranked against; its scores are in `scoring/scores_train.json` / `scoring/scores_test.json`. A simple streaming baseline can be scored with `bash scripts/baseline.sh` (visible scenes only).
