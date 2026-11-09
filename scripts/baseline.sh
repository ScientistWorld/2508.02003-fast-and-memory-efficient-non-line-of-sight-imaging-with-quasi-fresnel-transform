#!/bin/bash
# Score the simple streaming baseline (photon energy + peak time bin) on the
# visible train scenes, without registering it in scoring/methods.json.
# Writes scoring/baseline_scores_train.json.  The volumetric LCT baseline
# (baseline/lct.py) can be registered the same way; it exceeds the memory
# budget by design.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
REGISTRY="$(mktemp)"
trap 'rm -f "${REGISTRY}"' EXIT
cat > "${REGISTRY}" <<'JSON'
{"methods": {"peak_energy_baseline": {"command": ["python3", "baseline/peak_energy.py"]}}}
JSON
python3 eval/train/evaluate_train.py --methods "${REGISTRY}" --output "${ROOT}/scoring/baseline_scores_train.json"
