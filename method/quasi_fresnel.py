"""
Quasi-Fresnel Transform for NLOS imaging.

Implements the paper's algorithm:
  Wei et al., "Fast and Memory-efficient Non-line-of-sight Imaging
  with Quasi-Fresnel Transform", 2025.

The algorithm has three steps:
  1. Time integration: phi(x; s) = integral e^{-i*r^2/4s^2} * r^k * tau(x,r) dr
  2. Spatial deconvolution: psi(x; s) = (1/16pi^2s^4) * integral e^{i*|x~-x|^2/4s^2} * phi(x~;s) dx~
  3. Albedo/depth extraction: a(x)=|psi|, d(x)=sqrt(-2i*s^3 * psi^{-1} * dpsi/ds)

Key insight: The algorithm works with spatial distance r = c*t/2 in meters.
The parameter dt is the spatial distance per time bin (e.g., 0.003 m per bin).
"""

import numpy as np
from numpy.fft import fft2, ifft2, fftshift


SPEED_OF_LIGHT = 299792458  # m/s


def quasi_fresnel_time_integral(tau, s, dt, k=4):
    """
    Step 1: Compute phi(x; s) by integrating tau(x, t) over time.

    Uses the reparameterization r = c*t/2 (spatial distance in meters).
    In terms of r: phi(x; s) = integral_0^inf e^(-i*r^2/4s^2) * r^k * tau(x, r) dr

    Parameters:
      tau: array of shape (N, N, N_bins) — time-resolved measurement
      s: float — Quasi-Fresnel parameter (meters)
      dt: float — spatial distance per time bin (meters/bin)
      k: int — scattering parameter (4=isotropic, 2=retroreflective)

    Returns:
      phi: complex array of shape (N, N)
    """
    N_bins = tau.shape[2]

    # r values at bin centers
    r_centers = (np.arange(N_bins, dtype=np.float64) + 0.5) * dt

    # Integration weights: r^k * exp(-i * r^2 / 4s^2) * dr
    phase = -1j * (r_centers ** 2) / (4 * s ** 2)
    weights = (r_centers ** k) * np.exp(phase) * dt

    # Sum over time dimension: phi(x) = sum_t weights(t) * tau(x, t)
    phi = np.sum(weights[np.newaxis, np.newaxis, :] * tau, axis=2)

    return phi.astype(np.complex128)


def quasi_fresnel_spatial_deconv(phi, s, area):
    """
    Step 2: Recover psi(x; s) from phi(x; s) via 2D convolution.

    Implements Eq. (5):
      psi(x; s) = (1/16*pi^2*s^4) * integral e^{i*|x~-x|^2/4s^2} * phi(x~;s) dx~

    This is a 2D convolution with kernel h(x) = e^{i*|x|^2/4s^2}.
    Implemented via FFT.

    Parameters:
      phi: complex array of shape (N, N)
      s: float — Quasi-Fresnel parameter (meters)
      area: float — physical area of the relay wall in meters

    Returns:
      psi: complex array of shape (N, N)
    """
    N = phi.shape[0]
    dx = area / N  # pixel spacing in meters

    # Build centered quadratic phase kernel in physical coordinates
    # h(x_pix) = exp(i * (x_pix * dx)^2 / 4s^2) = exp(i * x_pix^2 * dx^2 / 4s^2)
    x = np.arange(N, dtype=np.float64) - N // 2
    X, Y = np.meshgrid(x, x, indexing='ij')
    r_sq_pix = X ** 2 + Y ** 2

    # Kernel phase with physical coordinate scaling
    kernel = np.exp(1j * r_sq_pix * dx ** 2 / (4.0 * s ** 2))

    # FFT-based convolution
    phi_ft = fft2(phi.astype(np.complex128))
    kernel_ft = fft2(kernel.astype(np.complex128))
    psi = ifft2(phi_ft * kernel_ft)
    psi = fftshift(psi)

    # Apply normalization from Eq. (5): 1/(16*pi^2*s^4) * dx^2
    # The dx^2 accounts for the discrete integration (Riemann sum approximation)
    norm = dx ** 2 / (16.0 * np.pi ** 2 * s ** 4)
    psi *= norm

    return psi


def extract_albedo_depth(psi, s, psi2=None, ds=None):
    """
    Step 3: Extract albedo and depth from psi(x; s).

    From Eq. (4): psi(x; s) = a(x) * exp(-i * d(x)^2 / 4s^2)

    Albedo: a(x) = |psi(x; s)|
    Depth: d(x) = sqrt(-2i * s^3 * psi^{-1} * dpsi/ds)

    When psi2 is provided (psi computed at s+ds), depth is extracted via
    finite differences. Otherwise, depth is estimated from phase only.

    Parameters:
      psi: complex array of shape (N, N) — reconstruction at parameter s
      s: float — Quasi-Fresnel parameter
      psi2: complex array of shape (N, N) — reconstruction at s+ds (optional)
      ds: float — step size for numerical differentiation

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N) in meters
    """
    albedo = np.abs(psi)

    if psi2 is not None and ds is not None and ds > 0:
        # Depth via finite differences: d(x) = sqrt(-2i*s^3 * (psi2-psi)/(ds*psi))
        eps = 1e-10
        psi_safe = psi + eps * np.exp(1j * np.angle(psi))  # avoid division by zero
        dpsi_ds = (psi2 - psi) / ds
        depth_sq = -2j * s ** 3 * dpsi_ds / psi_safe

        # depth_sq should be approximately real and positive
        # Take real part for robustness
        depth_sq_real = np.real(depth_sq)
        depth_sq_real = np.maximum(depth_sq_real, 0)
        depth = np.sqrt(depth_sq_real)
    else:
        # Depth from phase only: phase = -d^2/4s^2 => d = 2s*sqrt(-phase)
        phase = np.angle(psi)
        neg_phase = np.maximum(-phase, 0)
        depth = 2.0 * s * np.sqrt(neg_phase)

    return albedo, depth


def quasi_fresnel_reconstruct(tau, s, dt, k=4, area=None, use_fdh=False):
    """
    Full Quasi-Fresnel Transform reconstruction pipeline.

    Parameters:
      tau: array of shape (N, N, N_bins)
      s: float — Quasi-Fresnel parameter (meters)
      dt: float — spatial distance per time bin (meters/bin)
      k: int — scattering parameter
      area: float — physical area of relay wall (meters). Required for correct scaling.
      use_fdh: bool — use FDH mode

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N)
    """
    if area is None:
        area = float(tau.shape[0])

    # Step 1: Time integration
    phi = quasi_fresnel_time_integral(tau, s, dt, k)

    # Step 2: Spatial deconvolution
    psi = quasi_fresnel_spatial_deconv(phi, s, area)

    # Step 3: Extract albedo and depth
    # Use finite differences for better depth estimation
    ds = s * 0.01  # small step for numerical derivative
    phi2 = quasi_fresnel_time_integral(tau, s + ds, dt, k)
    psi2 = quasi_fresnel_spatial_deconv(phi2, s + ds, area)

    albedo, depth = extract_albedo_depth(psi, s, psi2, ds)

    return albedo, depth


def benchmark_reconstruction(tau, s, dt, k=4, area=None):
    """
    Benchmark the reconstruction: measure runtime and memory.
    """
    import time
    import tracemalloc

    if area is None:
        area = float(tau.shape[0])

    tracemalloc.start()

    t0 = time.perf_counter()
    # Step 1: Time integration
    phi = quasi_fresnel_time_integral(tau, s, dt, k)
    t1 = time.perf_counter()

    # Step 2: Spatial deconvolution
    psi = quasi_fresnel_spatial_deconv(phi, s, area)
    t2 = time.perf_counter()

    # Also compute at s+ds for depth extraction
    ds = s * 0.01
    phi2 = quasi_fresnel_time_integral(tau, s + ds, dt, k)
    psi2 = quasi_fresnel_spatial_deconv(phi2, s + ds, area)
    t3 = time.perf_counter()

    # Step 3: Extract albedo and depth
    albedo, depth = extract_albedo_depth(psi, s, psi2, ds)
    t4 = time.perf_counter()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        'albedo': albedo,
        'depth': depth,
        'timing': {
            'time_integration': t1 - t0,
            'spatial_deconv': t2 - t1,
            'depth_extraction': t3 - t2,
            'result_extraction': t4 - t3,
            'total': t4 - t0,
        },
        'memory_mb': peak / (1024 * 1024),
    }
