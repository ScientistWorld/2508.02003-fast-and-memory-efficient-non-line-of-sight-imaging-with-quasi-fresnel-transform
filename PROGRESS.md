# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The method is packaged behind `scripts/evaluate.sh` and `scripts/reproduce.sh`.
- A bundled real Zaragoza-style confocal sample exists in `data/zaragoza/`.
- The evaluation path now avoids oracle tuning on the test target and removes misleading baseline claims.
- The method code now includes both the paper's direct full-histogram integration path and its sequential-loading aggregation path.
- The evaluation pipeline now measures both the paper's public efficiency claim and the sequential-loading complexity claim in a standalone, container-validated run.

## Results Achieved
- Prior reported results in this repo were based on synthetic sanity checks and should not be treated as paper reproduction.
- Failed job `ad6c4c7b-f06` still completed the primary real-sample benchmark before crashing in the optional synthetic sanity branch.
- Successful job `63301e4c-2d6` validated the corrected evaluation pipeline end to end and produced `scoring/scores.json`.
- Real bundled Zaragoza-style sample result from the successful run: `runtime = 0.001707 s ± 0.001910 s`, `memory = 45.23 MB`, proxy quality `PSNR = 3.00 dB`, `SSIM = 0.0299`, `albedo MAE = 0.6843`, `depth MAE = 0.4606`.
- Synthetic sanity result from the successful run: `runtime = 0.005769 s`, `memory = 125.12 MB`, `PSNR = 12.81 dB`, `SSIM = 0.1794`.
- The current revision extends evaluation with a new Table 1 scaling experiment that fits empirical runtime and working-memory orders for the traditional and sequential-loading variants on cubic `N x N x N` measurement tensors.
- Failed job `338f63ee-ca8` still produced useful partial outputs before crashing on a diagnostics-file write bug: the bundled real sample showed exact agreement between traditional and sequential-loading reconstructions, and the initial scaling experiment already separated loading memory growth (`~N^1.98`) from traditional memory growth (`~N^2.64`).
- Successful job `ccc51754-375` completed the full corrected evaluation. On the bundled real Zaragoza-style sample, the proposed method ran in `0.002604 s ± 0.001937 s` with `50.00 MB` max RSS, while the sequential-loading variant produced exactly matching reconstructions (`PSNR = 100 dB`, `SSIM = 1.0` against the traditional path).
- The same successful job also validated the paper's loading-memory claim on direct time integration: traditional integration fit `runtime_order = 3.009`, `memory_order = 2.704`, while sequential loading fit `runtime_order = 1.764`, `memory_order = 1.891`.

## What Remains
- Implement the paper's FDH-style path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The corrected CPU run failed after the real benchmark because `generate_dataset()` received `N_relay` twice; this was fixed in the evaluator.
- The first complexity-scaling job failed after writing `scores.json` because `diag_path` was not redefined after the evaluator refactor; this has now been fixed.

## Deviations from Paper
- Current packaging uses one bundled Zaragoza-style sample rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm but not the paper's strongest deployment-oriented path.
- The complexity experiment measures empirical scaling on synthetic random `N x N x N` tensors to validate the asymptotic claim in Table 1; it is a complexity probe, not a physical-scene benchmark.
