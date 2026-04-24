#!/bin/bash
set -euo pipefail

cd /home/user

export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Run the reproduced Quasi-Fresnel method on the real Zaragoza bunny confocal
# scene (bunny_conf64.hdf5) and emit the raw report + diagnostics consumed by
# the train/test scorers.  Ground-truth albedo/depth maps in the HDF5 are at
# higher resolution than the relay-wall grid; we downsample them to match the
# method's 64x64 output before computing quality metrics.
python3 - <<'PY'
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

from eval.metrics import compute_metrics
from method.quasi_fresnel import (
    quasi_fresnel_reconstruct,
    quasi_fresnel_time_integral,
    quasi_fresnel_time_integral_loading,
)

# Load Zaragoza HDF5 using the dedicated loader which extracts wall coordinates,
# deltaT, area, and ground-truth maps with proper physical scaling.
from data.load_zaragoza import load_zaragoza_hdf5


def maxrss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def downsample_2d(arr, target_size):
    """Block-average *arr* down to (target_size, target_size)."""
    arr = np.asarray(arr, dtype=np.float64)
    h, w = arr.shape
    bh = h // target_size
    bw = w // target_size
    if bh < 1 or bw < 1:
        return arr
    cropped = arr[: bh * target_size, : bw * target_size]
    return cropped.reshape(target_size, bh, target_size, bw).mean(axis=(1, 3))


def benchmark_reconstruct(tau, s, dt, k, area, wall_x, wall_y, integration_mode, repeats=2):
    runtimes = []
    peak_mb = []
    albedo = None
    depth = None
    for _ in range(repeats):
        before = maxrss_mb()
        tracemalloc.start()
        start = time.perf_counter()
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
        runtimes.append(time.perf_counter() - start)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb.append(max(peak / (1024.0 * 1024.0), maxrss_mb() - before))
    return {
        "albedo": albedo,
        "depth": depth,
        "runtime_mean_s": float(np.mean(runtimes)),
        "runtime_std_s": float(np.std(runtimes)),
        "runtime_min_s": float(np.min(runtimes)),
        "runtime_max_s": float(np.max(runtimes)),
        "maxrss_mb": float(maxrss_mb()),
        "algorithm_peak_mb": float(np.max(peak_mb)),
    }


def scaling_summary(sizes=(16, 32, 48, 64), s=0.02, dt=0.003, k=4):
    rng = np.random.default_rng(250802003)
    per_mode = {
        "traditional": {"runtime_s": [], "memory_mb": []},
        "loading": {"runtime_s": [], "memory_mb": []},
    }
    ds = 1e-7
    for n in sizes:
        tau = rng.random((n, n, n), dtype=np.float64)
        for mode in ("traditional", "loading"):
            tracemalloc.start()
            start = time.perf_counter()
            if mode == "traditional":
                quasi_fresnel_time_integral(tau, s - ds, dt, k)
                quasi_fresnel_time_integral(tau, s, dt, k)
                quasi_fresnel_time_integral(tau, s + ds, dt, k)
            else:
                quasi_fresnel_time_integral_loading(tau, (s - ds, s, s + ds), dt, k)
            per_mode[mode]["runtime_s"].append(time.perf_counter() - start)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            per_mode[mode]["memory_mb"].append(peak / (1024.0 * 1024.0))

    out = {}
    x = np.log(np.asarray(sizes, dtype=np.float64))
    for mode, metrics in per_mode.items():
        out[mode] = {
            "sizes": list(sizes),
            "runtime_s": [round(float(v), 6) for v in metrics["runtime_s"]],
            "memory_mb": [round(float(v), 4) for v in metrics["memory_mb"]],
            "runtime_order": float(np.polyfit(x, np.log(metrics["runtime_s"]), 1)[0]),
            "memory_order": float(np.polyfit(x, np.log(metrics["memory_mb"]), 1)[0]),
        }
    return out


# ── Load real Zaragoza bunny data ─────────────────────────────────────
hdf5_path = ROOT / "data" / "zaragoza" / "bunny_conf64.hdf5"
print(f"Loading Zaragoza bunny: {hdf5_path}")
scene = load_zaragoza_hdf5(str(hdf5_path))

tau = scene["tau"]
dt = scene["dt"]
k = scene["k"]
area = scene["area"]
wall_x = scene.get("wall_x")
wall_y = scene.get("wall_y")
N = tau.shape[0]

print(f"  tau_shape={tau.shape} dt={dt} k={k} area={area}")
print(f"  wall_coords: {'yes' if wall_x is not None else 'no'}")
print(f"  GT: albedo={scene['has_albedo_gt']} depth={scene['has_depth_gt']} depth_metric_scale={scene['depth_metric_scale']}")

# Downsample GT to method output resolution
albedo_gt_full = scene["albedo"]
depth_gt_full = scene["depth"]
albedo_gt = downsample_2d(albedo_gt_full, N)
depth_gt = downsample_2d(depth_gt_full, N)
print(f"  GT downsampled: {albedo_gt.shape} from {albedo_gt_full.shape}")

# Paper-style s selection (matching typical confocal geometry)
s = 0.02

print(f"\n=== Zaragoza Bunny Confocal Benchmark ===")
print(f"s={s} N={N}")

traditional = benchmark_reconstruct(
    tau, s=s, dt=dt, k=k, area=area,
    wall_x=wall_x, wall_y=wall_y,
    integration_mode="traditional",
)
quality = compute_metrics(traditional["albedo"], traditional["depth"], albedo_gt, depth_gt)
print(
    "traditional "
    f"runtime={traditional['runtime_mean_s']:.6f}s "
    f"peak_memory={traditional['algorithm_peak_mb']:.2f}MB "
    f"PSNR={quality['psnr']:.4f} "
    f"SSIM={quality['ssim']:.4f} "
    f"depth_MAE={quality['depth_mae'] * 100.0:.4f}cm"
)

loading = benchmark_reconstruct(
    tau, s=s, dt=dt, k=k, area=area,
    wall_x=wall_x, wall_y=wall_y,
    integration_mode="loading",
)
loading_consistency = compute_metrics(
    loading["albedo"],
    loading["depth"],
    traditional["albedo"],
    traditional["depth"],
)
print(
    "loading "
    f"runtime={loading['runtime_mean_s']:.6f}s "
    f"peak_memory={loading['algorithm_peak_mb']:.2f}MB "
    f"depth_consistency={loading_consistency['depth_mae'] * 100.0:.6f}cm"
)

scaling = scaling_summary()
print(
    "scaling "
    f"traditional_runtime_order={scaling['traditional']['runtime_order']:.4f} "
    f"loading_memory_order={scaling['loading']['memory_order']:.4f}"
)

raw_scores = {
    "experiments": {
        "zaragoza_bunny_depth_error": {
            "results": {
                "quasi_fresnel_proposed": {
                    "depth_mae_cm": round(float(quality["depth_mae"] * 100.0), 4)
                }
            }
        },
        "zaragoza_efficiency_public_bunny": {
            "results": {
                "quasi_fresnel_proposed": {
                    "runtime_s": round(float(traditional["runtime_mean_s"]), 6),
                    "memory_mb": round(float(traditional["algorithm_peak_mb"]), 2),
                }
            }
        },
    }
}

diagnostics = {
    "primary_public_scene": {
        "scene_name": "zaragoza_bunny_conf64",
        "source_path": str(hdf5_path),
        "dt": round(float(dt), 8),
        "area_m": round(float(area), 6),
        "traditional": {
            "runtime_mean_s": round(float(traditional["runtime_mean_s"]), 6),
            "runtime_std_s": round(float(traditional["runtime_std_s"]), 6),
            "runtime_min_s": round(float(traditional["runtime_min_s"]), 6),
            "runtime_max_s": round(float(traditional["runtime_max_s"]), 6),
            "maxrss_mb": round(float(traditional["maxrss_mb"]), 2),
            "algorithm_peak_mb": round(float(traditional["algorithm_peak_mb"]), 2),
            "quality": {
                "psnr": round(float(quality["psnr"]), 4),
                "ssim": round(float(quality["ssim"]), 4),
                "albedo_mae": round(float(quality["albedo_mae"]), 6),
                "depth_mae_m": round(float(quality["depth_mae"]), 6),
                "depth_mae_cm": round(float(quality["depth_mae"] * 100.0), 4),
            },
        },
        "loading": {
            "runtime_mean_s": round(float(loading["runtime_mean_s"]), 6),
            "runtime_std_s": round(float(loading["runtime_std_s"]), 6),
            "runtime_min_s": round(float(loading["runtime_min_s"]), 6),
            "runtime_max_s": round(float(loading["runtime_max_s"]), 6),
            "maxrss_mb": round(float(loading["maxrss_mb"]), 2),
            "algorithm_peak_mb": round(float(loading["algorithm_peak_mb"]), 2),
            "consistency_vs_traditional": {
                "psnr": round(float(loading_consistency["psnr"]), 4),
                "ssim": round(float(loading_consistency["ssim"]), 6),
                "albedo_mae": round(float(loading_consistency["albedo_mae"]), 8),
                "depth_mae": round(float(loading_consistency["depth_mae"]), 8),
            },
        },
    },
    "complexity_scaling": scaling,
    "additional_public_scenes": [],
}

(ROOT / "scoring").mkdir(parents=True, exist_ok=True)
(ROOT / "scoring" / "raw_results.json").write_text(json.dumps(raw_scores, indent=2) + "\n")
(ROOT / "scoring" / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
print("Wrote /home/user/scoring/raw_results.json")
print("Wrote /home/user/scoring/diagnostics.json")
PY
# Score the generated method report through both benchmark slices in the same job.
bash scripts/evaluate_train.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_train.json
bash scripts/evaluate_test.sh /home/user/scoring/raw_results.json /home/user/scoring/scores_test.json
python3 validate.py --reference-only
