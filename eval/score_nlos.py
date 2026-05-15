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

    depth_out = {
        "depth_mae_cm": round(
            _require_number(depth_metrics.get("depth_mae_cm"), "depth_mae_cm"), 6
        )
    }
    quality = (
        diagnostics.get("primary_public_scene", {})
        .get("traditional", {})
        .get("quality", {})
    )
    if quality:
        if "psnr" in quality:
            depth_out["albedo_psnr_db"] = round(
                _require_number(quality.get("psnr"), "albedo_psnr_db"), 6
            )
        if "ssim" in quality:
            depth_out["albedo_ssim"] = round(
                _require_number(quality.get("ssim"), "albedo_ssim"), 6
            )
        if "albedo_mae" in quality:
            depth_out["albedo_mae"] = round(
                _require_number(quality.get("albedo_mae"), "albedo_mae"), 6
            )
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

    efficiency_out = {
        "runtime_s": round(_require_number(efficiency_metrics.get("runtime_s"), "runtime_s"), 6),
        "memory_mb": round(_require_number(efficiency_metrics.get("memory_mb"), "memory_mb"), 6),
    }
    complexity = diagnostics.get("complexity_scaling", {})
    loading_consistency = (
        diagnostics.get("primary_public_scene", {})
        .get("loading", {})
        .get("consistency_vs_traditional", {})
    )
    if complexity:
        traditional = complexity.get("traditional", {})
        loading = complexity.get("loading", {})
        if "runtime_order" in traditional:
            efficiency_out["traditional_runtime_order"] = round(
                _require_number(traditional.get("runtime_order"), "traditional_runtime_order"),
                6,
            )
        if "memory_order" in loading:
            efficiency_out["loading_memory_order"] = round(
                _require_number(loading.get("memory_order"), "loading_memory_order"),
                6,
            )
    if "depth_mae" in loading_consistency:
        efficiency_out["loading_depth_consistency_cm"] = round(
            100.0
            * _require_number(
                loading_consistency.get("depth_mae"), "loading_depth_consistency_cm"
            ),
            6,
        )
    scores["experiments"]["zaragoza_efficiency_public_bunny"] = {
        "results": {method_name: efficiency_out}
    }

    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="/home/user/scoring/raw_results.json",
        help="Method-produced benchmark report to score.",
    )
    parser.add_argument(
        "--output",
        default="/home/user/scoring/scores.json",
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
