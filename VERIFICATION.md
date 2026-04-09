# Verification Report

## Initial Assessment
The workspace was functional and already contained a recognizable implementation of the paper's Quasi-Fresnel reconstruction pipeline, but the claimed `core_claim` milestone was not justified. The packaged evaluation had been coupled directly to the method code, the scientist-facing scoring docs leaked method details, and the prior scoring story had already been downgraded to `method_runs` because it relied on stale metadata and overstated evidence.

## Issues Found
- Critical: `scripts/evaluate.sh` directly executed the paper implementation, so the evaluation entrypoint was not reusable for future methods.
- Minor: `scoring/CONSTRAINTS.md`, `scoring/DIRECTION.md`, and `scoring/EXPERIMENTS.md` exposed method-specific details that should not be visible to from-scratch scientist agents.
- Minor: the workspace lacked a report artifact contract separating method execution from scoring.

## Fixes Applied
- Added [`eval/score_nlos.py`](/home/user/eval/score_nlos.py) as a method-agnostic scorer that converts a method-produced benchmark report into [`scores.json`](/home/user/scoring/scores.json).
- Updated [`scripts/evaluate.sh`](/home/user/scripts/evaluate.sh) to score a report artifact instead of importing or running method code.
- Updated [`scripts/method.sh`](/home/user/scripts/method.sh) and [`scripts/reproduce.sh`](/home/user/scripts/reproduce.sh) so the paper implementation emits [`raw_results.json`](/home/user/scoring/raw_results.json) first and then calls the reusable evaluator.
- Adjusted [`scripts/evaluate_nlos.py`](/home/user/scripts/evaluate_nlos.py) to write the method report to [`raw_results.json`](/home/user/scoring/raw_results.json).
- Rewrote scientist-facing scoring docs to remove method-step leakage while preserving the problem, constraints, and optimization direction.
- Re-ran [`scripts/evaluate.sh`](/home/user/scripts/evaluate.sh) on the existing report artifact and confirmed `python validate.py --compare` passes.

## Final Judgment
This workspace is now structurally usable as a gym in both improve and from-scratch modes, but only at the `method_runs` milestone. The method implementation is real, the problem/eval split is now clean enough for reuse, and the scoring contract is serviceable. The remaining limitation is evidential rather than structural: the packaged quantitative claim is still too narrow and too lightly validated to defend `core_claim`.

- Milestone: method_runs
- Ready for gym use: partial
- Confidence: medium
- Key limitation: the scored evidence still rests on a very small public evaluation footprint rather than a broader paper-scale reproduction
