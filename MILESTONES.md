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

## Stop Justification
- Stopping at `core_claim`: the paper's core Quasi-Fresnel quality/efficiency claim is reproduced on the packaged benchmark split, with the method and evaluation environment validated end to end.
