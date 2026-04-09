#!/bin/bash
# Run only the Quasi-Fresnel method benchmarks.
set -euo pipefail

cd /home/user
python3 scripts/evaluate_nlos.py
bash scripts/evaluate.sh /home/user/scoring/raw_results.json /home/user/scoring/scores.json
