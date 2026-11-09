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


def quasi_fresnel_time_integral_loading(tau, s_values, dt, k=4):
    """
    Step 1 with the paper's sequential-loading strategy.

    This computes the same aggregated measurement phi(x; s) as
    ``quasi_fresnel_time_integral`` but accumulates it bin by bin instead of
    materializing a full ``weights * tau`` tensor. When multiple nearby
    ``s`` values are required for depth extraction, all corresponding phi
    arrays are accumulated in the same pass over the histogram.

    Parameters:
      tau: array of shape (N, N, N_bins) — time-resolved measurement
      s_values: float or sequence of floats — Quasi-Fresnel parameter(s)
      dt: float — spatial distance per time bin (meters/bin)
      k: int — scattering parameter (4=isotropic, 2=retroreflective)

    Returns:
      complex array if one s is provided, otherwise tuple of complex arrays.
    """
    return quasi_fresnel_time_integral_stream(
        (tau[:, :, bin_idx] for bin_idx in range(tau.shape[2])), s_values, dt, k
    )


def quasi_fresnel_time_integral_stream(bins, s_values, dt, k=4):
    """
    Step 1 for a histogram that is read sequentially, one time bin at a time.

    ``bins`` yields the 2D slices ``tau(:, :, t)`` for t = 0, 1, ...; only the
    current slice and the 2D ``phi`` accumulators are ever held in memory, which
    is the paper's sequential-loading strategy (memory O(N^2) instead of O(N^3)).
    The arithmetic is identical to ``quasi_fresnel_time_integral``.
    """
    s_arr = np.atleast_1d(np.asarray(s_values, dtype=np.float64))
    if s_arr.ndim != 1 or s_arr.size == 0:
        raise ValueError("s_values must be a scalar or a non-empty 1D sequence")

    accumulators = None
    for bin_idx, tau_bin in enumerate(bins):
        tau_bin = np.asarray(tau_bin).astype(np.float64, copy=False)
        if accumulators is None:
            accumulators = [
                np.zeros(tau_bin.shape, dtype=np.complex128) for _ in range(s_arr.size)
            ]
        r = (bin_idx + 0.5) * dt
        radial_term = r ** k
        for acc, s in zip(accumulators, s_arr):
            weight = radial_term * np.exp(-1j * (r ** 2) / (4 * s ** 2)) * dt
            acc += weight * tau_bin

    if accumulators is None:
        raise ValueError("the histogram has no time bins")
    if len(accumulators) == 1:
        return accumulators[0]
    return tuple(accumulators)


def quasi_fresnel_fdh_aggregate(tau, s_values, dt, k=4):
    """
    Paper's FDH-style temporal aggregation path.

    Eq. (6) rewrites the Quasi-Fresnel time integral as a complex weighted
    histogram that can be accumulated during acquisition. In this software
    reproduction we emulate that hardware path by streaming over time bins and
    returning only the aggregated two-dimensional ``phi`` arrays. The downstream
    reconstruction then starts from ``phi`` and never needs a volumetric hidden
    scene or a 3D FFT.
    """
    return quasi_fresnel_time_integral_loading(tau, s_values, dt, k)


def _centered_coordinates(n, spacing):
    return (np.arange(n, dtype=np.float64) - (n - 1) / 2.0) * spacing


def _quadrature_spacing(coords):
    if coords.size < 2:
        return 1.0
    diffs = np.diff(coords)
    return float(np.mean(np.abs(diffs)))


def _is_uniform_grid(coords, rtol=1e-5, atol=1e-9):
    if coords.size < 3:
        return True
    diffs = np.diff(coords)
    return bool(np.allclose(diffs, diffs[0], rtol=rtol, atol=atol))


def _next_fast_length(size):
    length = 1
    while length < size:
        length <<= 1
    return length


def _fft_convolve_same_axis(data, kernel, axis):
    """
    Linear convolution with centered ``same`` output along one axis.

    ``kernel`` is assumed to be indexed on offsets ``[-n+1, ..., n-1]`` where
    ``n`` is the size of ``data`` along ``axis``.
    """
    n = data.shape[axis]
    m = kernel.shape[0]
    full_length = n + m - 1
    fft_length = _next_fast_length(full_length)

    data_fft = np.fft.fft(data, n=fft_length, axis=axis)
    reshape = [1] * data.ndim
    reshape[axis] = m
    kernel_fft = np.fft.fft(kernel.reshape(reshape), n=fft_length, axis=axis)
    convolved = np.fft.ifft(data_fft * kernel_fft, n=fft_length, axis=axis)

    start = (m - 1) // 2
    stop = start + n
    slicer = [slice(None)] * data.ndim
    slicer[axis] = slice(start, stop)
    return convolved[tuple(slicer)]


def _spatial_deconv_dense(phi, s, wall_x, wall_y, dx, dy):
    kernel_x = np.exp(
        1j * (wall_x[:, np.newaxis] - wall_x[np.newaxis, :]) ** 2 / (4.0 * s ** 2)
    ).astype(np.complex128)
    kernel_y = np.exp(
        1j * (wall_y[:, np.newaxis] - wall_y[np.newaxis, :]) ** 2 / (4.0 * s ** 2)
    ).astype(np.complex128)

    psi = kernel_x @ phi.astype(np.complex128, copy=False) @ kernel_y.T
    psi *= (dx * dy) / (16.0 * np.pi ** 2 * s ** 4)
    return psi


def quasi_fresnel_spatial_deconv(phi, s, area=None, wall_x=None, wall_y=None):
    """
    Step 2: Recover psi(x; s) from phi(x; s) via 2D convolution.

    Implements Eq. (5):
      psi(x; s) = (1/16*pi^2*s^4) * integral e^{i*|x~-x|^2/4s^2} * phi(x~;s) dx~

    On a uniform relay-wall grid the kernel depends only on coordinate
    differences, so Eq. (5) becomes a separable 2D convolution and can be
    evaluated in O(N^2 log N) time using FFTs, matching the paper's analysis.
    For nonuniform coordinates we fall back to the direct dense quadrature.

    Parameters:
      phi: complex array of shape (N, N)
      s: float — Quasi-Fresnel parameter (meters)
      area: float — physical area of the relay wall in meters
      wall_x: optional 1D x coordinates of relay-wall samples
      wall_y: optional 1D y coordinates of relay-wall samples

    Returns:
      psi: complex array of shape (N, N)
    """
    nx, ny = phi.shape
    if wall_x is None:
        if area is None:
            area = float(nx)
        dx = area / max(nx - 1, 1)
        wall_x = _centered_coordinates(nx, dx)
    else:
        wall_x = np.asarray(wall_x, dtype=np.float64)
        dx = _quadrature_spacing(wall_x)

    if wall_y is None:
        if area is None:
            area = float(ny)
        dy = area / max(ny - 1, 1)
        wall_y = _centered_coordinates(ny, dy)
    else:
        wall_y = np.asarray(wall_y, dtype=np.float64)
        dy = _quadrature_spacing(wall_y)

    phi_complex = phi.astype(np.complex128, copy=False)
    if not (_is_uniform_grid(wall_x) and _is_uniform_grid(wall_y)):
        return _spatial_deconv_dense(phi_complex, s, wall_x, wall_y, dx, dy)

    offsets_x = (np.arange(-(nx - 1), nx, dtype=np.float64)) * dx
    offsets_y = (np.arange(-(ny - 1), ny, dtype=np.float64)) * dy
    kernel_x = np.exp(1j * offsets_x ** 2 / (4.0 * s ** 2)).astype(np.complex128)
    kernel_y = np.exp(1j * offsets_y ** 2 / (4.0 * s ** 2)).astype(np.complex128)

    psi = _fft_convolve_same_axis(phi_complex, kernel_x, axis=0)
    psi = _fft_convolve_same_axis(psi, kernel_y, axis=1)
    psi *= (dx * dy) / (16.0 * np.pi ** 2 * s ** 4)
    return psi


def quasi_fresnel_reconstruct_from_phi(
    phi,
    s,
    area=None,
    wall_x=None,
    wall_y=None,
    phi_prev=None,
    phi_next=None,
    ds=None,
):
    """
    Reconstruct albedo/depth from pre-aggregated Quasi-Fresnel measurements.

    This is the software interface for the paper's FDH/hardware acquisition
    variant: the method receives one or more 2D complex ``phi(x; s)`` arrays,
    applies the separable spatial inversion in Eq. (5), and extracts albedo and
    depth using Eq. (4).
    """
    if area is None:
        area = float(phi.shape[0])

    psi_prev = None
    psi_next = None
    if ds is not None and ds > 0 and phi_prev is not None:
        psi_prev = quasi_fresnel_spatial_deconv(
            phi_prev, s - ds, area=area, wall_x=wall_x, wall_y=wall_y
        )
    psi = quasi_fresnel_spatial_deconv(phi, s, area=area, wall_x=wall_x, wall_y=wall_y)
    if ds is not None and ds > 0 and phi_next is not None:
        psi_next = quasi_fresnel_spatial_deconv(
            phi_next, s + ds, area=area, wall_x=wall_x, wall_y=wall_y
        )

    return extract_albedo_depth(psi, s, psi_prev=psi_prev, psi_next=psi_next, ds=ds)


def extract_albedo_depth(psi, s, psi_prev=None, psi_next=None, ds=None):
    """
    Step 3: Extract albedo and depth from psi(x; s).

    From Eq. (4): psi(x; s) = a(x) * exp(-i * d(x)^2 / 4s^2)

    Albedo: a(x) = |psi(x; s)|
    Depth: d(x) = sqrt(-2i * s^3 * psi^{-1} * dpsi/ds)

    When neighboring reconstructions are provided, depth is extracted via
    finite differences. Otherwise, depth is estimated from phase only.

    Parameters:
      psi: complex array of shape (N, N) — reconstruction at parameter s
      s: float — Quasi-Fresnel parameter
      psi_prev: complex array of shape (N, N) — reconstruction at s-ds (optional)
      psi_next: complex array of shape (N, N) — reconstruction at s+ds (optional)
      ds: float — step size for numerical differentiation

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N) in meters
    """
    albedo = np.abs(psi)

    if ds is not None and ds > 0 and (psi_prev is not None or psi_next is not None):
        eps = 1e-10
        psi_safe = np.where(
            np.abs(psi) > eps,
            psi,
            eps * np.exp(1j * np.angle(psi + eps)),
        )
        if psi_prev is not None and psi_next is not None:
            dpsi_ds = (psi_next - psi_prev) / (2.0 * ds)
        elif psi_next is not None:
            dpsi_ds = (psi_next - psi) / ds
        else:
            dpsi_ds = (psi - psi_prev) / ds
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


def quasi_fresnel_reconstruct(
    tau,
    s,
    dt,
    k=4,
    area=None,
    wall_x=None,
    wall_y=None,
    use_fdh=False,
    integration_mode="traditional",
):
    """
    Full Quasi-Fresnel Transform reconstruction pipeline.

    Parameters:
      tau: array of shape (N, N, N_bins)
      s: float — Quasi-Fresnel parameter (meters)
      dt: float — spatial distance per time bin (meters/bin)
      k: int — scattering parameter
      area: float — physical area of relay wall (meters). Required when explicit
        relay-wall coordinates are unavailable.
      wall_x: optional 1D x coordinates of relay-wall samples
      wall_y: optional 1D y coordinates of relay-wall samples
      use_fdh: bool — use FDH mode
      integration_mode: "traditional" for direct full-histogram integration or
        "loading" for the paper's sequential-loading accumulation

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N)
    """
    if area is None:
        area = float(tau.shape[0])

    # The paper uses very close s values in the regular confocal setting.
    # A coarse finite-difference step noticeably degrades depth estimates.
    ds = 1e-7
    if use_fdh:
        phi_prev, phi, phi_next = quasi_fresnel_fdh_aggregate(
            tau, (s - ds, s, s + ds), dt, k
        )
        return quasi_fresnel_reconstruct_from_phi(
            phi,
            s,
            area=area,
            wall_x=wall_x,
            wall_y=wall_y,
            phi_prev=phi_prev,
            phi_next=phi_next,
            ds=ds,
        )
    if integration_mode == "traditional":
        phi_prev = quasi_fresnel_time_integral(tau, s - ds, dt, k)
        phi = quasi_fresnel_time_integral(tau, s, dt, k)
        phi_next = quasi_fresnel_time_integral(tau, s + ds, dt, k)
    elif integration_mode == "loading":
        phi_prev, phi, phi_next = quasi_fresnel_time_integral_loading(
            tau, (s - ds, s, s + ds), dt, k
        )
    else:
        raise ValueError(
            f"Unsupported integration_mode={integration_mode!r}; "
            "expected 'traditional' or 'loading'"
        )

    # Step 2: Spatial deconvolution
    psi_prev = quasi_fresnel_spatial_deconv(
        phi_prev, s - ds, area=area, wall_x=wall_x, wall_y=wall_y
    )
    psi = quasi_fresnel_spatial_deconv(phi, s, area=area, wall_x=wall_x, wall_y=wall_y)
    psi_next = quasi_fresnel_spatial_deconv(
        phi_next, s + ds, area=area, wall_x=wall_x, wall_y=wall_y
    )

    albedo, depth = extract_albedo_depth(psi, s, psi_prev=psi_prev, psi_next=psi_next, ds=ds)

    return albedo, depth


def benchmark_reconstruction(tau, s, dt, k=4, area=None, wall_x=None, wall_y=None):
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
    psi = quasi_fresnel_spatial_deconv(phi, s, area=area, wall_x=wall_x, wall_y=wall_y)
    t2 = time.perf_counter()

    # Also compute at s+ds for depth extraction
    ds = 1e-7
    phi_prev = quasi_fresnel_time_integral(tau, s - ds, dt, k)
    phi2 = quasi_fresnel_time_integral(tau, s + ds, dt, k)
    psi_prev = quasi_fresnel_spatial_deconv(
        phi_prev, s - ds, area=area, wall_x=wall_x, wall_y=wall_y
    )
    psi2 = quasi_fresnel_spatial_deconv(
        phi2, s + ds, area=area, wall_x=wall_x, wall_y=wall_y
    )
    t3 = time.perf_counter()

    # Step 3: Extract albedo and depth
    albedo, depth = extract_albedo_depth(psi, s, psi_prev=psi_prev, psi_next=psi2, ds=ds)
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
