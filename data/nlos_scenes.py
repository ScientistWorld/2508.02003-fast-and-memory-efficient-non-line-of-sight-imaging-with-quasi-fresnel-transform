#!/usr/bin/env python3
"""Procedural confocal NLOS scenes for the visible (train) split.

A scene is a set of surface-like hidden objects described by an albedo map
and a depth map over the relay-wall plane.  Transients are rendered with a
confocal three-bounce model (Lambertian relay wall and Lambertian object,
inverse-square falloff on each leg, no occlusion between objects) and then
corrupted by Poisson photon noise plus a small uniform background.

Acquisition geometry (fixed for the benchmark):
  * relay wall: 1 m x 1 m, ``n x n`` confocal scan points on a uniform grid
    ``x_i = y_i = -0.5 + i / (n - 1)`` metres;
  * 512 time bins; bin ``t`` collects returns whose one-way wall-to-scene
    distance lies in ``[t, t + 1) * 1.5 mm`` (the photon path grows by 3 mm
    per bin);
  * measurements are integer photon counts stored as ``uint16`` with layout
    ``[time_bin, x_index, y_index]``.

Usage:
  python3 data/nlos_scenes.py --write-train      # materialise data/train_scenes/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRAIN_DIR = ROOT / "data" / "train_scenes"

WALL_SIZE_M = 1.0
TIME_BINS = 512
BIN_WIDTH_M = 0.0015
FALLOFF_EXPONENT = 4
SUPERSAMPLE = 2
PEAK_EXPECTED_COUNTS = 200.0
BACKGROUND_COUNTS_PER_BIN = 0.001
DEPTH_LIMITS_M = (0.2, 0.62)

# (scene_id, seed, wall points per axis). Public: these are the visible scenes.
TRAIN_SCENES = (
    ("train_384_a", 101, 384),
    ("train_256_a", 102, 256),
    ("train_256_b", 103, 256),
    ("train_256_c", 104, 256),
    ("train_256_d", 105, 256),
    ("train_256_e", 106, 256),
)

SHAPES = ("disk", "ellipse", "rectangle", "annulus", "triangle", "cross", "ell")


def wall_coordinates(n: int) -> np.ndarray:
    return np.linspace(-WALL_SIZE_M / 2.0, WALL_SIZE_M / 2.0, n)


def max_observable_depth_m() -> float:
    return TIME_BINS * BIN_WIDTH_M


def _fine_coordinates(n: int) -> tuple[np.ndarray, float]:
    wall = wall_coordinates(n)
    dx = wall[1] - wall[0]
    offsets = ((np.arange(SUPERSAMPLE) + 0.5) / SUPERSAMPLE - 0.5) * dx
    return (wall[:, None] + offsets[None, :]).ravel(), dx / SUPERSAMPLE


def _shape_mask(kind: str, u: np.ndarray, v: np.ndarray, size: float, aspect: float) -> np.ndarray:
    if kind == "disk":
        return u * u + v * v < size * size
    if kind == "ellipse":
        return (u / size) ** 2 + (v / (size * aspect)) ** 2 < 1.0
    if kind == "rectangle":
        return (np.abs(u) < size) & (np.abs(v) < size * aspect)
    if kind == "annulus":
        r2 = u * u + v * v
        return (r2 < size * size) & (r2 > (0.55 * size) ** 2)
    if kind == "triangle":
        root3 = np.sqrt(3.0)
        return (v > -0.5 * size) & (root3 * u + v < size) & (-root3 * u + v < size)
    if kind == "cross":
        w = 0.32 * size
        return ((np.abs(u) < size) & (np.abs(v) < w)) | ((np.abs(u) < w) & (np.abs(v) < size))
    if kind == "ell":
        w = 0.38 * size
        horizontal = (u > -size) & (u < size) & (v > -size) & (v < -size + 2.0 * w)
        vertical = (u > -size) & (u < -size + 2.0 * w) & (v > -size) & (v < size)
        return horizontal | vertical
    raise ValueError(f"unknown shape {kind!r}")


def sample_scene(seed: int, n: int) -> dict:
    """Sample a hidden scene on a ``SUPERSAMPLE``-times finer grid than the wall."""
    rng = np.random.default_rng(seed)
    fine, cell = _fine_coordinates(n)
    X, Y = np.meshgrid(fine, fine, indexing="ij")
    albedo = np.zeros(X.shape, dtype=np.float64)
    depth = np.zeros(X.shape, dtype=np.float64)
    grad_x = np.zeros(X.shape, dtype=np.float64)
    grad_y = np.zeros(X.shape, dtype=np.float64)

    target = int(rng.integers(1, 4))
    placed: list[tuple[float, float, float]] = []
    for _ in range(400):
        if len(placed) >= target:
            break
        # Draw every parameter before any rejection test so the random stream
        # does not depend on the grid resolution.
        kind = SHAPES[int(rng.integers(len(SHAPES)))]
        size = float(rng.uniform(0.07, 0.15))
        aspect = float(rng.uniform(0.45, 0.85))
        theta = float(rng.uniform(0.0, np.pi))
        radius = 1.45 * size
        limit = max(0.34 - radius, 0.0)
        cx, cy = (float(c) for c in rng.uniform(-1.0, 1.0, size=2) * limit)
        d0 = float(rng.uniform(0.28, 0.48))
        curved = bool(rng.random() < 0.4)
        if curved:
            slope = rng.uniform(-0.2, 0.2, size=2)
            curvature = float(rng.uniform(-1.5, 1.5))
        else:
            slope = rng.uniform(-0.45, 0.45, size=2)
            curvature = 0.0
        textured = bool(rng.random() < 0.35)
        a0 = float(rng.uniform(0.45, 1.0))
        period = float(rng.uniform(0.03, 0.06))
        phase = float(rng.uniform(0.0, 1.0))

        if any(np.hypot(cx - px, cy - py) < radius + pr + 0.02 for px, py, pr in placed):
            continue
        du = X - cx
        dv = Y - cy
        c, s = np.cos(theta), np.sin(theta)
        u = c * du + s * dv
        v = -s * du + c * dv
        mask = _shape_mask(kind, u, v, size, aspect)
        if mask.sum() * cell * cell < 0.003:
            continue
        dmap = d0 + slope[0] * du + slope[1] * dv + curvature * (du * du + dv * dv)
        gx = slope[0] + 2.0 * curvature * du
        gy = slope[1] + 2.0 * curvature * dv
        if textured:
            stripes = np.mod(u / period + phase, 1.0) < 0.5
            amap = a0 * np.where(stripes, 1.0, 0.45)
        else:
            amap = np.full(X.shape, a0)
        albedo[mask] = amap[mask]
        depth[mask] = np.clip(dmap[mask], *DEPTH_LIMITS_M)
        grad_x[mask] = gx[mask]
        grad_y[mask] = gy[mask]
        placed.append((cx, cy, radius))

    if not placed:  # pragma: no cover - practically unreachable
        mask = X * X + Y * Y < 0.1 ** 2
        albedo[mask] = 0.8
        depth[mask] = 0.35

    return {
        "n": n,
        "X": X,
        "Y": Y,
        "albedo": albedo,
        "depth": depth,
        "grad_x": grad_x,
        "grad_y": grad_y,
        "cell": cell,
        "objects": len(placed) if placed else 1,
    }


def ground_truth(scene: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Albedo, depth and fully-covered mask at wall resolution."""
    n = scene["n"]
    ss = SUPERSAMPLE
    a = scene["albedo"].reshape(n, ss, n, ss)
    covered = a > 0
    albedo_gt = a.mean(axis=(1, 3))
    count = covered.sum(axis=(1, 3))
    depth_sum = (scene["depth"].reshape(n, ss, n, ss) * covered).sum(axis=(1, 3))
    depth_gt = np.where(count > 0, depth_sum / np.maximum(count, 1), 0.0)
    mask = count == ss * ss
    return albedo_gt, depth_gt, mask


try:  # numba makes rendering fast; a slower numpy path is kept as fallback
    from numba import njit, prange

    @njit(parallel=True, cache=False)
    def _render_kernel(wall, px, py, pz, gx, gy, w, dr, nbins, hist):  # pragma: no cover
        n = wall.shape[0]
        npts = px.shape[0]
        rmax = dr * nbins
        rmax2 = rmax * rmax
        for idx in prange(n * n):
            i = idx // n
            j = idx - i * n
            wx = wall[i]
            wy = wall[j]
            for p in range(npts):
                vx = wx - px[p]
                vy = wy - py[p]
                z = pz[p]
                r2 = vx * vx + vy * vy + z * z
                if r2 >= rmax2:
                    continue
                ndot = gx[p] * vx + gy[p] * vy + z
                if ndot <= 0.0:
                    continue
                r = np.sqrt(r2)
                b = int(r / dr)
                if b >= nbins:
                    continue
                r4 = r2 * r2
                hist[i, j, b] += w[p] * z * z * ndot * ndot / (r4 * r4)

    HAVE_NUMBA = True
except ImportError:  # pragma: no cover
    HAVE_NUMBA = False


def _render_numpy(wall, px, py, pz, gx, gy, w, dr, nbins, hist):  # pragma: no cover
    n = wall.shape[0]
    rmax2 = (dr * nbins) ** 2
    for i in range(n):
        vx = wall[i] - px[None, :]
        vy = wall[:, None] - py[None, :]
        r2 = vx * vx + vy * vy + pz[None, :] ** 2
        ndot = gx[None, :] * vx + gy[None, :] * vy + pz[None, :]
        r = np.sqrt(r2)
        b = (r / dr).astype(np.int64)
        valid = (r2 < rmax2) & (ndot > 0) & (b < nbins)
        contrib = w[None, :] * pz[None, :] ** 2 * ndot ** 2 / (r2 ** 4)
        rows = np.broadcast_to(np.arange(n)[:, None], b.shape)
        flat = rows[valid] * nbins + b[valid]
        hist[i] += np.bincount(flat, weights=contrib[valid], minlength=n * nbins).reshape(n, nbins)


def expected_histogram(scene: dict) -> np.ndarray:
    """Noise-free expected intensity, shape ``(n, n, TIME_BINS)`` (float32)."""
    n = scene["n"]
    wall = wall_coordinates(n)
    pts = scene["albedo"] > 0
    px = np.ascontiguousarray(scene["X"][pts])
    py = np.ascontiguousarray(scene["Y"][pts])
    pz = np.ascontiguousarray(scene["depth"][pts])
    gx = np.ascontiguousarray(scene["grad_x"][pts])
    gy = np.ascontiguousarray(scene["grad_y"][pts])
    w = scene["albedo"][pts] * scene["cell"] ** 2 / np.sqrt(1.0 + gx * gx + gy * gy)
    w = np.ascontiguousarray(w)
    hist = np.zeros((n, n, TIME_BINS), dtype=np.float32)
    renderer = _render_kernel if HAVE_NUMBA else _render_numpy
    renderer(wall, px, py, pz, gx, gy, w, BIN_WIDTH_M, TIME_BINS, hist)
    return hist


def photon_counts(hist: np.ndarray, seed: int) -> np.ndarray:
    """Poisson photon counts with layout ``[time_bin, x, y]`` (uint16)."""
    n = hist.shape[0]
    scale = PEAK_EXPECTED_COUNTS / float(hist.max())
    rng = np.random.default_rng([int(seed), 2])
    counts = np.empty((TIME_BINS, n, n), dtype=np.uint16)
    for i in range(n):
        lam = hist[i].astype(np.float64) * scale + BACKGROUND_COUNTS_PER_BIN
        row = rng.poisson(lam)
        counts[:, i, :] = np.minimum(row, 65535).T
    return counts


def scene_metadata(n: int) -> dict:
    return {
        "wall_points_per_axis": int(n),
        "wall_size_m": WALL_SIZE_M,
        "wall_coordinates": "x_i = y_i = -wall_size_m/2 + i * wall_size_m / (n - 1), i = 0..n-1; the wall is the plane z = 0 and the hidden scene lies at z > 0",
        "time_bins": TIME_BINS,
        "bin_width_m": BIN_WIDTH_M,
        "distance_convention": "bin t collects returns whose one-way wall-to-scene distance lies in [t, t+1) * bin_width_m; the round-trip photon path grows by 2 * bin_width_m per bin",
        "falloff_exponent": FALLOFF_EXPONENT,
        "confocal": True,
        "transient_file": "transient.npy",
        "transient_layout": "[time_bin, x_index, y_index]",
        "transient_dtype": "uint16 photon counts (shot noise and a small background are present)",
        "max_observable_depth_m": max_observable_depth_m(),
    }


def write_scene_inputs(directory: Path, seed: int, n: int, scene: dict | None = None) -> dict:
    """Write ``transient.npy`` and ``meta.json`` for one scene; returns the scene."""
    directory.mkdir(parents=True, exist_ok=True)
    if scene is None:
        scene = sample_scene(seed, n)
    hist = expected_histogram(scene)
    counts = photon_counts(hist, seed)
    del hist
    np.save(directory / "transient.npy", counts)
    (directory / "meta.json").write_text(json.dumps(scene_metadata(n), indent=2) + "\n")
    return scene


def ensure_train_scenes(force: bool = False) -> list[tuple[str, int, int]]:
    """Materialise the visible train scenes (deterministic) under data/train_scenes/."""
    for scene_id, seed, n in TRAIN_SCENES:
        directory = TRAIN_DIR / scene_id
        if not force and (directory / "transient.npy").is_file() and (directory / "meta.json").is_file():
            continue
        print(f"rendering train scene {scene_id} (seed={seed}, n={n})", flush=True)
        scene = write_scene_inputs(directory, seed, n)
        albedo_gt, depth_gt, mask = ground_truth(scene)
        np.savez_compressed(directory / "ground_truth.npz", albedo=albedo_gt, depth=depth_gt, mask=mask)
    return list(TRAIN_SCENES)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-train", action="store_true", help="render the visible train scenes")
    parser.add_argument("--force", action="store_true", help="re-render even if files exist")
    args = parser.parse_args()
    if args.write_train:
        ensure_train_scenes(force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
