#!/usr/bin/env python3
"""Exhaustive volumetric backprojection (the brute force the paper avoids).

    python3 redteam/hardening/bruteforce.py --scene <dir> --output <file.npz>

Every candidate voxel (N x N lateral x M depth bins) is scored against every
wall measurement (O(N^4 M) work, O(N^2 M) volume memory), followed by a
Laplacian high-pass filter and a per-pixel maximum.  Adapted from the red-team
audit's brute force, which solved the old 64 x 64 test in 18 s; at the
benchmark's 256-512 scan sizes it is ~10^3-10^4 times more work.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from numba import njit, prange


@njit(parallel=True, cache=False)
def exhaustive(tau, wall, dr):  # pragma: no cover - audit only
    nx, ny, nt = tau.shape
    volume = np.zeros((nx, ny, nt), dtype=np.float32)
    for i in prange(nx):
        for j in range(ny):
            for z in range(nt):
                depth = (z + 0.5) * dr
                total = 0.0
                norm = 0.0
                for wi in range(nx):
                    dx = wall[i] - wall[wi]
                    for wj in range(ny):
                        dy = wall[j] - wall[wj]
                        distance = np.sqrt(dx * dx + dy * dy + depth * depth)
                        b = int(distance / dr)
                        if b >= nt:
                            continue
                        weight = 1.0 / (distance ** 4 + 1e-30)
                        total += weight * tau[wi, wj, b]
                        norm += weight * weight
                volume[i, j, z] = total / np.sqrt(norm + 1e-30)
    return volume


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scene = Path(args.scene)
    meta = json.loads((scene / "meta.json").read_text())
    n = int(meta["wall_points_per_axis"])
    wall = np.linspace(-0.5 * meta["wall_size_m"], 0.5 * meta["wall_size_m"], n)
    dr = float(meta["bin_width_m"])
    tau = np.ascontiguousarray(np.moveaxis(np.load(scene / "transient.npy"), 0, 2), dtype=np.float32)
    volume = exhaustive(tau, wall, dr)
    lap = -6.0 * volume
    for axis in range(3):
        lap += np.roll(volume, 1, axis) + np.roll(volume, -1, axis)
    filtered = np.maximum(-lap, 0.0)
    albedo = filtered.max(axis=2).astype(np.float64)
    depth = (np.argmax(filtered, axis=2) + 0.5) * dr
    np.savez(args.output, albedo=albedo, depth=depth)


if __name__ == "__main__":
    main()
