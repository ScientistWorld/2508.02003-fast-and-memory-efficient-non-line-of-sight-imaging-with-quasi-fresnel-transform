#!/usr/bin/env python3
"""Select the Quasi-Fresnel parameter s on the visible train scenes.

The paper fixes s per dataset (Zaragoza 0.02 m, USAF 0.025 m, Stanford
0.05-0.10 m) and notes that its admissible range is set by sampling density and
signal-to-noise ratio.  This benchmark's scenes carry shot noise, so s is
chosen once, on the visible train scenes only, from a fixed grid:

    python3 method/select_s.py --write-registry /tmp/grid.json
    python3 eval/train/evaluate_train.py --methods /tmp/grid.json --output /tmp/grid_scores.json
    python3 method/select_s.py --choose /tmp/grid_scores.json     # writes method/qf_params.json

The choice maximises the benchmark's own quality aggregate (coefficient-weighted,
direction-corrected improvement over the grid's first valid entry, each metric
divided by its spread across the grid), ignoring entries that fail.  Working
memory is excluded: s does not change the computation's memory, so its
differences across the grid are measurement jitter (~1 MB) that would be
magnified by the tiny spread.
(`bash scripts/method.sh --select-s` runs all three steps.)
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GRID = (0.02, 0.025, 0.03, 0.035, 0.04, 0.05)


def _name(s: float) -> str:
    return f"qf_select_s{s:.3f}".replace(".", "p")


def write_registry(path: Path) -> None:
    methods = {_name(s): {"command": ["python3", "method/run_qf.py", "--s", repr(s)]} for s in GRID}
    path.write_text(json.dumps({"methods": methods}, indent=2) + "\n")


def choose(scores_path: Path) -> float:
    scores = json.loads(scores_path.read_text())
    reference = json.loads((ROOT / "scoring" / "reference.json").read_text())
    specs = [(exp, metric, float(p["weight"]), abs(float(m["coefficient"])), 1 if m["higher_is_better"] else -1)
             for exp, p in reference["experiments"].items() for metric, m in p["metrics"].items()
             if exp == "surface_reconstruction"]
    all_specs = [(exp, metric) for exp, p in reference["experiments"].items() for metric in p["metrics"]]
    names = [_name(s) for s in GRID]
    valid = [n for n in names if scores["_status"][n]["valid"]]
    if not valid:
        raise SystemExit("no grid value passes the benchmark constraints")

    def val(n, e, m):
        return float(scores["experiments"][e]["results"][n][m])

    totals = {}
    for n in valid:
        total = 0.0
        for e, m, w, c, d in specs:
            sd = statistics.pstdev([val(v, e, m) for v in valid]) if len(valid) > 1 else 0.0
            if sd > 0:
                total += w * c * d * (val(n, e, m) - val(valid[0], e, m)) / sd
        totals[n] = total
    best = max(valid, key=lambda n: (round(totals[n], 9), -GRID[names.index(n)]))
    s_best = GRID[names.index(best)]
    record = {
        "s": s_best,
        "selected_by": "method/select_s.py on the visible train scenes",
        "grid": list(GRID),
        "train_quality_aggregate_by_s": {str(GRID[names.index(n)]): round(t, 6) for n, t in totals.items()},
        "train_metrics_by_s": {str(GRID[names.index(n)]): {
            m: val(n, e, m) for e, m in all_specs} for n in names},
        "paper_zaragoza_s": 0.02,
    }
    (HERE / "qf_params.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return s_best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-registry")
    parser.add_argument("--choose")
    args = parser.parse_args()
    if args.write_registry:
        write_registry(Path(args.write_registry))
    if args.choose:
        choose(Path(args.choose))


if __name__ == "__main__":
    main()
