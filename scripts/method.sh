#!/bin/bash
# Run only the Quasi-Fresnel method benchmarks.
set -euo pipefail

cd /home/user
python3 scripts/evaluate_nlos.py
