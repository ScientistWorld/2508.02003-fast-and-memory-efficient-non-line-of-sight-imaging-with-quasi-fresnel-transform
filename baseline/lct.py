"""
Light-Cone Transform (LCT) baseline for NLOS imaging.

LCT is a state-of-the-art NLOS reconstruction method based on the
confocal geometry and the light-cone transform.
Based on: O'Toole et al., "Confocal non-line-of-sight imaging based on
the light-cone transform", Nature, 2018.
"""

import numpy as np
from numpy.fft import fftn, ifftn, fftfreq


def lct_reconstruct(tau, dt, k=4, c=299792458, z_range=None):
    """
    Light-Cone Transform for NLOS reconstruction.

    The LCT relates the time-resolved measurement on the relay wall
    to the hidden scene using a light-cone transformation. This is
    implemented via a 3D Fourier transform with specific scaling.

    Parameters:
      tau: array of shape (N, N, N_bins) — time-resolved measurement
      dt: float — time bin width in meters
      k: int — scattering parameter
      c: float — speed of light in m/s

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N) in meters
    """
    N = tau.shape[0]
    N_bins = tau.shape[2]

    if z_range is None:
        z_range = N_bins

    # Convert time to depth: z = c*t/2
    z_bins = np.arange(N_bins) * dt * c / 2

    # Step 1: Apply the light-cone transform kernel
    # The LCT kernel in Fourier domain is: K(w_x, w_y, w_z) = exp(-i*w_z*z_0)
    # where z_0 is the depth. We use a simplified version.

    # Compute the 3D Fourier transform of tau
    tau_ft = fftn(tau)

    # Frequency coordinates
    dx = dt  # Relay wall spacing (approximation)
    freq_x = fftfreq(N, dx)
    freq_y = fftfreq(N, dx)
    freq_z = fftfreq(N_bins, dt * c / 2)

    FX, FY, FZ = np.meshgrid(freq_x, freq_y, freq_z, indexing='ij')

    # LCT kernel: H(kx, ky, kz) = exp(-i * kz / kx^2 + ky^2)
    # Simplified: use a Gaussian-shaped kernel
    k_norm_sq = FX**2 + FY**2 + 1e-10
    kernel = np.exp(-1j * FZ / np.sqrt(k_norm_sq))

    # Apply kernel
    psi_ft = tau_ft * kernel

    # Inverse 3D FFT
    psi = np.real(ifftn(psi_ft))

    # Step 2: Extract best z-slice (maximum intensity)
    albedo = np.max(psi, axis=2)
    albedo = albedo / (albedo.max() + 1e-10)

    # Find depth of maximum response for each pixel
    depth_map = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            peak_z = np.argmax(psi[i, j, :])
            depth_map[i, j] = z_bins[min(peak_z, N_bins-1)]

    # Normalize depth
    if depth_map.max() > 0.1:
        depth_map = depth_map / depth_map.max() * 2.0

    return albedo, depth_map
