# Reproduction Milestones

**Current: method_runs**

## Progress Log

### [2026-04-09 00:00] - none
- Started from an existing partial workspace
- Read the paper and audited the existing implementation against the paper

### [2026-04-09 00:00] - method_runs
- Verified that the workspace contains the paper's three-step Quasi-Fresnel pipeline rather than a surrogate model
- Removed overstated `core_claim` reporting that had been based on synthetic sanity checks and an unfaithful baseline
- Reworked evaluation to target the bundled real Zaragoza-style sample with fixed paper-style `s` selection and repeated timing

### [2026-04-09 00:00] - method_runs
- Job `ad6c4c7b-f06` executed the real-sample benchmark inside the container and produced a primary result before failing in the optional synthetic sanity-check branch
- Recorded real-sample efficiency output of `0.002303 s ± 0.002884 s` runtime and `47.78 MB` max RSS on the bundled confocal sample
- Fixed the `generate_dataset()` call mismatch and changed the evaluator to persist `scores.json` immediately after the primary real benchmark

### [2026-04-09 00:00] - method_runs
- Job `63301e4c-2d6` completed successfully and validated the corrected traditional evaluation path end to end
- Added the paper's sequential-loading aggregation mode to the Quasi-Fresnel implementation so the next job can benchmark traditional versus loading execution on the same bundled real sample

## Stop Justification
