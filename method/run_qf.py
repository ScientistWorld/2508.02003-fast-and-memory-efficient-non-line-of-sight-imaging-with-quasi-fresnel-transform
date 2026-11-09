#!/usr/bin/env python3
"""Quasi-Fresnel reconstruction of one scene (benchmark command-line contract).

    python3 method/run_qf.py --scene <dir with transient.npy + meta.json> --output <prediction.npz>

Default mode follows the paper's "Loading" variant: the histogram is read from
disk one time bin at a time and folded into the 2D aggregated measurements
phi(x; s - ds), phi(x; s), phi(x; s + ds) (Eq. 3); psi is recovered from each
phi by the separable FFT deconvolution of Eq. (5); albedo = |psi| and depth =
(-2 i s^3 psi^-1 dpsi/ds)^(1/2) (Eq. 4, Alg. 1).  ``--mode traditional`` loads
the full histogram first (the paper's "Traditional" variant, O(N^3) memory).

s = 0.02 m is the paper's setting for 256 x 256 scans of a 1 m x 1 m wall with
3 mm of photon path per time bin (Zaragoza experiments).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from quasi_fresnel import (  # noqa: E402
    quasi_fresnel_reconstruct_from_phi,
    quasi_fresnel_time_integral,
    quasi_fresnel_time_integral_stream,
)

DEFAULT_S = 0.02
DS = 1e-7


def read_meta(scene_dir: Path) -> dict:
    meta = json.loads((scene_dir / "meta.json").read_text())
    n = int(meta["wall_points_per_axis"])
    size = float(meta["wall_size_m"])
    return {
        "n": n,
        "bins": int(meta["time_bins"]),
        "dr": float(meta["bin_width_m"]),
        "k": int(meta["falloff_exponent"]),
        "wall": np.linspace(-size / 2.0, size / 2.0, n),
        "size": size,
        "depth_max": float(meta.get("max_observable_depth_m", int(meta["time_bins"]) * float(meta["bin_width_m"]))),
    }


def iter_time_bins(path: Path):
    """Yield the histogram one time bin (an N x N slice) at a time from a .npy file."""
    with open(path, "rb") as handle:
        version = np.lib.format.read_magic(handle)
        if version == (1, 0):
            shape, fortran, dtype = np.lib.format.read_array_header_1_0(handle)
        else:
            shape, fortran, dtype = np.lib.format.read_array_header_2_0(handle)
        if fortran or len(shape) != 3:
            raise ValueError(f"expected a C-ordered [time, x, y] array, got shape={shape} fortran={fortran}")
        n_bins, nx, ny = shape
        buf = np.empty(nx * ny, dtype=dtype)
        view = memoryview(buf).cast("B")
        for _ in range(n_bins):
            if handle.readinto(view) != view.nbytes:
                raise ValueError("truncated histogram file")
            yield buf.reshape(nx, ny)


def finalize(albedo: np.ndarray, depth: np.ndarray, depth_max: float) -> tuple[np.ndarray, np.ndarray]:
    """Output contract: finite, non-negative albedo; depth inside the observable range."""
    albedo = np.nan_to_num(albedo, nan=0.0, posinf=0.0, neginf=0.0)
    depth = np.nan_to_num(depth, nan=0.0, posinf=depth_max, neginf=0.0)
    return np.maximum(albedo, 0.0), np.clip(depth, 0.0, depth_max)


def reconstruct(scene_dir: Path, s: float = DEFAULT_S, mode: str = "loading") -> tuple[np.ndarray, np.ndarray]:
    meta = read_meta(scene_dir)
    s_values = (s - DS, s, s + DS)
    if mode == "loading":
        phi_prev, phi, phi_next = quasi_fresnel_time_integral_stream(
            iter_time_bins(scene_dir / "transient.npy"), s_values, meta["dr"], meta["k"]
        )
    elif mode == "traditional":
        tau = np.load(scene_dir / "transient.npy").astype(np.float64)
        tau = np.moveaxis(tau, 0, 2)  # (x, y, time)
        phi_prev, phi, phi_next = (
            quasi_fresnel_time_integral(tau, sv, meta["dr"], meta["k"]) for sv in s_values
        )
        del tau
    else:
        raise ValueError(f"unknown mode {mode!r}")
    albedo, depth = quasi_fresnel_reconstruct_from_phi(
        phi, s, area=meta["size"], wall_x=meta["wall"], wall_y=meta["wall"],
        phi_prev=phi_prev, phi_next=phi_next, ds=DS,
    )
    return finalize(albedo, depth, meta["depth_max"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--s", type=float, default=DEFAULT_S)
    parser.add_argument("--mode", choices=("loading", "traditional"), default="loading")
    args = parser.parse_args()
    albedo, depth = reconstruct(Path(args.scene), s=args.s, mode=args.mode)
    np.savez(args.output, albedo=albedo, depth=depth)


if __name__ == "__main__":
    main()
