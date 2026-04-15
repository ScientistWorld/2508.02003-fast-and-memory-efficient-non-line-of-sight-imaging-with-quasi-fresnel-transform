#!/bin/bash
set -euo pipefail

cd /home/user

export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Regenerate the public Zaragoza report and produce both designer score slices.
bash scripts/method.sh
bash scripts/evaluate_train.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_train.json
bash scripts/evaluate_test.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_test.json
python3 validate.py --reference-only
