#!/usr/bin/env python3
"""Hidden test evaluation: run every registered method on hidden scenes.

Usage (no arguments scores every method registered in scoring/methods.json):
    python3 eval/test/evaluate_test.py [--methods scoring/methods.json] [--output scoring/scores_test.json]

Hidden measurements are rendered at test time into a temporary directory that
is deleted after each scene; ground truth stays in this process.  Each method
runs as a fresh process per scene through the same command-line contract as
the train evaluation.  No prediction or metric written by a method is trusted:
the evaluator validates the prediction arrays, recomputes every metric, and
measures peak resident memory of the method's process tree itself.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import test_harness as harness  # noqa: E402
import test_scenes as scenes  # noqa: E402


class HiddenScenes(harness.SceneProvider):
    def __init__(self) -> None:
        self.spec = {sid: (seed, n) for sid, seed, n in scenes.HIDDEN_SCENES}
        self.scenes = [(sid, n) for sid, _, n in scenes.HIDDEN_SCENES]
        self.depth_max_m = scenes.max_observable_depth_m()
        self._scratch = Path(tempfile.mkdtemp(prefix="nlos_hidden_"))
        self._cache: dict[str, dict] = {}

    def _scene(self, scene_id):
        if scene_id not in self._cache:
            seed, n = self.spec[scene_id]
            self._cache[scene_id] = scenes.sample_scene(seed, n)
        return self._cache[scene_id]

    def ground_truth(self, scene_id):
        truth = scenes.ground_truth(self._scene(scene_id))
        return truth

    def prepare(self, scene_id):
        seed, n = self.spec[scene_id]
        directory = self._scratch / f"scene_{n}"
        scenes.write_scene_inputs(directory, seed, n, scene=self._scene(scene_id))
        return directory

    def release(self, scene_id):
        self._cache.pop(scene_id, None)
        shutil.rmtree(self._scratch / f"scene_{self.spec[scene_id][1]}", ignore_errors=True)

    def close(self):
        shutil.rmtree(self._scratch, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--methods", default=str(ROOT / "scoring" / "methods.json"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "scores_test.json"))
    parser.add_argument("--rescore", default=None, help="recompute scores from a kept-prediction directory")
    args = parser.parse_args()

    keep = os.environ.get("NLOS_AUDIT_DIR")
    provider = HiddenScenes()
    try:
        scores = harness.evaluate(
            provider,
            Path(args.methods),
            Path(args.output),
            keep_dir=Path(keep) if keep else None,
            keep_predictions_under_outputs=False,
            rescore_dir=Path(args.rescore) if args.rescore else None,
            log=lambda msg: print(msg, flush=True),
        )
    finally:
        provider.close()
    harness.print_summary(scores)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
