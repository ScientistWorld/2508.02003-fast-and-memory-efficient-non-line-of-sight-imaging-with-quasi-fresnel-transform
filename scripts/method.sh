#!/bin/bash
# Register the reference Quasi-Fresnel method in scoring/methods.json.
#
# A method is any command that accepts `--scene <dir> --output <file.npz>`
# (see briefing/evaluation.md).  The evaluators run every registered command
# on every scene themselves, so registering is all a training-free method needs.
# Existing registrations of other methods are kept.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

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
    "description": "Reference reproduction (paper's sequential-loading variant, s = 0.02 m).",
}
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"Registered quasi_fresnel in {path}: {sorted(data['methods'])}")
PY
