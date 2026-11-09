#!/usr/bin/env python3
"""Uncapped diagnostic: true peak memory and quality of volumetric paths.

The benchmark kills any run above its 256 MB budget, so the gym itself only
records that the full-histogram Quasi-Fresnel variant and the LCT baseline
fail.  This audit reruns them, plus the reference and the simple baseline, on
two visible 256 x 256 train scenes with a 24 GB ceiling to record how much
memory they actually need and what quality they reach.  It reuses the train
harness (method-agnostic runner, metrics) and never touches eval/test/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval" / "train"))
sys.path.insert(0, str(ROOT))

import train_harness as harness  # noqa: E402
from data import nlos_scenes  # noqa: E402

METHODS = {
    "quasi_fresnel": ["python3", "method/run_qf.py"],
    "qf_s0p020_paper": ["python3", "method/run_qf.py", "--s", "0.02"],
    "qf_lean": ["python3", "redteam/hardening/variants.py", "--variant", "lean"],
    "qf_traditional": ["python3", "method/run_qf.py", "--mode", "traditional"],
    "lct_volumetric": ["python3", "baseline/lct.py"],
    "peak_energy_baseline": ["python3", "baseline/peak_energy.py"],
}
SCENES = ("train_256_a", "train_256_b")


def main() -> None:
    out_dir = ROOT / "outputs" / "hardening_audit" / "uncapped"
    out_dir.mkdir(parents=True, exist_ok=True)
    nlos_scenes.ensure_train_scenes()
    spec = {sid: (seed, n) for sid, seed, n in nlos_scenes.TRAIN_SCENES}
    results: dict = {}
    for sid in SCENES:
        seed, n = spec[sid]
        truth = nlos_scenes.ground_truth(nlos_scenes.sample_scene(seed, n))
        stats = harness.scene_reference_stats(*truth)
        results.setdefault("_scene_stats", {})[sid] = stats
        for name, command in METHODS.items():
            pred_path = out_dir / f"{name}_{sid}.npz"
            run = harness.run_method(command, nlos_scenes.TRAIN_DIR / sid, pred_path,
                                     out_dir / f"{name}_{sid}.log", budget_mb=24000.0, timeout_s=3600.0)
            entry = {k: run.get(k) for k in ("exit_code", "peak_rss_mb", "killed", "wall_time_s")}
            if run.get("exit_code") == 0 and not run.get("killed"):
                pred, err = harness.load_prediction(pred_path, n, nlos_scenes.max_observable_depth_m())
                if err:
                    entry["error"] = err
                else:
                    entry.update(harness.scene_metrics(*pred, *truth))
            results.setdefault(name, {})[sid] = entry
            print(sid, name, json.dumps(entry), flush=True)
    target = ROOT / "redteam" / "hardening" / "uncapped_diagnostics.json"
    target.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
