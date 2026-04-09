#!/bin/bash
# Standard evaluation entrypoint.
# Score a method-produced report artifact without importing method code.
set -euo pipefail

cd /home/user
INPUT_PATH="${1:-/home/user/scoring/raw_results.json}"
OUTPUT_PATH="${2:-/home/user/scoring/scores.json}"

python3 eval/score_nlos.py --input "${INPUT_PATH}" --output "${OUTPUT_PATH}"
