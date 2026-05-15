#!/bin/bash
# Train-slice evaluation entrypoint.
# Score a method-produced report artifact without importing method code.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
INPUT_PATH="${1:-${ROOT}/scoring/raw_results.json}"
OUTPUT_PATH="${2:-${ROOT}/scoring/scores_train.json}"

python3 eval/train/score_nlos_train.py --input "${INPUT_PATH}" --output "${OUTPUT_PATH}"
