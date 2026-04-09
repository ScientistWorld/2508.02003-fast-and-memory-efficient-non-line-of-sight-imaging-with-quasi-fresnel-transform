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
from pathlib import Path

import numpy as np

ROOT = Path("/home/user")
sys.path.insert(0, str(ROOT))

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from data.generate_nlos_data import generate_dataset
from method.quasi_fresnel import quasi_fresnel_reconstruct
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
    repeats: int = 5,
) -> dict[str, object]:
    runtimes: list[float] = []
    albedo = None
    depth = None

    rss_before = _linux_maxrss_mb()
    for _ in range(repeats):
        t0 = time.perf_counter()
        albedo, depth = quasi_fresnel_reconstruct(tau, s=s, dt=dt, k=k, area=area)
        runtimes.append(time.perf_counter() - t0)
    rss_after = _linux_maxrss_mb()

    return {
        "albedo": albedo,
        "depth": depth,
        "runtime_mean_s": float(np.mean(runtimes)),
        "runtime_std_s": float(np.std(runtimes)),
        "runtime_min_s": float(np.min(runtimes)),
        "runtime_max_s": float(np.max(runtimes)),
        "maxrss_mb": max(rss_before, rss_after),
    }


def load_real_sample() -> dict[str, object]:
    path = ROOT / "data" / "zaragoza" / "bunny_conf64.npz"
    data = np.load(path)
    return {
        "tau": data["tau"],
        "albedo": data["albedo"],
        "depth": data["depth"],
        "dt": float(data["dt"]),
        "k": int(data["k"]),
        "area": float(data["area"]),
        "scene_name": str(data["scene_name"]),
    }


def build_scores(real_result: dict[str, object]) -> dict[str, object]:
    return {
        "experiments": {
            "zaragoza_efficiency_real_sample": {
                "results": {
                    "quasi_fresnel_proposed": {
                        "runtime_s": round(real_result["runtime_mean_s"], 6),
                        "memory_mb": round(real_result["maxrss_mb"], 2),
                    }
                }
            }
        }
    }


def main() -> None:
    print("=== Real Zaragoza-style Sample ===")
    real = load_real_sample()
    # Paper uses scene-specific fixed s values, not test-set tuning.
    # The bundled sample is a bunny scene; we use the paper's 0.02 setting
    # for non-USAF Zaragoza instances.
    real_s = 0.02
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

    print("\n=== Synthetic Sanity Check ===")
    synthetic = generate_dataset(
        "kylin", 64, 256, area=0.3, dt=0.003, k=4, N_relay=64, default_depth=0.15
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

    scores = build_scores(real_result)
    out_path = ROOT / "scoring" / "scores.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scores, indent=2) + "\n")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
