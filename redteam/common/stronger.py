"""Exact QFT sums without materializing a weighted 3-D histogram.

No new observations, labels, hyperparameter fitting, or numerical approximation.
The same complex weights are contracted directly into 2-D accumulators.
"""
import numpy as np


def quasi_fresnel_time_integral(tau, s, dt, k=4):
    r = (np.arange(tau.shape[2], dtype=np.float64) + 0.5) * dt
    weights = r**k * np.exp(-1j * r**2 / (4 * s**2)) * dt
    return np.einsum('ijt,t->ij', tau, weights, optimize=False)


def quasi_fresnel_time_integral_loading(tau, s_values, dt, k=4):
    s_arr = np.atleast_1d(np.asarray(s_values, dtype=np.float64))
    if s_arr.ndim != 1 or not s_arr.size:
        raise ValueError('s_values must be a non-empty 1-D sequence')
    # Keep sequential acquisition: read each bin once, reuse one scratch plane.
    r = (np.arange(tau.shape[2], dtype=np.float64) + 0.5) * dt
    acc = [np.zeros(tau.shape[:2], dtype=np.complex128) for _ in s_arr]
    scratch = np.empty(tau.shape[:2], dtype=np.float64)
    for b, radius in enumerate(r):
        for out, s in zip(acc, s_arr):
            weight = radius**k * np.exp(-1j * radius**2 / (4*s**2)) * dt
            np.multiply(tau[:, :, b], weight.real, out=scratch)
            np.add(out.real, scratch, out=out.real)
            np.multiply(tau[:, :, b], weight.imag, out=scratch)
            np.add(out.imag, scratch, out=out.imag)
    return acc[0] if len(acc) == 1 else tuple(acc)
