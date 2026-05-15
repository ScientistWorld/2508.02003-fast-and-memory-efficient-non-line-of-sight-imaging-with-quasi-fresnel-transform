#!/usr/bin/env python3
"""
Visible train-slice scorer for the NLOS benchmark.

The input contract mirrors scripts/evaluate.sh: read a method-produced JSON
report plus its companion diagnostics artifact, then write normalized scores.
This file deliberately does not import method code. Any future method that
emits the same report structure can be scored here.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


DEPTH_EXPERIMENT = "zaragoza_bunny_depth_error"
EFFICIENCY_EXPERIMENT = "zaragoza_efficiency_public_bunny"
REQUIRED_EXPERIMENTS = (DEPTH_EXPERIMENT, EFFICIENCY_EXPERIMENT)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"Metric {name!r} must be numeric, got {type(value).__name__}")
    return float(value)


def _optional_number(*values: Any, name: str) -> float:
    for value in values:
        if value is not None:
            return _number(value, name)
    raise KeyError(f"Missing metric {name!r}")


def _diagnostics_path(input_path: Path) -> Path:
    override = os.environ.get("DIAGNOSTICS_PATH")
    if override:
        return Path(override)
    return input_path.parent / "diagnostics.json"


def _experiment_results(report: dict[str, Any], experiment: str) -> dict[str, dict[str, Any]]:
    experiments = report.get("experiments")
    if not isinstance(experiments, dict):
        raise ValueError("Input report must contain an 'experiments' object")
    exp_payload = experiments.get(experiment)
    if not isinstance(exp_payload, dict):
        raise ValueError(f"Missing experiment {experiment!r} in input report")
    results = exp_payload.get("results")
    if not isinstance(results, dict) or not results:
        raise ValueError(f"Experiment {experiment!r} must contain non-empty results")

    out: dict[str, dict[str, Any]] = {}
    for method_name, payload in results.items():
        if not isinstance(method_name, str):
            raise ValueError(f"Experiment {experiment!r} has a non-string method key")
        if not isinstance(payload, dict):
            raise ValueError(
                f"Experiment {experiment!r} method {method_name!r} must be an object"
            )
        out[method_name] = payload
    return out


def _method_names(report: dict[str, Any]) -> list[str]:
    method_sets = [
        set(_experiment_results(report, experiment))
        for experiment in REQUIRED_EXPERIMENTS
    ]
    common = set.intersection(*method_sets)
    if not common:
        raise ValueError("No method appears in every required experiment")
    return sorted(common)


def _diagnostics_for_method(diagnostics: dict[str, Any], method_name: str) -> dict[str, Any]:
    for key in ("methods", "by_method"):
        method_map = diagnostics.get(key)
        if isinstance(method_map, dict) and isinstance(method_map.get(method_name), dict):
            return method_map[method_name]
    return diagnostics


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _quality_metrics(method_diagnostics: dict[str, Any]) -> dict[str, Any]:
    quality = _nested(method_diagnostics, "quality_scene", "traditional", "quality")
    if isinstance(quality, dict):
        return quality
    fallback = _nested(method_diagnostics, "primary_public_scene", "traditional", "quality")
    if isinstance(fallback, dict):
        return fallback
    return {}


def _complexity(method_diagnostics: dict[str, Any]) -> dict[str, Any]:
    complexity = method_diagnostics.get("complexity_scaling")
    return complexity if isinstance(complexity, dict) else {}


def build_scores(report: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    depth_results = _experiment_results(report, DEPTH_EXPERIMENT)
    efficiency_results = _experiment_results(report, EFFICIENCY_EXPERIMENT)

    scores: dict[str, Any] = {
        "experiments": {
            DEPTH_EXPERIMENT: {"results": {}},
            EFFICIENCY_EXPERIMENT: {"results": {}},
        }
    }

    for method_name in _method_names(report):
        method_diagnostics = _diagnostics_for_method(diagnostics, method_name)
        quality = _quality_metrics(method_diagnostics)
        complexity = _complexity(method_diagnostics)

        depth_payload = depth_results[method_name]
        efficiency_payload = efficiency_results[method_name]

        scores["experiments"][DEPTH_EXPERIMENT]["results"][method_name] = {
            "depth_mae_cm": round(
                _optional_number(
                    depth_payload.get("depth_mae_cm"),
                    quality.get("depth_mae_cm"),
                    name="depth_mae_cm",
                ),
                6,
            ),
            "albedo_psnr_db": round(
                _optional_number(
                    depth_payload.get("albedo_psnr_db"),
                    quality.get("psnr"),
                    name="albedo_psnr_db",
                ),
                6,
            ),
            "albedo_mae": round(
                _optional_number(
                    depth_payload.get("albedo_mae"),
                    quality.get("albedo_mae"),
                    name="albedo_mae",
                ),
                6,
            ),
        }

        loading_scaling = complexity.get("loading") if isinstance(complexity, dict) else None
        if not isinstance(loading_scaling, dict):
            loading_scaling = {}
        scores["experiments"][EFFICIENCY_EXPERIMENT]["results"][method_name] = {
            "memory_mb": round(
                _optional_number(efficiency_payload.get("memory_mb"), name="memory_mb"),
                6,
            ),
            "loading_memory_order": round(
                _optional_number(
                    efficiency_payload.get("loading_memory_order"),
                    loading_scaling.get("memory_order"),
                    name="loading_memory_order",
                ),
                6,
            ),
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
        default=str(ROOT / "scoring" / "scores_train.json"),
        help="Where to write normalized train-slice scores.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    diagnostics_path = _diagnostics_path(input_path)

    report = _load_json(input_path)
    diagnostics = _load_json(diagnostics_path)
    scores = build_scores(report, diagnostics)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
