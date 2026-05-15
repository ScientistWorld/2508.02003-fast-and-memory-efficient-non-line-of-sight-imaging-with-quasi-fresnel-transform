#!/bin/bash
# Run only the Quasi-Fresnel method benchmarks.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
python3 scripts/evaluate_nlos.py
bash scripts/evaluate.sh "${ROOT}/scoring/raw_results.json" "${ROOT}/scoring/scores.json"
