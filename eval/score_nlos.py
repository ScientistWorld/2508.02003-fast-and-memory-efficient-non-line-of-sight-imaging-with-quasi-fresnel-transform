#!/usr/bin/env python3
"""
Convert a method-produced NLOS benchmark report into scoring/scores.json.

This script is method-agnostic: any approach that emits the same experiment
and metric structure can be scored through this entrypoint.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))
from eval.metrics import compute_metrics


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_number(value: object, metric_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"Metric {metric_name!r} must be numeric, got {type(value).__name__}")
    return float(value)


def _diagnostics_path(input_path: Path) -> Path:
    override = os.environ.get("DIAGNOSTICS_PATH")
    if override:
        return Path(override)
    return input_path.parent / "diagnostics.json"


def _load_diagnostics(input_path: Path) -> dict:
    path = _diagnostics_path(input_path)
    if not path.exists():
        return {}
    return _load_json(path)


def _single_method(results: dict, experiment_name: str) -> tuple[str, dict]:
    if not isinstance(results, dict) or not results:
        raise ValueError(f"Experiment {experiment_name!r} must contain at least one method")
    if len(results) != 1:
        raise ValueError(
            f"Experiment {experiment_name!r} must contain exactly one method result; "
            f"found {len(results)}: {list(results.keys())}"
        )
    method_name, method_payload = next(iter(results.items()))
    if not isinstance(method_payload, dict):
        raise ValueError(
            f"Experiment {experiment_name!r} method {method_name!r} must be an object"
        )
    return method_name, method_payload


def _artifact_path(payload: dict, key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Method payload is missing artifact path {key!r}")
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _load_prediction(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(path) as data:
        if "albedo" not in data or "depth" not in data:
            raise ValueError(f"{path} must contain 'albedo' and 'depth' arrays")
        return data["albedo"].astype(np.float64), data["depth"].astype(np.float64)


def _load_ground_truth(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(path) as data:
        if "albedo" not in data or "depth" not in data:
            raise ValueError(f"{path} must contain 'albedo' and 'depth' arrays")
        return data["albedo"].astype(np.float64), data["depth"].astype(np.float64)


def _downsample_mean(image: np.ndarray, out_shape: tuple[int, int]) -> np.ndarray:
    in_h, in_w = image.shape
    out_h, out_w = out_shape
    if (in_h, in_w) == (out_h, out_w):
        return image.astype(np.float64, copy=False)
    if in_h % out_h != 0 or in_w % out_w != 0:
        raise ValueError(f"Cannot evenly downsample from {(in_h, in_w)} to {(out_h, out_w)}")
    sh = in_h // out_h
    sw = in_w // out_w
    return image.reshape(out_h, sh, out_w, sw).mean(axis=(1, 3))


def _score_prediction(prediction_path: Path, ground_truth_path: Path) -> dict[str, float]:
    albedo_pred, depth_pred = _load_prediction(prediction_path)
    albedo_gt, depth_gt = _load_ground_truth(ground_truth_path)
    albedo_gt = _downsample_mean(albedo_gt, albedo_pred.shape)
    depth_gt = _downsample_mean(depth_gt, depth_pred.shape)
    return compute_metrics(albedo_pred, depth_pred, albedo_gt, depth_gt)


def _load_efficiency(path: Path) -> dict:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an object")
    return payload


def _nested(mapping: dict, *keys: str):
    current = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _normalize_results(report: dict, diagnostics: dict) -> dict:
    experiments = report.get("experiments")
    if not isinstance(experiments, dict):
        raise ValueError("Input report must contain an 'experiments' object")

    scores: dict[str, dict] = {"experiments": {}}

    depth_payload = experiments.get("zaragoza_bunny_depth_error")
    if not isinstance(depth_payload, dict) or not isinstance(depth_payload.get("results"), dict):
        raise ValueError("Missing experiment 'zaragoza_bunny_depth_error' in input report")
    method_name, depth_metrics = _single_method(
        depth_payload["results"], "zaragoza_bunny_depth_error"
    )

    quality = _score_prediction(
        _artifact_path(depth_metrics, "prediction_path"),
        _artifact_path(depth_metrics, "ground_truth_path"),
    )
    depth_out = {
        "depth_mae_cm": round(100.0 * quality["depth_mae"], 6),
        "albedo_psnr_db": round(quality["psnr"], 6),
        "albedo_ssim": round(quality["ssim"], 6),
        "albedo_mae": round(quality["albedo_mae"], 6),
    }
    scores["experiments"]["zaragoza_bunny_depth_error"] = {
        "results": {method_name: depth_out}
    }

    efficiency_payload = experiments.get("zaragoza_efficiency_public_bunny")
    if not isinstance(efficiency_payload, dict) or not isinstance(
        efficiency_payload.get("results"), dict
    ):
        raise ValueError("Missing experiment 'zaragoza_efficiency_public_bunny' in input report")
    efficiency_method, efficiency_metrics = _single_method(
        efficiency_payload["results"], "zaragoza_efficiency_public_bunny"
    )
    if efficiency_method != method_name:
        raise ValueError("Input report uses different method names across experiments")

    efficiency = _load_efficiency(_artifact_path(efficiency_metrics, "efficiency_path"))
    complexity = efficiency.get("complexity_scaling", {})
    traditional = complexity.get("traditional", {}) if isinstance(complexity, dict) else {}
    loading = complexity.get("loading", {}) if isinstance(complexity, dict) else {}
    loading_consistency = _nested(efficiency, "loading", "consistency_vs_traditional") or {}
    efficiency_out = {
        "memory_mb": round(
            _require_number(_nested(efficiency, "fdh", "algorithm_peak_mb"), "memory_mb"),
            6,
        ),
        "traditional_memory_order": round(
            _require_number(traditional.get("memory_order"), "traditional_memory_order"),
            6,
        ),
        "loading_memory_order": round(
            _require_number(loading.get("memory_order"), "loading_memory_order"),
            6,
        ),
        "loading_depth_consistency_cm": round(
            100.0
            * _require_number(
                loading_consistency.get("depth_mae"), "loading_depth_consistency_cm"
            ),
            6,
        ),
    }
    scores["experiments"]["zaragoza_efficiency_public_bunny"] = {
        "results": {method_name: efficiency_out}
    }

    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(ROOT / "scoring" / "raw_results.json"),
        help="Method-produced benchmark report to score.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "scoring" / "scores.json"),
        help="Where to write normalized scores.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    report = _load_json(input_path)
    diagnostics = _load_diagnostics(input_path)
    scores = _normalize_results(report, diagnostics)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
