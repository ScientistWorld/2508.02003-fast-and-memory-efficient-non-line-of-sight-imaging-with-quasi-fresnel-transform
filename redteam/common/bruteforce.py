"""Exhaustive volumetric spherical backprojection baseline.

Evaluates every (64 x 64 x T) candidate voxel against every wall measurement.
Uses only transient histograms and acquisition metadata; never loads labels.
This deliberately spends O(N^4 T) work and O(N^2 T) scene memory, the costs
that direct surface reconstruction aims to avoid.
"""
import numpy as np
from numba import njit, prange
from scipy.ndimage import laplace


@njit(parallel=True, cache=True)
def exhaustive(tau, area, dt, k):
    nx, ny, nt = tau.shape
    volume = np.zeros((nx, ny, nt), dtype=np.float64)
    for i in prange(nx):
        for j in range(ny):
            for z in range(nt):
                depth = (z + 0.5)*dt
                total = 0.0
                norm = 0.0
                for wi in range(nx):
                    dx = (i-wi)*area/max(nx-1, 1)
                    for wj in range(ny):
                        dy = (j-wj)*area/max(ny-1, 1)
                        distance = np.sqrt(dx*dx + dy*dy + depth*depth)
                        b = min(int(distance/dt), nt-1)
                        weight = 1.0/(distance**k + 1e-30)
                        total += weight*tau[wi,wj,b]
                        norm += weight*weight
                volume[i,j,z] = total/np.sqrt(norm + 1e-30)
    return volume


def reconstruct(tau, s, dt, k=4, area=None, wall_x=None, wall_y=None,
                use_fdh=False, integration_mode='traditional'):
    volume = exhaustive(tau, float(area), float(dt), int(k))
    # Classical high-pass filtering removes the backprojection's smooth haze.
    filtered = np.maximum(-laplace(volume), 0.0)
    peak = np.argmax(filtered, axis=2)
    albedo = np.max(filtered, axis=2)
    depth = (peak + 0.5)*dt
    return albedo, depth
