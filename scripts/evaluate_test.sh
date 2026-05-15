#!/bin/bash
# Held-out test-slice evaluation entrypoint.
# Score a method-produced report artifact without importing method code.
# The Python scorer reads scoring/scores_train.json when present so this pass
# evaluates the same method keys as the visible train slice.
set -euo pipefail

cd /home/user
INPUT_PATH="${1:-/home/user/scoring/raw_results.json}"
OUTPUT_PATH="${2:-/home/user/scoring/scores_test.json}"

python3 eval/test/score_nlos_test.py --input "${INPUT_PATH}" --output "${OUTPUT_PATH}"
