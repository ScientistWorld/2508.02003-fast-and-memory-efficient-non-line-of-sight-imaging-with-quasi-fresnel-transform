#!/usr/bin/env python3
"""Volumetric light-cone-transform (LCT) baseline (O'Toole et al., Nature 2018).

    python3 baseline/lct.py --scene <scene_dir> --output <prediction.npz>

Steps (confocal, diffuse falloff k):
  1. radiometric correction  tau(x, r) * r^k;
  2. mass-conserving resampling of the time axis from r to v = r^2;
  3. 3D Wiener deconvolution with the shift-invariant light-cone kernel
     h(x, v) = delta(v - |x|^2) on a zero-padded (2N, 2N, 2M) grid;
  4. resampling back to depth z (density factor 2z), albedo = max over z,
     depth = argmax over z.

This is the volumetric reconstruction class the paper compares against: its
working memory grows as O(N^2 M) (several GB for 256 x 256 x 512 scans), so it
exceeds the benchmark's memory budget by design.  It is provided as a
reference point for quality and memory, not as a competitive entry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import fft as sfft

SNR = 0.8  # O'Toole et al.'s default Wiener regulariser is 1/snr


def lct_reconstruct(tau: np.ndarray, wall: np.ndarray, dr: float, k: int = 4, snr: float = SNR):
    """tau: (N, N, M) float32 histogram (x, y, time)."""
    n = tau.shape[0]
    m = tau.shape[2]
    dx = float(wall[1] - wall[0])
    r_centers = (np.arange(m, dtype=np.float64) + 0.5) * dr
    corrected = tau * (r_centers ** k).astype(np.float32)

    # r -> v = r^2, conserving counts (cumulative sum interpolated at sqrt(v)).
    r_max = m * dr
    dv = r_max ** 2 / m
    cumulative = np.zeros((n, n, m + 1), dtype=np.float32)
    np.cumsum(corrected, axis=2, out=cumulative[:, :, 1:])
    del corrected
    edges = np.sqrt(np.arange(m + 1, dtype=np.float64) * dv) / dr  # fractional r-edge index
    lo = np.clip(np.floor(edges).astype(np.int64), 0, m)
    hi = np.clip(lo + 1, 0, m)
    frac = (edges - lo).astype(np.float32)
    c_v = cumulative[:, :, lo] * (1.0 - frac) + cumulative[:, :, hi] * frac
    del cumulative
    padded = np.zeros((2 * n, 2 * n, 2 * m), dtype=np.float32)
    padded[:n, :n, :m] = np.diff(c_v, axis=2)
    del c_v

    # Light-cone kernel on the padded grid (circular layout: lateral zero
    # offset at index 0, negative offsets wrap to the end).
    q = np.arange(2 * n)
    offsets = np.where(q < n, q, q - 2 * n) * dx
    lateral2 = offsets[:, None] ** 2 + offsets[None, :] ** 2
    v_index = np.floor(lateral2 / dv).astype(np.int64)
    psf = np.zeros((2 * n, 2 * n, 2 * m), dtype=np.float32)
    ii, jj = np.nonzero(v_index < 2 * m)
    psf[ii, jj, v_index[ii, jj]] = 1.0
    psf /= np.float32(np.sqrt(ii.size))  # unit L2 norm (entries are 0/1)

    fpsf = sfft.rfftn(psf, workers=1)
    del psf
    fdata = sfft.rfftn(padded, workers=1)
    del padded
    fdata *= np.conj(fpsf)
    fpsf = np.abs(fpsf) ** 2
    fpsf += np.float32(1.0 / snr)
    fdata /= fpsf
    del fpsf
    g = sfft.irfftn(fdata, s=(2 * n, 2 * n, 2 * m), workers=1)[:n, :n, :m]
    del fdata

    # u = z^2 -> z, density factor 2z.
    pos = r_centers ** 2 / dv - 0.5
    lo = np.clip(np.floor(pos).astype(np.int64), 0, m - 1)
    hi = np.clip(lo + 1, 0, m - 1)
    frac = np.clip(pos - lo, 0.0, 1.0).astype(np.float32)
    volume = g[:, :, lo] * (1.0 - frac) + g[:, :, hi] * frac
    del g
    volume *= (2.0 * r_centers).astype(np.float32)
    np.maximum(volume, 0.0, out=volume)
    albedo = volume.max(axis=2).astype(np.float64)
    depth = (np.argmax(volume, axis=2) + 0.5) * dr
    return albedo, depth


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--snr", type=float, default=SNR)
    args = parser.parse_args()
    scene = Path(args.scene)
    meta = json.loads((scene / "meta.json").read_text())
    n = int(meta["wall_points_per_axis"])
    size = float(meta["wall_size_m"])
    wall = np.linspace(-size / 2.0, size / 2.0, n)
    counts = np.load(scene / "transient.npy")
    tau = np.ascontiguousarray(np.moveaxis(counts, 0, 2), dtype=np.float32)
    del counts
    albedo, depth = lct_reconstruct(tau, wall, float(meta["bin_width_m"]), int(meta["falloff_exponent"]), args.snr)
    np.savez(args.output, albedo=albedo, depth=depth)


if __name__ == "__main__":
    main()
