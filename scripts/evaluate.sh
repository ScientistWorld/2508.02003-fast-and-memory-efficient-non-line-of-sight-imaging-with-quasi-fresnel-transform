#!/bin/bash
# Standard evaluation entrypoint: score every registered method on the visible
# train scenes and write scoring/scores.json (same content as scores_train.json).
# Extra arguments are passed to eval/train/evaluate_train.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
python3 eval/train/evaluate_train.py --output "${ROOT}/scoring/scores.json" "$@"
