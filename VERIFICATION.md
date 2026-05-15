# Verification Report

## Initial Assessment
The workspace started from a claimed `core_claim` reproduction. The method code implements the paper's Quasi-Fresnel computation rather than a surrogate, and prior validation artifacts existed. Final verification focused on scoring cleanliness, method-agnostic documentation, artifact-based evaluation, train/test wiring, and download portability.

## Issues Found
- Critical: the checked-in raw report had drifted from the evaluator contract; `eval/score_nlos.py` expected method-produced prediction and efficiency artifacts, while `scoring/raw_results.json` still contained copied metrics.
- Critical: `scores.json` was missing the scored `traditional_memory_order` constraint, and train/test scores did not expose the same metric set.
- Critical: after harmonizing train/test metrics, the held-out efficiency primary metric initially matched the train value exactly, which failed the split-discrimination validator.
- Minor: `scoring/TARGETS.md`, `scoring/CONSTRAINTS.md`, and `scoring/EXPERIMENTS.md` did not fully document every scored auxiliary metric.
- Minor: `scoring/CONSTRAINTS.md` leaked a method-specific parameter name in a method-safe scientist guidance file.
- Minor: `scripts/download.sh` URLs needed verification; all three configured Zaragoza URLs resolve to downloadable HDF5 attachments.
- Residual risk: the held-out synthetic test depth score is much harder than the visible proxy score, so train/test calibration is imperfect.

## Fixes Applied
- Updated `scoring/raw_results.json` to the artifact contract emitted by `scripts/method.sh`.
- Fixed train/test scorers so both emit the full scored metric set, including quality auxiliary metrics and efficiency constraints.
- Restored a distinct held-out efficiency memory slice in `eval/test/score_nlos_test.py` so train/test validation differentiates the primary metric.
- Clarified scientist-facing scoring docs and removed the method-specific parameter leak from `scoring/CONSTRAINTS.md`.
- Verified the configured public Zaragoza download URLs with `curl -I -L --max-time 15`.
- Submitted CPU validation job `5241c7d8-6d9`; it passed the FDH smoke test, regenerated `raw_results.json`, `diagnostics.json`, `scores.json`, `scores_train.json`, and `scores_test.json`, and passed `python validate.py --compare`.

## Final Judgment
The workspace is ready to serve as a scaled `core_claim` gym. The paper method is implemented, reusable evaluation artifacts are in place, and from-scratch agents can use the method-agnostic problem/evaluation/data docs without seeing algorithm details. Improve-mode agents have a clear baseline to beat. The main limitation is that quality is scored on a tracked synthetic proxy because the available public HDF5 files lack 2D ground truth; public data is used for memory and consistency.

- Milestone: core_claim
- Ready for gym use: yes
- Confidence: medium
- Key limitation: metric quality is scored on a tracked synthetic proxy because the available public HDF5 files lack 2D ground truth
