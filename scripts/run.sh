#!/bin/bash
# End-to-end reproduction of the reference (CPU only, ~5 min on one core):
#   1. render the visible train scenes (deterministic, cached in data/train_scenes/);
#   2. select the Quasi-Fresnel parameter s on the visible train scenes and register
#      the reference method (method/qf_params.json, scoring/methods.json);
#   3. score it on the visible scenes (scores.json, scores_train.json) and on the
#      hidden scenes (scores_test.json), score the simple baseline on the visible
#      scenes, and validate the workspace.
# The hardening audit (variants, baselines, shortcuts) is redteam/hardening/run_audit.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

python3 data/nlos_scenes.py --write-train
bash scripts/method.sh --select-s
bash scripts/evaluate.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
bash scripts/baseline.sh
python3 validate.py --post-design
