# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-15 21:25] - method_runs
- Existing Quasi-Fresnel implementation executes the paper's time aggregation, spatial inversion, and albedo/depth extraction pipeline end to end.
- Packaged scripts produce method artifacts and score them without importing `method/` from `eval/`.

### [2026-05-15 21:25] - core_claim
- Prior container job reproduced the central quality/efficiency claim on the available benchmark split: metric depth quality on the tracked Zaragoza-style bunny proxy and runtime/memory behavior on public Zaragoza bunny measurements.
- Current turn adds the paper's FDH-style aggregated reconstruction interface and fixes relay-wall extent inference; a new submitted job will refresh the scored artifacts.

### [2026-05-15 21:36] - core_claim
- Container job `b27e91f3-049` passed the FDH smoke test, regenerated `raw_results.json`, `diagnostics.json`, `scores.json`, train/test scores, and passed `python validate.py --compare`.
- Refreshed scores show the FDH-style public-bunny path at `0.075464 s` and `1.70 MB` with exact consistency against the traditional reconstruction, while the quality proxy remains at `0.4936 cm` depth MAE.
- The reproduced score method is named `quasi_fresnel_scaled_reproduction` because the benchmark uses a tracked quality proxy and lightweight public-bunny efficiency fixture rather than the exact full paper setting.

### [2026-05-15 22:25] - core_claim
- Final CPU validation job `eca1622c-006` passed after verifier fixes, including the FDH smoke test, method artifact regeneration, train/test scoring, and `python validate.py --compare`.
- Final verification confirmed the gym remains at `core_claim`, with runtime-dependent metrics removed from scoring and held-out scorer wiring fixed.

## Stop Justification
- Completed at milestone `core_claim`.
