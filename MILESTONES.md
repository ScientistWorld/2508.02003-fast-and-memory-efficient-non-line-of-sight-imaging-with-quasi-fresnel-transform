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

### [2026-05-15 22:48] - core_claim
- Final CPU validation job `5241c7d8-6d9` passed after artifact-contract and train/test metric fixes.
- The validated score contract now includes depth and albedo quality metrics plus memory, direct-path scaling, low-memory scaling, and low-memory consistency constraints.
- `python validate.py --compare` passed, including import separation, artifact-based evaluation checks, and train/test split checks.

### [2026-11-09] - core_claim (hardening, iteration 11)
- Rebuilt the evaluation so the evaluator runs every registered method itself: hidden scenes rendered inside eval/test/ at test time (ten 256 x 256 and two 512 x 512 scans, shot noise), ground truth computed in-process, peak memory measured from /proc, constraint and task gates with bounded failure values.
- Reference (paper's sequential-loading Quasi-Fresnel, s = 0.03 selected on visible train scenes): hidden depth MAE 0.399 cm, albedo NCC 0.956, PSNR 26.29 dB, 148 MB; volumetric paths (full-histogram variant 804 MB, LCT 3.27 GB at 256 x 256) exceed the 256 MB budget.
- Audit (jobs 0afbe2f3-634, 5ef43463-5be): better variants score higher beyond paired noise, weaker ones lower, all red-team shortcuts fail or tie; LCT's better depth (0.07 cm) means the paper's lowest-depth-error claim is not reproduced on these scenes. See HARDENING.md.

## Stop Justification
- Completed at milestone `core_claim`.
