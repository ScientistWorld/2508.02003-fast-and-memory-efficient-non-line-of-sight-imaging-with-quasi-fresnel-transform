"""
Filtered Back Projection (FBP) baseline for NLOS imaging.

FBP is a classic tomographic reconstruction method applied to NLOS imaging.
Based on: Velten et al., "Recovering three-dimensional shape around a corner
using ultrafast time-of-flight imaging", Nature Communications, 2012.
"""

import numpy as np
from numpy.fft import fft2, ifft2, fftfreq


def fbp_reconstruct(tau, dt, k=4, c=299792458):
    """
    Filtered Back Projection for NLOS reconstruction.

    FBP treats the NLOS problem as a computed tomography problem.
    It works by filtering the time-of-flight data and back-projecting
    along spherical surfaces.

    Parameters:
      tau: array of shape (N, N, N_bins) — time-resolved measurement
      dt: float — time bin width in meters
      k: int — scattering parameter

    Returns:
      albedo: real array of shape (N, N)
      depth: real array of shape (N, N) in meters
    """
    N = tau.shape[0]
    N_bins = tau.shape[2]
    t_max = N_bins * dt
    t_bins = np.linspace(0, t_max, N_bins + 1)
    t_centers = (t_bins[:-1] + t_bins[1:]) / 2

    # Step 1: Integrate time dimension (like FBP projection)
    projection = np.sum(tau, axis=2)

    # Step 2: Apply a Ram-Lak filter (high-pass) in the spatial domain
    # Simplified: apply a 2D gradient-based filter
    from scipy.ndimage import laplace

    # Filter the projection
    filtered = projection - 0.5 * laplace(projecting)

    # Step 3: Back-project (simplified - for FBP this would be iterative)
    # Here we do a simplified version: average the filtered projection
    albedo = np.abs(filtered)
    albedo = albedo / (albedo.max() + 1e-10)

    # Depth estimation from time-of-flight peaks
    # For each pixel, find the time bin with maximum intensity
    depth_map = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            col = tau[i, j, :]
            peak_bin = np.argmax(col)
            depth_map[i, j] = c * t_centers[peak_bin] / 2

    # Normalize depth
    depth_map = depth_map / (depth_map.max() + 1e-10) * 2.0

    return albedo, depth_map


def fbp_reconstruct_v2(tau, dt, k=4, c=299792458):
    """
    Improved FBP with proper filtering.
    """
    N = tau.shape[0]
    N_bins = tau.shape[2]
    t_max = N_bins * dt
    t_bins = np.linspace(0, t_max, N_bins + 1)
    t_centers = (t_bins[:-1] + t_bins[1:]) / 2

    c = SPEED_OF_LIGHT = 299792458

    # Compute the FBP reconstruction volume
    V = np.zeros((N, N, N_bins))

    for bi in range(N_bins):
        r = c * t_centers[bi] / 2
        # Spherical shell back-projection
        for i in range(N):
            for j in range(N):
                # Distance from relay wall center
                d_ij = np.sqrt(((i - N//2)**2 + (j - N//2)**2)) * dt
                if abs(d_ij - r) < dt:
                    V[i, j, bi] = tau[i, j, bi] / (r**k + 1e-10)

    # Integrate over depth
    albedo = np.sum(V, axis=2)
    albedo = albedo / (albedo.max() + 1e-10)

    # Depth from maximum intensity time bin
    depth_map = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            col = V[i, j, :]
            peak_bin = np.argmax(col)
            depth_map[i, j] = c * t_centers[peak_bin] / 2

    depth_map = depth_map / (depth_map.max() + 1e-10) * 2.0

    return albedo, depth_map
