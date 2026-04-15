#!/bin/bash
set -euo pipefail

cd /home/user

export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# The existing method runner searches the downloader cache first. In this
# workspace the public Zaragoza files are already present under data/zaragoza_public
# and data/zaragoza/public, so expose them at the expected cache paths without
# copying the large HDF5 files.
mkdir -p /home/user/data/downloads/zaragoza/public
ln -sf /home/user/data/zaragoza_public/bunny_simple_256_conf.hdf5 \
  /home/user/data/downloads/zaragoza/bunny_simple_256_conf.hdf5
ln -sf /home/user/data/zaragoza_public/usaf_simple_256_conf.hdf5 \
  /home/user/data/downloads/zaragoza/usaf_simple_256_conf.hdf5
ln -sf /home/user/data/zaragoza/public/T_conf64.hdf5 \
  /home/user/data/downloads/zaragoza/public/T_conf64.hdf5

# Regenerate the public Zaragoza report and produce both designer score slices.
bash scripts/method.sh
bash scripts/evaluate_train.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_train.json
bash scripts/evaluate_test.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_test.json
python3 validate.py --reference-only
