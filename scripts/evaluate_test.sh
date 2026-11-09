#!/bin/bash
# Hidden test evaluation.  With no arguments: renders the hidden scenes at test
# time, runs every method registered in scoring/methods.json on them, and writes
# scoring/scores_test.json.  Never imports method code and never trusts numbers
# written by a method.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
python3 eval/test/evaluate_test.py "$@"
