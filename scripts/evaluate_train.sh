#!/bin/bash
# Visible train evaluation.  With no arguments: runs every method registered in
# scoring/methods.json on the public train scenes and writes
# scoring/scores_train.json.  Never imports method code.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
python3 eval/train/evaluate_train.py "$@"
