# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The method is packaged behind `scripts/evaluate.sh` and `scripts/reproduce.sh`.
- A bundled real Zaragoza-style confocal sample exists in `data/zaragoza/`.
- The evaluation path now avoids oracle tuning on the test target and removes misleading baseline claims.

## Results Achieved
- Prior reported results in this repo were based on synthetic sanity checks and should not be treated as paper reproduction.
- Failed job `ad6c4c7b-f06` still completed the primary real-sample benchmark before crashing in the optional synthetic sanity branch.
- Real bundled Zaragoza-style sample result from that run: `runtime = 0.002303 s ± 0.002884 s`, `memory = 47.78 MB`, proxy quality `PSNR = 3.00 dB`, `SSIM = 0.0299`, `albedo MAE = 0.6843`, `depth MAE = 0.4606`.
- The crash was caused by a bad `generate_dataset(...)` call signature in `scripts/evaluate_nlos.py`; this has now been fixed, and the script now writes `scores.json` plus a partial `diagnostics.json` immediately after the real benchmark.

## What Remains
- Run the corrected evaluation job and inspect the resulting runtime/memory numbers.
- Implement the paper's lower-memory sequential-loading or FDH-style path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.
- The corrected CPU run failed after the real benchmark because `generate_dataset()` received `N_relay` twice; this was fixed in the evaluator.

## Deviations from Paper
- Current packaging uses one bundled Zaragoza-style sample rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm but not the paper's strongest deployment-oriented path.
