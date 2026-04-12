#!/bin/bash
set -euo pipefail

cd /home/user

export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Regenerate the public Zaragoza benchmark after the FFT-based Eq. (5) fix.
bash scripts/method.sh
python3 validate.py --compare
