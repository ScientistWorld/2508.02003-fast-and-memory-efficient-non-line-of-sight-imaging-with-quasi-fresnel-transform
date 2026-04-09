#!/usr/bin/env python3
"""
Evaluate the Quasi-Fresnel implementation on the bundled real Zaragoza-style
sample and on a synthetic sanity-check scene.

This script is intentionally conservative:
- no oracle tuning on test ground truth
- no claims against unfaithful baselines
- paper-matched scoring uses only metrics the paper explicitly reports
  numerically for the public Zaragoza efficiency comparison
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

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from data.generate_nlos_data import generate_dataset
from data.load_zaragoza import load_zaragoza_hdf5
from method.quasi_fresnel import (
    quasi_fresnel_reconstruct,
    quasi_fresnel_time_integral,
    quasi_fresnel_time_integral_loading,
)
from eval.metrics import compute_metrics


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
    integration_mode: str = "traditional",
    repeats: int = 5,
) -> dict[str, object]:
    runtimes: list[float] = []
    algorithm_peak_mb: list[float] = []
    albedo = None
    depth = None

    rss_before = _linux_maxrss_mb()
    for _ in range(repeats):
        tracemalloc.start()
        t0 = time.perf_counter()
        albedo, depth = quasi_fresnel_reconstruct(
            tau,
            s=s,
            dt=dt,
            k=k,
            area=area,
            integration_mode=integration_mode,
        )
        runtimes.append(time.perf_counter() - t0)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        algorithm_peak_mb.append(peak / (1024.0 * 1024.0))
    rss_after = _linux_maxrss_mb()

    return {
        "albedo": albedo,
        "depth": depth,
        "integration_mode": integration_mode,
        "runtime_mean_s": float(np.mean(runtimes)),
        "runtime_std_s": float(np.std(runtimes)),
        "runtime_min_s": float(np.min(runtimes)),
        "runtime_max_s": float(np.max(runtimes)),
        "maxrss_mb": max(rss_before, rss_after),
        "algorithm_peak_mb": float(np.max(algorithm_peak_mb)),
    }


def load_real_sample() -> dict[str, object]:
    npz_path = ROOT / "data" / "zaragoza" / "bunny_conf64.npz"
    hdf5_path = ROOT / "data" / "zaragoza" / "bunny_conf64.hdf5"
    npz_data = np.load(npz_path)
    hdf5_data = load_zaragoza_hdf5(hdf5_path)
    return {
        "tau": hdf5_data["tau"],
        "albedo": npz_data["albedo"],
        "depth": npz_data["depth"],
        "has_ground_truth": True,
        "dt": float(hdf5_data["dt"]),
        "k": int(npz_data["k"]),
        "area": float(hdf5_data["area"]),
        "scene_name": str(hdf5_data["scene_name"]),
    }


def _scene_parameter_s(scene_name: str) -> float:
    return 0.025 if "usaf" in scene_name.lower() else 0.02


def discover_additional_public_scenes() -> list[Path]:
    candidates = [
        ROOT / "data" / "zaragoza" / "public" / "T_conf64.hdf5",
    ]
    return [path for path in candidates if path.exists()]


def load_public_scene(path: Path) -> dict[str, object]:
    if path.suffix == ".npz":
        data = np.load(path)
        return {
            "tau": data["tau"],
            "albedo": data["albedo"],
            "depth": data["depth"],
            "has_ground_truth": True,
            "dt": float(data["dt"]),
            "k": int(data["k"]),
            "area": float(data["area"]),
            "scene_name": str(data["scene_name"]),
        }

    hdf5_data = load_zaragoza_hdf5(path)
    return {
        "tau": hdf5_data["tau"],
        "albedo": hdf5_data["albedo"],
        "depth": hdf5_data["depth"],
        "has_ground_truth": bool(
            hdf5_data.get("has_albedo_gt", False) and hdf5_data.get("has_depth_gt", False)
        ),
        "dt": float(hdf5_data["dt"]),
        "k": int(hdf5_data["k"]),
        "area": float(hdf5_data["area"]),
        "scene_name": str(hdf5_data["scene_name"]),
    }


def build_scores(
    real_result: dict[str, object], scaling: dict[str, dict[str, object]]
) -> dict[str, object]:
    return {
        "experiments": {
            "zaragoza_efficiency_real_sample": {
                "results": {
                    "quasi_fresnel_proposed": {
                        "runtime_s": round(real_result["runtime_mean_s"], 6),
                        "memory_mb": round(real_result["maxrss_mb"], 2),
                    }
                }
            },
            "complexity_scaling_cubic_measurements": {
                "results": {
                    "quasi_fresnel_traditional": {
                        "memory_order": round(scaling["traditional"]["memory_order"], 3),
                    },
                    "quasi_fresnel_loading": {
                        "memory_order": round(scaling["loading"]["memory_order"], 3),
                    },
                }
            }
        }
    }


def build_diagnostics(
    real_result: dict[str, object],
    real_metrics: dict[str, float],
    loading_result: dict[str, object],
    loading_consistency: dict[str, float],
    scaling: dict[str, dict[str, object]],
    public_scene_results: list[dict[str, object]],
    syn_result: dict[str, object],
    syn_metrics: dict[str, float],
) -> dict[str, object]:
    return {
        "real_sample": {
            "traditional": {
                "runtime_mean_s": round(real_result["runtime_mean_s"], 6),
                "runtime_std_s": round(real_result["runtime_std_s"], 6),
                "runtime_min_s": round(real_result["runtime_min_s"], 6),
                "runtime_max_s": round(real_result["runtime_max_s"], 6),
                "memory_mb": round(real_result["maxrss_mb"], 2),
                "algorithm_peak_mb": round(real_result["algorithm_peak_mb"], 2),
                "proxy_quality": {
                    "psnr": round(real_metrics["psnr"], 4),
                    "ssim": round(real_metrics["ssim"], 4),
                    "albedo_mae": round(real_metrics["albedo_mae"], 6),
                    "depth_mae": round(real_metrics["depth_mae"], 6),
                },
            },
            "loading": {
                "runtime_mean_s": round(loading_result["runtime_mean_s"], 6),
                "runtime_std_s": round(loading_result["runtime_std_s"], 6),
                "runtime_min_s": round(loading_result["runtime_min_s"], 6),
                "runtime_max_s": round(loading_result["runtime_max_s"], 6),
                "memory_mb": round(loading_result["maxrss_mb"], 2),
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
        "synthetic_sanity": {
            "runtime_mean_s": round(syn_result["runtime_mean_s"], 6),
            "runtime_std_s": round(syn_result["runtime_std_s"], 6),
            "memory_mb": round(syn_result["maxrss_mb"], 2),
            "algorithm_peak_mb": round(syn_result["algorithm_peak_mb"], 2),
            "quality": {
                "psnr": round(syn_metrics["psnr"], 4),
                "ssim": round(syn_metrics["ssim"], 4),
                "albedo_mae": round(syn_metrics["albedo_mae"], 6),
                "depth_mae": round(syn_metrics["depth_mae"], 6),
            },
        },
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
    ds = s * 0.01
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
                    quasi_fresnel_time_integral(tau, s, dt, k)
                    quasi_fresnel_time_integral(tau, s + ds, dt, k)
                else:
                    quasi_fresnel_time_integral_loading(tau, (s, s + ds), dt, k)
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
    print("=== Real Zaragoza-style Sample ===")
    real = load_real_sample()
    # Paper uses scene-specific fixed s values, not test-set tuning.
    # The bundled sample is a bunny scene; we use the paper's 0.02 setting
    # for non-USAF Zaragoza instances.
    real_s = _scene_parameter_s(real["scene_name"])
    real_result = benchmark_qft(
        real["tau"], s=real_s, dt=real["dt"], k=real["k"], area=real["area"], repeats=5
    )
    real_metrics = _scene_quality_metrics(
        real_result["albedo"], real_result["depth"], real["albedo"], real["depth"]
    )
    print(
        f"scene={real['scene_name']} s={real_s:.3f} "
        f"runtime={real_result['runtime_mean_s']:.6f}s +/- {real_result['runtime_std_s']:.6f}s "
        f"maxrss={real_result['maxrss_mb']:.2f}MB"
    )
    print(
        "proxy_quality "
        f"PSNR={real_metrics['psnr']:.2f}dB "
        f"SSIM={real_metrics['ssim']:.4f} "
        f"albedo_MAE={real_metrics['albedo_mae']:.4f} "
        f"depth_MAE={real_metrics['depth_mae']:.4f}"
    )

    print("\n=== Real Sample: Sequential Loading Variant ===")
    loading_result = benchmark_qft(
        real["tau"],
        s=real_s,
        dt=real["dt"],
        k=real["k"],
        area=real["area"],
        integration_mode="loading",
        repeats=5,
    )
    loading_consistency = compute_metrics(
        loading_result["albedo"],
        loading_result["depth"],
        real_result["albedo"],
        real_result["depth"],
    )
    print(
        f"scene={real['scene_name']} s={real_s:.3f} "
        f"mode=loading runtime={loading_result['runtime_mean_s']:.6f}s "
        f"+/- {loading_result['runtime_std_s']:.6f}s "
        f"maxrss={loading_result['maxrss_mb']:.2f}MB"
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
            repeats=3,
        )
        scene_diag = {
            "scene_name": public_scene["scene_name"],
            "source_path": str(scene_path),
            "s": round(public_s, 4),
            "runtime_mean_s": round(public_result["runtime_mean_s"], 6),
            "runtime_std_s": round(public_result["runtime_std_s"], 6),
            "memory_mb": round(public_result["maxrss_mb"], 2),
            "algorithm_peak_mb": round(public_result["algorithm_peak_mb"], 2),
            "has_ground_truth": bool(public_scene["has_ground_truth"]),
        }
        if public_scene["has_ground_truth"]:
            public_metrics = _scene_quality_metrics(
                public_result["albedo"],
                public_result["depth"],
                public_scene["albedo"],
                public_scene["depth"],
            )
            scene_diag["proxy_quality"] = {
                "psnr": round(public_metrics["psnr"], 4),
                "ssim": round(public_metrics["ssim"], 4),
                "albedo_mae": round(public_metrics["albedo_mae"], 6),
                "depth_mae": round(public_metrics["depth_mae"], 6),
            }
            print(
                f"scene={public_scene['scene_name']} s={public_s:.3f} "
                f"runtime={public_result['runtime_mean_s']:.6f}s "
                f"maxrss={public_result['maxrss_mb']:.2f}MB "
                f"PSNR={public_metrics['psnr']:.2f}dB "
                f"SSIM={public_metrics['ssim']:.4f}"
            )
        else:
            print(
                f"scene={public_scene['scene_name']} s={public_s:.3f} "
                f"runtime={public_result['runtime_mean_s']:.6f}s "
                f"maxrss={public_result['maxrss_mb']:.2f}MB "
                "quality=unavailable"
            )
        public_scene_results.append(scene_diag)

    scores = build_scores(real_result, scaling)
    out_path = ROOT / "scoring" / "scores.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scores, indent=2) + "\n")
    print(f"\nWrote {out_path}")
    diag_path = ROOT / "scoring" / "diagnostics.json"

    print("\n=== Synthetic Sanity Check ===")
    synthetic = generate_dataset(
        "kylin", 64, 256, area=0.3, dt=0.003, k=4, N_scene=64, default_depth=0.15
    )
    syn_s = 0.025
    syn_result = benchmark_qft(
        synthetic["tau"],
        s=syn_s,
        dt=synthetic["dt"],
        k=synthetic["k"],
        area=synthetic["area"],
        repeats=3,
    )
    syn_metrics = compute_metrics(
        syn_result["albedo"],
        syn_result["depth"],
        synthetic["albedo"],
        synthetic["depth"],
    )
    print(
        f"scene=kylin_synthetic s={syn_s:.3f} "
        f"runtime={syn_result['runtime_mean_s']:.6f}s "
        f"maxrss={syn_result['maxrss_mb']:.2f}MB "
        f"PSNR={syn_metrics['psnr']:.2f}dB "
        f"SSIM={syn_metrics['ssim']:.4f}"
    )

    diagnostics = build_diagnostics(
        real_result,
        real_metrics,
        loading_result,
        loading_consistency,
        scaling,
        public_scene_results,
        syn_result,
        syn_metrics,
    )
    diag_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(f"Wrote {diag_path}")


if __name__ == "__main__":
    main()
