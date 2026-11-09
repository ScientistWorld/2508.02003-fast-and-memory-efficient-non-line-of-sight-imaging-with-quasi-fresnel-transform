#!/usr/bin/env python3
"""Simple streaming baseline: albedo = photon energy per wall point, depth = peak time bin.

    python3 baseline/peak_energy.py --scene <scene_dir> --output <prediction.npz>

Reads the histogram one time bin at a time (O(N^2) memory).  It performs no
spatial inversion, so the albedo is the strongly blurred energy image and the
depth is the distance to the brightest return seen from each wall point.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def iter_time_bins(path: Path):
    with open(path, "rb") as handle:
        version = np.lib.format.read_magic(handle)
        reader = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
        shape, fortran, dtype = reader(handle)
        n_bins, nx, ny = shape
        buf = np.empty(nx * ny, dtype=dtype)
        view = memoryview(buf).cast("B")
        for _ in range(n_bins):
            if handle.readinto(view) != view.nbytes:
                raise ValueError("truncated histogram file")
            yield buf.reshape(nx, ny)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scene = Path(args.scene)
    meta = json.loads((scene / "meta.json").read_text())
    dr = float(meta["bin_width_m"])
    energy = None
    best = None
    arg = None
    for t, tau in enumerate(iter_time_bins(scene / "transient.npy")):
        tau = tau.astype(np.float64)
        if energy is None:
            energy = np.zeros_like(tau)
            best = np.full_like(tau, -1.0)
            arg = np.zeros(tau.shape, dtype=np.int64)
        energy += tau
        better = tau > best
        best[better] = tau[better]
        arg[better] = t
    depth = (arg + 0.5) * dr
    np.savez(args.output, albedo=energy, depth=depth)


if __name__ == "__main__":
    main()
