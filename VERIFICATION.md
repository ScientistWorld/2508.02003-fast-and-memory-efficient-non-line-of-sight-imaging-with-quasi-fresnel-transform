# Verification Report

## Initial Assessment
The workspace starts from a claimed `core_claim` reproduction. The method code implements the paper's Quasi-Fresnel computation rather than a surrogate, and the main validator passes on the currently packaged score artifacts. The gym is close to usable, but final verification found several rubric and documentation issues that should be fixed before signaling done.

## Issues Found
- Critical: strict method-agnostic documentation leaked the paper method name and acquisition variant in `scoring/EXPERIMENTS.md`.
- Critical: normalized scoring still carried wall-clock runtime fields in `reference.json` and `scores.json`. Their coefficients were zero, but final scoring should not expose runtime as a scored metric.
- Critical: the held-out test scorer preferred the visible raw depth metric before held-out diagnostics, so a future rerun could silently collapse the test slice onto the train slice.
- Minor: `briefing/problem.md`, `briefing/evaluation.md`, `scoring/TARGETS.md`, `scoring/CONSTRAINTS.md`, and `scoring/DIRECTION.md` needed clearer method-agnostic wording.
- Minor: `scripts/download.sh` URLs needed verification; all three configured Zaragoza URLs resolve to downloadable HDF5 attachments.
- Residual risk: the held-out synthetic test depth score is much harder than the visible proxy score, so train/test calibration is imperfect.

## Fixes Applied
- Rewrote strict and high-level scientist-facing docs to describe the task and metrics without naming the paper's specific algorithm.
- Removed wall-clock runtime and runtime-order metrics from normalized `reference.json` and regenerated `scores.json` through `scripts/evaluate.sh`.
- Fixed `eval/test/score_nlos_test.py` so held-out quality diagnostics take precedence over visible raw-report metrics.
- Verified the configured public Zaragoza download URLs with `curl -I -L --max-time 15`.

## Final Judgment
Final judgment is pending a CPU container validation job because the login-node Python does not have NumPy, and the edited method/test scoring path should be rerun inside the packaged environment. If that job passes, the workspace remains a usable `core_claim` gym with a scaled/proxy quality target and a public-data memory target.

- Milestone: core_claim
- Ready for gym use: partial pending validation
- Confidence: medium
- Key limitation: metric quality is scored on a tracked synthetic proxy because the available public HDF5 files lack 2D ground truth
