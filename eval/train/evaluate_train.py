#!/usr/bin/env python3
"""Visible (train) evaluation: run every registered method on the public train scenes.

Usage (no arguments scores every method registered in scoring/methods.json):
    python3 eval/train/evaluate_train.py [--methods scoring/methods.json] [--output scoring/scores_train.json]

The train scenes and their ground truth are public (data/train_scenes/,
regenerated deterministically by data/nlos_scenes.py).  Ground truth used for
scoring is recomputed from the scene generator, never read from files a method
could edit.  Predictions are kept under outputs/<method>/train_predictions/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import train_harness as harness  # noqa: E402
from data import nlos_scenes  # noqa: E402


class TrainScenes(harness.SceneProvider):
    def __init__(self) -> None:
        nlos_scenes.ensure_train_scenes()
        self.spec = {sid: (seed, n) for sid, seed, n in nlos_scenes.TRAIN_SCENES}
        self.scenes = [(sid, n) for sid, _, n in nlos_scenes.TRAIN_SCENES]
        self.depth_max_m = nlos_scenes.max_observable_depth_m()

    def ground_truth(self, scene_id):
        seed, n = self.spec[scene_id]
        return nlos_scenes.ground_truth(nlos_scenes.sample_scene(seed, n))

    def prepare(self, scene_id):
        return nlos_scenes.TRAIN_DIR / scene_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--methods", default=str(ROOT / "scoring" / "methods.json"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_train.json"))
    parser.add_argument("--rescore", default=None, help="recompute scores from a kept-prediction directory")
    args = parser.parse_args()

    keep = os.environ.get("NLOS_AUDIT_DIR")
    scores = harness.evaluate(
        TrainScenes(),
        Path(args.methods),
        Path(args.output),
        keep_dir=Path(keep) if keep else None,
        keep_predictions_under_outputs=True,
        rescore_dir=Path(args.rescore) if args.rescore else None,
        log=lambda msg: print(msg, flush=True),
    )
    harness.print_summary(scores)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
