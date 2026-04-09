#!/usr/bin/env python3
"""
Convert a method-produced NLOS benchmark report into scoring/scores.json.

This script is method-agnostic: any approach that emits the same experiment
and metric structure can be scored through this entrypoint.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "zaragoza_efficiency_real_sample": {
        "quasi_fresnel_proposed": ("runtime_s", "memory_mb"),
    },
    "complexity_scaling_cubic_measurements": {
        "quasi_fresnel_traditional": ("memory_order",),
        "quasi_fresnel_loading": ("memory_order",),
    },
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_number(value: object, metric_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"Metric {metric_name!r} must be numeric, got {type(value).__name__}")
    return float(value)


def _normalize_results(report: dict) -> dict:
    experiments = report.get("experiments")
    if not isinstance(experiments, dict):
        raise ValueError("Input report must contain an 'experiments' object")

    scores: dict[str, dict] = {"experiments": {}}
    for experiment_name, methods in REQUIRED.items():
        experiment_payload = experiments.get(experiment_name)
        if not isinstance(experiment_payload, dict):
            raise ValueError(f"Missing experiment {experiment_name!r} in input report")
        result_payload = experiment_payload.get("results")
        if not isinstance(result_payload, dict):
            raise ValueError(f"Experiment {experiment_name!r} must contain a 'results' object")

        normalized_methods: dict[str, dict[str, float]] = {}
        for method_name, metric_names in methods.items():
            method_payload = result_payload.get(method_name)
            if not isinstance(method_payload, dict):
                raise ValueError(
                    f"Experiment {experiment_name!r} is missing method {method_name!r}"
                )
            normalized_metrics: dict[str, float] = {}
            for metric_name in metric_names:
                normalized_metrics[metric_name] = round(
                    _require_number(method_payload.get(metric_name), metric_name), 6
                )
            normalized_methods[method_name] = normalized_metrics

        scores["experiments"][experiment_name] = {"results": normalized_methods}

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
    scores = _normalize_results(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
