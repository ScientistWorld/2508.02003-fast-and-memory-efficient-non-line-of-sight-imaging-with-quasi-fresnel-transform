#!/usr/bin/env python3
"""
Evaluate the Quasi-Fresnel implementation on Zaragoza-style confocal scenes.

The scored path targets the paper's central claim on Zaragoza data:
- depth quality on a tracked synthetic bunny proxy with metric ground truth
- runtime and memory efficiency on public Zaragoza HDF5 measurements
"""

from __future__ import annotations

import json
import os
import resource
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

ROOT = Path("/home/user")
sys.path.insert(0, str(ROOT))
METHOD_NAME = "quasi_fresnel_scaled_reproduction"

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from data.load_zaragoza import load_zaragoza_hdf5
from eval.metrics import compute_metrics
from method.quasi_fresnel import (
    quasi_fresnel_reconstruct,
    quasi_fresnel_time_integral,
    quasi_fresnel_time_integral_loading,
)


def _linux_maxrss_mb() -> float:
    """Return ru_maxrss in MB on Linux."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _downsample_mean(image: np.ndarray, out_shape: tuple[int, int]) -> np.ndarray:
    """Average-pool an image to a smaller shape."""
    in_h, in_w = image.shape
    out_h, out_w = out_shape
    if (in_h, in_w) == (out_h, out_w):
        return image.astype(np.float64, copy=False)
    if in_h % out_h != 0 or in_w % out_w != 0:
        raise ValueError(
            f"Cannot evenly downsample from {(in_h, in_w)} to {(out_h, out_w)}"
        )
    sh = in_h // out_h
    sw = in_w // out_w
    return image.reshape(out_h, sh, out_w, sw).mean(axis=(1, 3))


def _scene_quality_metrics(
    albedo_pred: np.ndarray,
    depth_pred: np.ndarray,
    albedo_gt: np.ndarray,
    depth_gt: np.ndarray,
) -> dict[str, float]:
    albedo_gt_small = _downsample_mean(albedo_gt, albedo_pred.shape)
    depth_gt_small = _downsample_mean(depth_gt, depth_pred.shape)
    return compute_metrics(albedo_pred, depth_pred, albedo_gt_small, depth_gt_small)


def benchmark_qft(
    tau: np.ndarray,
    s: float,
    dt: float,
    k: int,
    area: float,
    wall_x: np.ndarray | None = None,
    wall_y: np.ndarray | None = None,
    integration_mode: str = "traditional",
    repeats: int = 3,
) -> dict[str, object]:
    runtimes: list[float] = []
    algorithm_peak_mb: list[float] = []
    rss_growth_mb: list[float] = []
    albedo = None
    depth = None

    initial_rss_before = _linux_maxrss_mb()
    for _ in range(repeats):
        rss_before = _linux_maxrss_mb()
        tracemalloc.start()
        t0 = time.perf_counter()
        albedo, depth = quasi_fresnel_reconstruct(
            tau,
            s=s,
            dt=dt,
            k=k,
            area=area,
            wall_x=wall_x,
            wall_y=wall_y,
            integration_mode=integration_mode,
        )
        runtimes.append(time.perf_counter() - t0)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rss_after = _linux_maxrss_mb()
        tracemalloc_peak_mb = peak / (1024.0 * 1024.0)
        rss_delta_mb = max(0.0, rss_after - rss_before)
        algorithm_peak_mb.append(max(tracemalloc_peak_mb, rss_delta_mb))
        rss_growth_mb.append(rss_delta_mb)
    rss_after = _linux_maxrss_mb()

    return {
        "albedo": albedo,
        "depth": depth,
        "integration_mode": integration_mode,
        "runtime_mean_s": float(np.mean(runtimes)),
        "runtime_std_s": float(np.std(runtimes)),
        "runtime_min_s": float(np.min(runtimes)),
        "runtime_max_s": float(np.max(runtimes)),
        "maxrss_mb": max(initial_rss_before, rss_after),
        "algorithm_peak_mb": float(np.max(algorithm_peak_mb)),
        "rss_growth_mb": float(np.max(rss_growth_mb)),
    }


def _scene_parameter_s(scene_name: str) -> float:
    if "synthetic_bunny" in scene_name.lower():
        return 0.025
    return 0.025 if "usaf" in scene_name.lower() else 0.02


def load_public_scene(path: Path) -> dict[str, object]:
    hdf5_data = load_zaragoza_hdf5(path)
    return {
        "tau": hdf5_data["tau"],
        "albedo": hdf5_data["albedo"],
        "depth": hdf5_data["depth"],
        "has_ground_truth": bool(
            hdf5_data.get("has_albedo_gt", False) and hdf5_data.get("has_depth_gt", False)
        ),
        "depth_metric_scale": bool(hdf5_data.get("depth_metric_scale", False)),
        "dt": float(hdf5_data["dt"]),
        "k": int(hdf5_data["k"]),
        "area": float(hdf5_data["area"]),
        "scene_name": str(hdf5_data["scene_name"]),
        "source_path": str(path),
        "wall_x": hdf5_data.get("wall_x"),
        "wall_y": hdf5_data.get("wall_y"),
    }


def load_synthetic_quality_scene() -> dict[str, object]:
    path = ROOT / "data" / "bunny" / "bunny_64x64.npz"
    if not path.exists():
        raise FileNotFoundError(f"Missing tracked synthetic quality scene: {path}")
    with np.load(path) as data:
        return {
            "tau": data["tau"].astype(np.float64),
            "albedo": data["albedo"].astype(np.float64),
            "depth": data["depth"].astype(np.float64),
            "has_ground_truth": True,
            "depth_metric_scale": True,
            "dt": float(data["dt"]),
            "k": int(data["k"]),
            "area": float(data["area"]),
            "scene_name": "synthetic_bunny_proxy_64",
            "source_path": str(path),
            "wall_x": None,
            "wall_y": None,
        }


def load_public_efficiency_scene() -> dict[str, object]:
    candidates = [
        ROOT / "data" / "zaragoza" / "bunny_conf64.hdf5",
        ROOT / "data" / "downloads" / "zaragoza" / "bunny_simple_256_conf.hdf5",
    ]
    for path in candidates:
        if not path.exists():
            continue
        return load_public_scene(path)
    raise FileNotFoundError(
        "No public bunny Zaragoza scene was found for efficiency evaluation. "
        "Expected one of: " + ", ".join(str(path) for path in candidates)
    )


def discover_additional_public_scenes() -> list[Path]:
    candidates = [
        ROOT / "data" / "downloads" / "zaragoza" / "usaf_simple_256_conf.hdf5",
        ROOT / "data" / "downloads" / "zaragoza" / "public" / "T_conf64.hdf5",
    ]
    return [path for path in candidates if path.exists()]


def build_scores(
    quality_metrics: dict[str, float],
    efficiency_result: dict[str, object],
) -> dict[str, object]:
    return {
        "experiments": {
            "zaragoza_bunny_depth_error": {
                "results": {
                    METHOD_NAME: {
                        "depth_mae_cm": round(quality_metrics["depth_mae"] * 100.0, 4),
                    }
                }
            },
            "zaragoza_efficiency_public_bunny": {
                "results": {
                    METHOD_NAME: {
                        "runtime_s": round(efficiency_result["runtime_mean_s"], 6),
                        "memory_mb": round(efficiency_result["algorithm_peak_mb"], 2),
                    }
                }
            },
        }
    }


def build_diagnostics(
    quality_scene: dict[str, object],
    quality_result: dict[str, object],
    quality_metrics: dict[str, float],
    efficiency_scene: dict[str, object],
    efficiency_result: dict[str, object],
    loading_result: dict[str, object],
    loading_consistency: dict[str, float],
    scaling: dict[str, dict[str, object]],
    public_scene_results: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "quality_scene": {
            "scene_name": quality_scene["scene_name"],
            "source_path": quality_scene["source_path"],
            "dt": round(float(quality_scene["dt"]), 8),
            "area_m": round(float(quality_scene["area"]), 6),
            "note": (
                "Tracked synthetic proxy with metric albedo/depth ground truth. "
                "The public Zaragoza HDF5 files packaged here contain measurements "
                "but no 2D albedo/depth targets."
            ),
            "traditional": {
                "runtime_mean_s": round(quality_result["runtime_mean_s"], 6),
                "runtime_std_s": round(quality_result["runtime_std_s"], 6),
                "runtime_min_s": round(quality_result["runtime_min_s"], 6),
                "runtime_max_s": round(quality_result["runtime_max_s"], 6),
                "maxrss_mb": round(quality_result["maxrss_mb"], 2),
                "algorithm_peak_mb": round(quality_result["algorithm_peak_mb"], 2),
                "quality": {
                    "psnr": round(quality_metrics["psnr"], 4),
                    "ssim": round(quality_metrics["ssim"], 4),
                    "albedo_mae": round(quality_metrics["albedo_mae"], 6),
                    "depth_mae_m": round(quality_metrics["depth_mae"], 6),
                    "depth_mae_cm": round(quality_metrics["depth_mae"] * 100.0, 4),
                },
            },
        },
        "primary_public_scene": {
            "scene_name": efficiency_scene["scene_name"],
            "source_path": efficiency_scene["source_path"],
            "dt": round(float(efficiency_scene["dt"]), 8),
            "area_m": round(float(efficiency_scene["area"]), 6),
            "has_ground_truth": bool(efficiency_scene["has_ground_truth"]),
            "depth_metric_scale": bool(efficiency_scene["depth_metric_scale"]),
            "traditional": {
                "runtime_mean_s": round(efficiency_result["runtime_mean_s"], 6),
                "runtime_std_s": round(efficiency_result["runtime_std_s"], 6),
                "runtime_min_s": round(efficiency_result["runtime_min_s"], 6),
                "runtime_max_s": round(efficiency_result["runtime_max_s"], 6),
                "maxrss_mb": round(efficiency_result["maxrss_mb"], 2),
                "algorithm_peak_mb": round(efficiency_result["algorithm_peak_mb"], 2),
            },
            "loading": {
                "runtime_mean_s": round(loading_result["runtime_mean_s"], 6),
                "runtime_std_s": round(loading_result["runtime_std_s"], 6),
                "runtime_min_s": round(loading_result["runtime_min_s"], 6),
                "runtime_max_s": round(loading_result["runtime_max_s"], 6),
                "maxrss_mb": round(loading_result["maxrss_mb"], 2),
                "algorithm_peak_mb": round(loading_result["algorithm_peak_mb"], 2),
                "consistency_vs_traditional": {
                    "psnr": round(loading_consistency["psnr"], 4),
                    "ssim": round(loading_consistency["ssim"], 6),
                    "albedo_mae": round(loading_consistency["albedo_mae"], 8),
                    "depth_mae": round(loading_consistency["depth_mae"], 8),
                },
            },
        },
        "complexity_scaling": scaling,
        "additional_public_scenes": public_scene_results,
    }


def _fit_scaling_order(sizes: list[int], values: list[float]) -> float:
    x = np.log(np.asarray(sizes, dtype=np.float64))
    y = np.log(np.asarray(values, dtype=np.float64))
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)


def benchmark_complexity_scaling(
    sizes: tuple[int, ...] = (32, 64, 96, 128),
    s: float = 0.02,
    dt: float = 0.003,
    k: int = 4,
) -> dict[str, dict[str, object]]:
    ds = 1e-7
    rng = np.random.default_rng(250802003)
    per_mode: dict[str, dict[str, list[float]]] = {
        "traditional": {"runtime_s": [], "memory_mb": []},
        "loading": {"runtime_s": [], "memory_mb": []},
    }

    for n in sizes:
        tau = rng.random((n, n, n), dtype=np.float64)
        for mode in ("traditional", "loading"):
            runtimes: list[float] = []
            peaks_mb: list[float] = []
            for _ in range(3):
                tracemalloc.start()
                t0 = time.perf_counter()
                if mode == "traditional":
                    quasi_fresnel_time_integral(tau, s - ds, dt, k)
                    quasi_fresnel_time_integral(tau, s, dt, k)
                    quasi_fresnel_time_integral(tau, s + ds, dt, k)
                else:
                    quasi_fresnel_time_integral_loading(tau, (s - ds, s, s + ds), dt, k)
                runtimes.append(time.perf_counter() - t0)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peaks_mb.append(peak / (1024.0 * 1024.0))
            per_mode[mode]["runtime_s"].append(float(np.mean(runtimes)))
            per_mode[mode]["memory_mb"].append(float(np.max(peaks_mb)))

    summary: dict[str, dict[str, object]] = {}
    for mode, metrics in per_mode.items():
        summary[mode] = {
            "sizes": list(sizes),
            "runtime_s": [round(v, 6) for v in metrics["runtime_s"]],
            "memory_mb": [round(v, 4) for v in metrics["memory_mb"]],
            "runtime_order": _fit_scaling_order(list(sizes), metrics["runtime_s"]),
            "memory_order": _fit_scaling_order(list(sizes), metrics["memory_mb"]),
        }
    return summary


def main() -> None:
    print("=== Synthetic Quality Proxy Scene ===")
    quality_scene = load_synthetic_quality_scene()
    quality_s = _scene_parameter_s(quality_scene["scene_name"])
    quality_result = benchmark_qft(
        quality_scene["tau"],
        s=quality_s,
        dt=quality_scene["dt"],
        k=quality_scene["k"],
        area=quality_scene["area"],
        wall_x=quality_scene["wall_x"],
        wall_y=quality_scene["wall_y"],
        repeats=3,
    )
    quality_metrics = _scene_quality_metrics(
        quality_result["albedo"],
        quality_result["depth"],
        quality_scene["albedo"],
        quality_scene["depth"],
    )
    print(
        f"scene={quality_scene['scene_name']} s={quality_s:.3f} "
        f"runtime={quality_result['runtime_mean_s']:.6f}s +/- {quality_result['runtime_std_s']:.6f}s "
        f"peak_memory={quality_result['algorithm_peak_mb']:.2f}MB"
    )
    print(
        "quality "
        f"PSNR={quality_metrics['psnr']:.2f}dB "
        f"SSIM={quality_metrics['ssim']:.4f} "
        f"albedo_MAE={quality_metrics['albedo_mae']:.4f} "
        f"depth_MAE={quality_metrics['depth_mae'] * 100.0:.4f}cm"
    )

    print("\n=== Public Zaragoza Efficiency Scene ===")
    efficiency_scene = load_public_efficiency_scene()
    efficiency_s = _scene_parameter_s(efficiency_scene["scene_name"])
    efficiency_result = benchmark_qft(
        efficiency_scene["tau"],
        s=efficiency_s,
        dt=efficiency_scene["dt"],
        k=efficiency_scene["k"],
        area=efficiency_scene["area"],
        wall_x=efficiency_scene["wall_x"],
        wall_y=efficiency_scene["wall_y"],
        repeats=3,
    )
    print(
        f"scene={efficiency_scene['scene_name']} s={efficiency_s:.3f} "
        f"runtime={efficiency_result['runtime_mean_s']:.6f}s +/- {efficiency_result['runtime_std_s']:.6f}s "
        f"peak_memory={efficiency_result['algorithm_peak_mb']:.2f}MB "
        f"ground_truth={efficiency_scene['has_ground_truth']}"
    )

    print("\n=== Public Scene: Sequential Loading Variant ===")
    loading_result = benchmark_qft(
        efficiency_scene["tau"],
        s=efficiency_s,
        dt=efficiency_scene["dt"],
        k=efficiency_scene["k"],
        area=efficiency_scene["area"],
        wall_x=efficiency_scene["wall_x"],
        wall_y=efficiency_scene["wall_y"],
        integration_mode="loading",
        repeats=3,
    )
    loading_consistency = compute_metrics(
        loading_result["albedo"],
        loading_result["depth"],
        efficiency_result["albedo"],
        efficiency_result["depth"],
    )
    print(
        f"scene={efficiency_scene['scene_name']} s={efficiency_s:.3f} "
        f"mode=loading runtime={loading_result['runtime_mean_s']:.6f}s "
        f"+/- {loading_result['runtime_std_s']:.6f}s "
        f"peak_memory={loading_result['algorithm_peak_mb']:.2f}MB"
    )
    print(
        "consistency_vs_traditional "
        f"PSNR={loading_consistency['psnr']:.2f}dB "
        f"SSIM={loading_consistency['ssim']:.6f} "
        f"albedo_MAE={loading_consistency['albedo_mae']:.8f} "
        f"depth_MAE={loading_consistency['depth_mae']:.8f}"
    )

    print("\n=== Complexity Scaling ===")
    scaling = benchmark_complexity_scaling()
    for mode in ("traditional", "loading"):
        print(
            f"{mode} runtime_order={scaling[mode]['runtime_order']:.3f} "
            f"memory_order={scaling[mode]['memory_order']:.3f} "
            f"sizes={scaling[mode]['sizes']} "
            f"algorithm_peak_mb={scaling[mode]['memory_mb']}"
        )

    public_scene_results: list[dict[str, object]] = []
    additional_scenes = discover_additional_public_scenes()
    if additional_scenes:
        print("\n=== Additional Public Zaragoza Scenes ===")
    for scene_path in additional_scenes:
        public_scene = load_public_scene(scene_path)
        public_s = _scene_parameter_s(public_scene["scene_name"])
        public_result = benchmark_qft(
            public_scene["tau"],
            s=public_s,
            dt=public_scene["dt"],
            k=public_scene["k"],
            area=public_scene["area"],
            wall_x=public_scene["wall_x"],
            wall_y=public_scene["wall_y"],
            repeats=2,
        )
        scene_diag = {
            "scene_name": public_scene["scene_name"],
            "source_path": str(scene_path),
            "s": round(public_s, 4),
            "runtime_mean_s": round(public_result["runtime_mean_s"], 6),
            "runtime_std_s": round(public_result["runtime_std_s"], 6),
            "maxrss_mb": round(public_result["maxrss_mb"], 2),
            "algorithm_peak_mb": round(public_result["algorithm_peak_mb"], 2),
            "has_ground_truth": bool(public_scene["has_ground_truth"]),
            "depth_metric_scale": bool(public_scene["depth_metric_scale"]),
        }
        if public_scene["has_ground_truth"] and public_scene["depth_metric_scale"]:
            public_metrics = _scene_quality_metrics(
                public_result["albedo"],
                public_result["depth"],
                public_scene["albedo"],
                public_scene["depth"],
            )
            scene_diag["quality"] = {
                "psnr": round(public_metrics["psnr"], 4),
                "ssim": round(public_metrics["ssim"], 4),
                "albedo_mae": round(public_metrics["albedo_mae"], 6),
                "depth_mae_m": round(public_metrics["depth_mae"], 6),
                "depth_mae_cm": round(public_metrics["depth_mae"] * 100.0, 4),
            }
            print(
                f"scene={public_scene['scene_name']} s={public_s:.3f} "
                f"runtime={public_result['runtime_mean_s']:.6f}s "
                f"peak_memory={public_result['algorithm_peak_mb']:.2f}MB "
                f"PSNR={public_metrics['psnr']:.2f}dB "
                f"SSIM={public_metrics['ssim']:.4f} "
                f"depth_MAE={public_metrics['depth_mae'] * 100.0:.4f}cm"
            )
        else:
            print(
                f"scene={public_scene['scene_name']} s={public_s:.3f} "
                f"runtime={public_result['runtime_mean_s']:.6f}s "
                f"peak_memory={public_result['algorithm_peak_mb']:.2f}MB "
                "quality=unavailable"
            )
        public_scene_results.append(scene_diag)

    scores = build_scores(quality_metrics, efficiency_result)
    out_path = ROOT / "scoring" / "raw_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scores, indent=2) + "\n")
    print(f"\nWrote {out_path}")

    diagnostics = build_diagnostics(
        quality_scene,
        quality_result,
        quality_metrics,
        efficiency_scene,
        efficiency_result,
        loading_result,
        loading_consistency,
        scaling,
        public_scene_results,
    )
    diag_path = ROOT / "scoring" / "diagnostics.json"
    diag_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(f"Wrote {diag_path}")


if __name__ == "__main__":
    main()
