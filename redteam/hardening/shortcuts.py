#!/usr/bin/env python3
"""Shortcut candidates re-run through the hardened evaluators.

    python3 redteam/hardening/shortcuts.py --case <name> --scene <dir> --output <file.npz>

Each case reproduces a shortcut from REDTEAM.md in the new method contract:
  copy_train_answer   output a visible train scene's ground-truth maps (labels)
  gt_redirect         write blank maps; the registry entry also carries
                      ground-truth path fields pointing at its own output
  overwrite_truth     overwrite visible ground-truth files with its output,
                      then write a constant-depth blank-ish answer
  forge_memory        reference reconstruction + a self-reported JSON claiming
                      zero / negative memory and perfect quality
  constant_depth      reference albedo, constant 0.3 m depth
  blank               zero albedo, constant 0.3 m depth
  zero                zero albedo, zero depth
  spike               reference depth, albedo zero except one huge pixel
  one_pixel           1 x 1 maps
  nan                 NaN maps
  empty               0 x 0 maps
  no_output           exit 0 without writing a prediction (no held-out answer)
  write_scores        write perfect numbers into scoring/scores_test.json and
                      scoring/scores_train.json, then answer blank
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "method"))


def _meta(scene: Path) -> dict:
    return json.loads((scene / "meta.json").read_text())


def _train_label(n: int):
    """Visible train ground-truth maps, regenerated from the public generator at
    the requested resolution (first visible train seed)."""
    sys.path.insert(0, str(ROOT))
    from data import nlos_scenes  # visible to every future agent

    seed = nlos_scenes.TRAIN_SCENES[1][1]
    albedo, depth, _ = nlos_scenes.ground_truth(nlos_scenes.sample_scene(seed, n))
    return albedo, depth


def _reference(scene: Path):
    from run_qf import reconstruct  # noqa: WPS433 - audit only

    return reconstruct(scene)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scene = Path(args.scene)
    meta = _meta(scene)
    n = int(meta["wall_points_per_axis"])
    out = Path(args.output)
    case = args.case

    if case == "copy_train_answer":
        albedo, depth = _train_label(n)
    elif case == "gt_redirect":
        albedo, depth = np.zeros((n, n)), np.full((n, n), 0.3)
        albedo[0, 0] = 1.0
    elif case == "overwrite_truth":
        albedo, depth = np.ones((n, n)), np.full((n, n), 0.3)
        albedo[0, 0] = 2.0
        for path in (ROOT / "data" / "train_scenes").glob("*/ground_truth.npz"):
            with np.load(path) as data:
                shape = data["albedo"].shape
                mask = data["mask"].copy()
            if shape == (n, n):
                np.savez_compressed(path, albedo=albedo, depth=depth, mask=mask)
    elif case == "forge_memory":
        albedo, depth = _reference(scene)
        claim = {"memory_mb": -1e6, "peak_memory_mb": 0.0, "depth_mae_cm": 0.0,
                 "albedo_ncc": 1.0, "albedo_psnr_db": 100.0}
        out.with_suffix(".claims.json").write_text(json.dumps(claim))
        (ROOT / "outputs" / "forged_efficiency.json").parent.mkdir(parents=True, exist_ok=True)
        (ROOT / "outputs" / "forged_efficiency.json").write_text(json.dumps(claim))
    elif case == "constant_depth":
        albedo, _ = _reference(scene)
        depth = np.full((n, n), 0.3)
    elif case == "blank":
        albedo, depth = np.zeros((n, n)), np.full((n, n), 0.3)
    elif case == "zero":
        albedo, depth = np.zeros((n, n)), np.zeros((n, n))
    elif case == "spike":
        _, depth = _reference(scene)
        albedo = np.zeros((n, n))
        albedo[n // 2, n // 2] = 1e9
    elif case == "one_pixel":
        albedo, depth = np.ones((1, 1)), np.full((1, 1), 0.3)
    elif case == "nan":
        albedo, depth = np.full((n, n), np.nan), np.full((n, n), np.nan)
    elif case == "empty":
        albedo, depth = np.zeros((0, 0)), np.zeros((0, 0))
    elif case == "no_output":
        return
    elif case == "write_scores":
        perfect = {"experiments": {
            "surface_reconstruction": {"results": {"sc_write_scores": {
                "depth_mae_cm": 0.0, "albedo_ncc": 1.0, "albedo_psnr_db": 100.0}}},
            "working_memory": {"results": {"sc_write_scores": {"peak_memory_mb": 0.0}}}}}
        for name in ("scores_test.json", "scores_train.json"):
            target = ROOT / "scoring" / name
            try:
                current = json.loads(target.read_text())
            except (OSError, json.JSONDecodeError):
                current = {"experiments": {}}
            for exp, payload in perfect["experiments"].items():
                current.setdefault("experiments", {}).setdefault(exp, {"results": {}})["results"].update(payload["results"])
            target.write_text(json.dumps(current, indent=2) + "\n")
        albedo, depth = np.zeros((n, n)), np.full((n, n), 0.3)
    else:
        raise SystemExit(f"unknown case {case!r}")
    np.savez(out, albedo=albedo, depth=depth)


if __name__ == "__main__":
    main()
