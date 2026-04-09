# Progress

## What Works
- The workspace contains a recognizable implementation of the paper's Quasi-Fresnel reconstruction equations.
- The method is packaged behind `scripts/evaluate.sh` and `scripts/reproduce.sh`.
- A bundled real Zaragoza-style confocal sample exists in `data/zaragoza/`.
- The evaluation path now avoids oracle tuning on the test target and removes misleading baseline claims.

## Results Achieved
- Prior reported results in this repo were based on synthetic sanity checks and should not be treated as paper reproduction.
- A new validation run is prepared to regenerate `scoring/scores.json` on the real bundled sample under the corrected benchmark definition.

## What Remains
- Run the corrected evaluation job and inspect the resulting runtime/memory numbers.
- Implement the paper's lower-memory sequential-loading or FDH-style path.
- Add a faithful published baseline implementation.
- Expand to larger public Zaragoza and Stanford datasets if download and budget permit.

## Issues Encountered
- The previous repo state mislabeled synthetic experiments as Zaragoza/Stanford reproductions.
- The prior LCT baseline was explicitly simplified and cannot support the paper's comparison claims.
- The paper's strongest quantitative evidence is efficiency, while direct quality tables are mostly qualitative in the manuscript.

## Deviations from Paper
- Current packaging uses one bundled Zaragoza-style sample rather than the full public Zaragoza and Stanford benchmark suites.
- The efficient FDH acquisition path is not yet implemented; the current method corresponds to the analytical three-step algorithm but not the paper's strongest deployment-oriented path.
