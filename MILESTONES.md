# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-15 21:25] - method_runs
- Existing Quasi-Fresnel implementation executes the paper's time aggregation, spatial inversion, and albedo/depth extraction pipeline end to end.
- Packaged scripts produce method artifacts and score them without importing `method/` from `eval/`.

### [2026-05-15 21:25] - core_claim
- Prior container job reproduced the central quality/efficiency claim on the available benchmark split: metric depth quality on the tracked Zaragoza-style bunny proxy and runtime/memory behavior on public Zaragoza bunny measurements.
- Current turn adds the paper's FDH-style aggregated reconstruction interface and fixes relay-wall extent inference; a new submitted job will refresh the scored artifacts.

## Stop Justification
- Not stopped. Continuing with a submitted verification job for the FDH-style efficiency path.
