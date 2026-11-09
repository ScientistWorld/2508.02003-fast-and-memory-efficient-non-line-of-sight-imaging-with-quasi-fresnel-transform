#!/bin/bash
# Register the reference Quasi-Fresnel method in scoring/methods.json.
#
# A method is any command that accepts `--scene <dir> --output <file.npz>`
# (see briefing/evaluation.md).  The evaluators run every registered command
# on every scene themselves, so registering is all a training-free method needs.
# Existing registrations of other methods are kept.
#   bash scripts/method.sh --select-s   also re-selects s on the visible train scenes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

if [ "${1:-}" = "--select-s" ]; then
    # Re-select the operating point s on the visible train scenes (writes method/qf_params.json).
    GRID_REGISTRY="$(mktemp -p outputs 2>/dev/null || mktemp)"
    GRID_SCORES="${GRID_REGISTRY}.scores.json"
    python3 method/select_s.py --write-registry "${GRID_REGISTRY}"
    python3 eval/train/evaluate_train.py --methods "${GRID_REGISTRY}" --output "${GRID_SCORES}"
    python3 method/select_s.py --choose "${GRID_SCORES}"
    rm -f "${GRID_REGISTRY}" "${GRID_SCORES}"
fi

python3 - <<'PY'
import json
from pathlib import Path

path = Path("scoring/methods.json")
data = {"methods": {}}
if path.exists():
    try:
        loaded = json.loads(path.read_text())
        if isinstance(loaded, dict) and isinstance(loaded.get("methods"), dict):
            data = loaded
    except json.JSONDecodeError:
        pass
data["methods"]["quasi_fresnel"] = {
    "command": ["python3", "method/run_qf.py"],
    "description": "Reference reproduction (paper's sequential-loading variant; s from method/qf_params.json).",
}
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"Registered quasi_fresnel in {path}: {sorted(data['methods'])}")
PY
