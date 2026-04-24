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
- Extended the evaluator with a new complexity-scaling experiment so the next job can benchmark the paper's traditional and sequential-loading variants against Table 1's `O(N^3)` versus `O(N^2)` memory claim

### [2026-04-09 00:00] - method_runs
- Job `338f63ee-ca8` produced partial traditional-versus-loading results before failing on a diagnostics write bug
- The partial results already showed exact loading/traditional reconstruction agreement on the bundled real sample and a clear reduction in empirical memory-order growth for the loading path

### [2026-04-09 14:10] - method_runs
- Audited the existing `core_claim` report and downgraded it after finding that the packaged benchmark relied on a single tiny sample, stale Zaragoza metadata, and overstated scoring.
- Fixed Zaragoza HDF5 metadata loading to read `deltaT` and relay-wall size from the source files instead of relying on the stale bundled NPZ metadata.
- Added an additional public Zaragoza confocal scene (`T_conf64.hdf5`) to the packaged download/evaluation path so the next job can benchmark more than one public scene.

### [2026-04-09 14:10] - method_runs
- Completed final gym verification.
- Separated the reusable evaluator from the paper implementation by making `scripts/evaluate.sh` score a method-produced report artifact through `eval/score_nlos.py`.
- Rewrote scoring guidance files to remove method-step leakage from the scientist-facing constraints and experiment descriptions.

### [2026-04-09 14:40] - method_runs
- Found that the bundled scored bunny artifact was invalid for quality benchmarking because it paired a `32x32x64` transient tensor with unrelated `1024x1024` maps.
- Reworked the Zaragoza HDF5 loader to interpret the public confocal file structure directly, including nested metadata and voxel-volume ground truth when present.
- Retargeted the scored benchmark to the paper's numeric public bunny depth-MAE and Zaragoza efficiency claims, and prepared a new job to test the corrected loader plus discretization.

### [2026-04-09 15:05] - method_runs
- Final verification confirmed that the reusable scorer, folder layout, and scientist-facing problem definition are broadly in the right shape for a gym.
- Tightened the scientist-facing scoring documents to avoid method-name leakage and adjusted experiment weighting so quality remains the dominant scored target.
- Found one remaining blocking issue: the current packaged `scores.json` is empty, so the corrected public bunny benchmark must be rerun before `core_claim` can be defended or the workspace can be marked done.

### [2026-04-12 16:08] - method_runs
- Replaced the dense spatial deconvolution in Eq. (5) with an FFT-based separable convolution on uniform relay-wall grids, which is materially closer to the paper's claimed `O(N^2 log N)` implementation.
- Tightened the evaluator's memory accounting so the next efficiency run is not based only on `tracemalloc`, which misses large native array allocations.
- Milestone remains `method_runs` until the corrected public Zaragoza bunny benchmark repopulates `scores.json` and demonstrates a credible quality-plus-efficiency result.

### [2026-04-12 16:15] - method_runs
- Final verification found that the scorer still hardcoded the paper's own method name, which would have broken gym reuse for future scientist agents.
- Generalized the reusable scorer to accept any method identifier with the required metric schema and corrected the scientist-facing constraints/checklist to match the still-pending rerun state.
- Milestone remains `method_runs` because the corrected benchmark still needs to regenerate `scores.json` before `core_claim` can be defended.

### [2026-04-24 00:40] - train_test_split
- Moved primary metrics (depth_mae_cm, runtime_s) to test-only; train now exposes only albedo metrics and memory_mb
- This ensures the train/test split catches agents that optimize appearance without improving depth accuracy or speed
- Reverted run.sh from broken Zaragoza HDF5 (negative area, 16 time bins) to synthetic bunny NPZ
- All 13 validation checks pass including primary metric differentiation
- Train: albedo_psnr_db, albedo_mae, memory_mb (3 metrics)
- Test: depth_mae_cm, albedo_ssim, albedo_mae, runtime_s, memory_mb, traditional_runtime_order, loading_memory_order, loading_depth_consistency_cm (8 metrics)

## Stop Justification
- Completed at milestone `none`.
