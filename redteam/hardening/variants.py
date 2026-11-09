#!/usr/bin/env python3
"""Hardening-audit variants of the reference Quasi-Fresnel reconstruction.

    python3 redteam/hardening/variants.py --variant <name> --scene <dir> --output <file.npz>

Variants (all keep the paper's three steps unless stated):
  lean          same arithmetic, lower working memory: in-place real/imag
                accumulation, chunked separable FFT convolution, intermediates
                freed as soon as they are consumed.
  smooth        reference + albedo-weighted Gaussian smoothing (sigma = 1 px)
                of albedo and depth (the paper notes 2D image processing can be
                applied to the recovered maps).
  lean_smooth   lean + smooth.
  multi_s       average of reconstructions at 0.9 s, s, 1.1 s (s = reference value).
  no_deconv     weaker ablation: skips the spatial deconvolution (Eq. 5) and
                reads albedo/depth from phi directly.
These live outside method/ on purpose: they are audit evidence, not part of
the reference a future agent starts from.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "method"))

from quasi_fresnel import (  # noqa: E402
    extract_albedo_depth,
    quasi_fresnel_reconstruct_from_phi,
    quasi_fresnel_time_integral_stream,
)
from run_qf import DEFAULT_S, DS, finalize, iter_time_bins, read_meta, reconstruct  # noqa: E402


def _next_pow2(size: int) -> int:
    length = 1
    while length < size:
        length <<= 1
    return length


def lean_accumulate(path: Path, s_values, dr: float, k: int, n: int):
    s_values = np.asarray(s_values, dtype=np.float64)
    acc_re = np.zeros((s_values.size, n, n))
    acc_im = np.zeros((s_values.size, n, n))
    tau = np.empty((n, n))
    scratch = np.empty((n, n))
    for t, counts in enumerate(iter_time_bins(path)):
        np.copyto(tau, counts, casting="unsafe")
        r = (t + 0.5) * dr
        for m, s in enumerate(s_values):
            w = (r ** k) * np.exp(-1j * (r ** 2) / (4 * s ** 2)) * dr
            np.multiply(tau, w.real, out=scratch)
            acc_re[m] += scratch
            np.multiply(tau, w.imag, out=scratch)
            acc_im[m] += scratch
    return acc_re, acc_im


def lean_deconv(phi: np.ndarray, s: float, wall: np.ndarray, chunk: int = 32) -> np.ndarray:
    """Eq. (5) as two chunked 1D FFT convolutions; same result as the reference."""
    n = phi.shape[0]
    dx = float(np.mean(np.abs(np.diff(wall))))
    offsets = np.arange(-(n - 1), n, dtype=np.float64) * dx
    kernel = np.exp(1j * offsets ** 2 / (4.0 * s ** 2))
    length = _next_pow2(3 * n - 2)
    kfft = np.fft.fft(kernel, n=length)
    start = n - 1
    out = np.empty((n, n), dtype=np.complex128)
    for c0 in range(0, n, chunk):
        spec = np.fft.fft(phi[:, c0:c0 + chunk], n=length, axis=0)
        spec *= kfft[:, None]
        out[:, c0:c0 + chunk] = np.fft.ifft(spec, n=length, axis=0)[start:start + n]
    for r0 in range(0, n, chunk):
        spec = np.fft.fft(out[r0:r0 + chunk, :], n=length, axis=1)
        spec *= kfft[None, :]
        out[r0:r0 + chunk, :] = np.fft.ifft(spec, n=length, axis=1)[:, start:start + n]
    out *= dx * dx / (16.0 * np.pi ** 2 * s ** 4)
    return out


def lean_reconstruct(scene: Path, s: float = DEFAULT_S):
    meta = read_meta(scene)
    n = meta["n"]
    acc_re, acc_im = lean_accumulate(scene / "transient.npy", (s - DS, s, s + DS), meta["dr"], meta["k"], n)
    psis = []
    for m, sv in enumerate((s - DS, s, s + DS)):
        phi = acc_re[m] + 1j * acc_im[m]
        psis.append(lean_deconv(phi, sv, meta["wall"]))
        del phi
    del acc_re, acc_im
    albedo, depth = extract_albedo_depth(psis[1], s, psi_prev=psis[0], psi_next=psis[2], ds=DS)
    return finalize(albedo, depth, meta["depth_max"])


def _blur(img: np.ndarray, sigma: float = 1.0, radius: int = 3) -> np.ndarray:
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    taps = np.exp(-x ** 2 / (2 * sigma ** 2))
    taps /= taps.sum()
    out = img
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (radius, radius)
        padded = np.pad(out, pad, mode="edge")
        acc = np.zeros_like(out)
        for i, w in enumerate(taps):
            sl = [slice(None), slice(None)]
            sl[axis] = slice(i, i + out.shape[axis])
            acc += w * padded[tuple(sl)]
        out = acc
    return out


def smooth(albedo: np.ndarray, depth: np.ndarray, depth_max: float):
    a_s = _blur(albedo)
    weight = _blur(albedo)
    num = _blur(albedo * depth)
    d_s = np.where(weight > 1e-12 * max(weight.max(), 1e-300), num / np.maximum(weight, 1e-300), depth)
    return finalize(a_s, d_s, depth_max)


def multi_s(scene: Path, s_list=None):
    if s_list is None:
        s_list = (0.9 * DEFAULT_S, DEFAULT_S, 1.1 * DEFAULT_S)
    meta = read_meta(scene)
    s_values = []
    for s in s_list:
        s_values += [s - DS, s, s + DS]
    phis = quasi_fresnel_time_integral_stream(iter_time_bins(scene / "transient.npy"), s_values, meta["dr"], meta["k"])
    albedo_sum = None
    depth_num = None
    weight_sum = None
    for idx, s in enumerate(s_list):
        a, d = quasi_fresnel_reconstruct_from_phi(
            phis[3 * idx + 1], s, area=meta["size"], wall_x=meta["wall"], wall_y=meta["wall"],
            phi_prev=phis[3 * idx], phi_next=phis[3 * idx + 2], ds=DS)
        a, d = finalize(a, d, meta["depth_max"])
        a = a / max(a.mean(), 1e-300)
        albedo_sum = a if albedo_sum is None else albedo_sum + a
        depth_num = a * d if depth_num is None else depth_num + a * d
        weight_sum = a.copy() if weight_sum is None else weight_sum + a
    depth = np.where(weight_sum > 0, depth_num / np.maximum(weight_sum, 1e-300), 0.0)
    return finalize(albedo_sum / len(s_list), depth, meta["depth_max"])


def no_deconv(scene: Path, s: float = DEFAULT_S):
    meta = read_meta(scene)
    phi_prev, phi, phi_next = quasi_fresnel_time_integral_stream(
        iter_time_bins(scene / "transient.npy"), (s - DS, s, s + DS), meta["dr"], meta["k"])
    albedo, depth = extract_albedo_depth(phi, s, psi_prev=phi_prev, psi_next=phi_next, ds=DS)
    return finalize(albedo, depth, meta["depth_max"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True,
                        choices=("lean", "smooth", "lean_smooth", "multi_s", "no_deconv"))
    parser.add_argument("--scene", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scene = Path(args.scene)
    if args.variant == "lean":
        albedo, depth = lean_reconstruct(scene)
    elif args.variant == "smooth":
        albedo, depth = smooth(*reconstruct(scene), read_meta(scene)["depth_max"])
    elif args.variant == "lean_smooth":
        albedo, depth = smooth(*lean_reconstruct(scene), read_meta(scene)["depth_max"])
    elif args.variant == "multi_s":
        albedo, depth = multi_s(scene)
    else:
        albedo, depth = no_deconv(scene)
    np.savez(args.output, albedo=albedo, depth=depth)


if __name__ == "__main__":
    main()
