"""
NLOS Quasi-Fresnel Transform Data Generation

Generates synthetic time-resolved NLOS measurements based on the
three-point transport model from the paper.

Usage:
  python data/generate_nlos_data.py --scene kylin --resolution 64
  python data/generate_nlos_data.py --scene bunny --resolution 128
  python data/generate_nlos_data.py --scene dynamic --resolution 32
"""

import numpy as np
import argparse
import os
from pathlib import Path

SPEED_OF_LIGHT = 299792458  # m/s
DEFAULT_AREA = 1.0  # m (1m x 1m relay wall)
DEFAULT_DT = 0.003  # m per time bin (for Zaragoza dataset)
DEFAULT_K = 4  # 4 for isotropic scattering, 2 for retroreflective


def generate_scene(scene_name, N, area=1.0, default_depth=0.3):
    """
    Generate a synthetic hidden scene (albedo + depth map). Fully vectorized.

    Parameters:
      scene_name: type of scene ('kylin', 'bunny', 'shapes', etc.)
      N: grid resolution
      area: physical size in meters
      default_depth: default depth of the hidden scene in meters.
        The forward model uses dt (distance per bin) and N_bins to determine
        the capture range. For realistic NLOS data, depth should be within
        (N_bins * dt) to ensure the signal falls within the time window.
        Default 0.3m works well with dt=0.003m and N_bins=128+.
    """
    x = np.linspace(-area/2, area/2, N)
    y = np.linspace(-area/2, area/2, N)
    X, Y = np.meshgrid(x, y, indexing='ij')
    cx, cy = N // 2, N // 2
    xn = (X - X[cx, cy]) / area  # normalize by physical size
    yn = (Y - Y[cx, cy]) / area  # so xn, yn in [-0.5, 0.5]

    albedo = np.zeros((N, N), dtype=np.float64)
    depth = np.ones((N, N), dtype=np.float64) * default_depth

    if scene_name == "kylin":
        # Body ellipse — scaled to fit within [-0.45, 0.45] (within area bounds)
        body = (xn / 0.20)**2 + (yn / 0.15)**2 < 1
        # Legs (4 simple rectangles) — fully vectorized, scaled
        leg_positions = [(0.35, 0.25), (-0.35, 0.25), (0.35, -0.25), (-0.35, -0.25)]
        for lx, ly in leg_positions:
            leg = (np.abs(xn - lx) < 0.025) & (np.abs(yn - ly) < 0.08)
            albedo[leg] = 0.7
        # Neck and head
        neck = (np.abs(xn - 0.12) < 0.04) & (0 <= yn - 0.12) & (yn - 0.12 < 0.18)
        albedo[neck] = 0.8
        head = (xn - 0.12)**2 + (yn - 0.32)**2 < (0.06)**2
        albedo[head] = 0.8
        # Horn
        horn = (np.abs(xn - 0.12) < 0.008) & (0.22 < yn - 0.12) & (yn - 0.12 < 0.35)
        albedo[horn] = 0.7
        # Tail
        tail = (np.abs(yn + 0.20) < 0.025) & (0.12 < xn + 0.20) & (xn + 0.20 < 0.32)
        albedo[tail] = 0.6
        albedo[body] = 0.8
        # Background noise — vectorized, no Python loop
        mask = albedo == 0
        albedo[mask] = np.random.rand(N, N)[mask] * 0.05

        # Depth varies with distance from center — fully vectorized
        depth = np.where(albedo > 0,
                         default_depth + 0.01 * (xn**2 + yn**2),
                         default_depth)

    elif scene_name == "bunny":
        # Stanford bunny - Gaussian blob with ears
        sigma = 0.2
        xn_flat = xn.ravel()
        yn_flat = yn.ravel()
        r = np.sqrt(xn_flat**2 + 0.8 * yn_flat**2)
        # Torso
        val = np.exp(-2 * r**2)
        # Ears
        ear1 = np.exp(-20 * ((xn_flat - 0.3)**2 + (yn_flat - 0.5)**2))
        ear2 = np.exp(-20 * ((xn_flat - 0.3)**2 + (yn_flat + 0.5)**2))
        val = np.maximum(val, ear1 * 0.8)
        val = np.maximum(val, ear2 * 0.8)
        albedo = val.reshape(N, N)
        albedo = albedo / (albedo.max() + 1e-8) * 0.9
        depth = default_depth + 0.01 * r.reshape(N, N)

    elif scene_name == "usaf":
        # USAF 1951 resolution chart — fully vectorized
        albedo_mask = np.zeros((N, N), dtype=bool)
        for group in range(6):
            for element in range(6):
                freq = 2**(group + element / 6)
                period = int(N // (freq * 4))
                if period < 2:
                    continue
                # Vertical bars
                bar_x = int((cx + (element - 3) * period) % N)
                if 0 <= bar_x < N:
                    bar = np.zeros((N, N), dtype=bool)
                    bar[:, max(0, bar_x - period//2):min(N, bar_x + period//2)] = True
                    bar = bar & (np.abs(Y / N) < 0.4)
                    albedo_mask |= bar
                # Horizontal bars
                bar_y = int((cy + (element - 3) * period) % N)
                if 0 <= bar_y < N:
                    bar = np.zeros((N, N), dtype=bool)
                    bar[max(0, bar_y - period//2):min(N, bar_y + period//2), :] = True
                    bar = bar & (np.abs(X / N) < 0.4)
                    albedo_mask |= bar
        albedo[albedo_mask] = 1.0

    elif scene_name == "letters":
        # Simple shapes — fully vectorized using broadcasting, no per-pixel Python loops
        N_letter_size = N // 4
        offset_x = cx - N_letter_size
        offset_y = cy - N_letter_size

        # Create 2D index grids for the letter region: di[i,j]=i, dj[i,j]=j  (both N_ls, N_ls)
        di, dj = np.meshgrid(np.arange(N_letter_size), np.arange(N_letter_size), indexing='ij')

        # Global pixel indices for the letter region: (N_ls, N_ls) arrays
        gx = offset_x + di  # (N_ls, N_ls)
        gy = offset_y + dj  # (N_ls, N_ls)

        # Boolean masks for in-bounds pixels
        in_bounds = (gx >= 0) & (gx < N) & (gy >= 0) & (gy < N)

        # === Letter N ===
        # Left bar (di < N_ls/5), diagonal (|di-dj| < N_ls/5), right bar (di >= 4*N_ls/5)
        left_bar_n = di < N_letter_size // 5
        diag_n = np.abs(di - dj) < N_letter_size // 5
        right_bar_n = di >= N_letter_size * 4 // 5
        n_mask = (left_bar_n | diag_n | right_bar_n) & in_bounds
        albedo[gx[n_mask], gy[n_mask]] = 0.8
        depth[gx[n_mask], gy[n_mask]] = default_depth

        # === Letter L ===
        offset_x2 = offset_x + N_letter_size
        offset_y2 = offset_y
        gx2 = offset_x2 + di
        gy2 = offset_y2 + dj
        in_bounds2 = (gx2 >= 0) & (gx2 < N) & (gy2 >= 0) & (gy2 < N)
        # Vertical bar (di < N_ls/5) OR horizontal bar (dj < N_ls/5)
        vert_l = di < N_letter_size // 5
        horz_l = dj < N_letter_size // 5
        l_mask = (vert_l | horz_l) & in_bounds2
        albedo[gx2[l_mask], gy2[l_mask]] = 0.8
        # Horizontal bar at slightly different depth
        depth[gx2[l_mask], gy2[l_mask]] = np.where(horz_l[l_mask], default_depth + 0.01, default_depth)

    elif scene_name == "dynamic":
        # Dynamic scene - simple block
        albedo = np.zeros((N, N), dtype=np.float64)
        albedo[N//4:3*N//4, N//4:3*N//4] = 0.8
        depth = np.ones((N, N), dtype=np.float64) * default_depth
        depth[N//4:3*N//4, N//4:3*N//4] = default_depth

    elif scene_name == "shapes":
        # Multiple geometric shapes at different depths
        # Circle
        r_grid = np.sqrt(xn**2 + yn**2)
        circle = r_grid < 0.15
        albedo[circle] = 0.8
        depth[circle] = default_depth

        # Square at slightly different depth
        square = (np.abs(xn - 0.3) < 0.12) & (np.abs(yn + 0.2) < 0.12)
        albedo[square] = 0.7
        depth[square] = default_depth + 0.02

        # Triangle
        tri_x = xn + 0.3
        tri_y = yn - 0.3
        triangle = (tri_x > 0) & (tri_x < 0.2) & (tri_y > -0.1) & (tri_y < 0.1) & (tri_y > tri_x - 0.15)
        albedo[triangle] = 0.6
        depth[triangle] = default_depth - 0.02

        # Rectangle
        rect = (np.abs(xn + 0.3) < 0.15) & (np.abs(yn) < 0.08)
        albedo[rect] = 0.9
        depth[rect] = default_depth + 0.05

    else:
        # Default: simple centered blob
        r_grid = np.sqrt(xn**2 + yn**2)
        blob = r_grid < 0.3
        albedo[blob] = 0.8 * (1 - r_grid[blob])
        depth[blob] = default_depth + 0.03 * r_grid[blob]

    return albedo.astype(np.float64), depth.astype(np.float64)


def forward_model_vectorized(albedo, depth, N_relay=64, N_bins=64, area=1.0, dt=0.003, k=4):
    """
    Fully vectorized forward model: compute time-resolved NLOS measurements.
    Based on the three-point transport model from the paper (Eq. 2).

    Physics: for each scene pixel at (xs, ys, depth), its contribution goes to
    relay wall point (xr, yr) at time bin b where the round-trip distance
    d = sqrt((xr-xs)^2 + (yr-ys)^2 + depth^2) maps to bin b.

    Strategy: per-depth-slice vectorization. For each unique depth value (scene row),
    compute all pairwise distances between relay points and that row's scene pixels
    in one vectorized operation using 4D broadcasting, then bin and accumulate.
    This eliminates the triple-nested Python loops while keeping memory bounded.

    Memory: O(N_relay^2 * N_scene) per slice.
    For N=64: ~8M elements per slice = ~64 MB — acceptable.

    Parameters:
      albedo: (N_scene, N_scene) array of surface albedos
      depth: (N_scene, N_scene) array of scene depths (meters)
      N_relay: relay wall resolution
      N_bins: number of time bins
      area: scene/relay wall area (meters)
      dt: spatial distance per time bin (meters)
      k: scattering exponent

    Returns:
      tau: (N_relay, N_relay, N_bins) time-resolved measurements
    """
    c = SPEED_OF_LIGHT
    N_scene = albedo.shape[0]

    # Relay wall coordinate grids — shape (N_relay, N_relay)
    x_relay = np.linspace(-area/2, area/2, N_relay)
    y_relay = np.linspace(-area/2, area/2, N_relay)
    Xr, Yr = np.meshgrid(x_relay, y_relay, indexing='ij')

    # Scene coordinate grids — shape (N_scene, N_scene)
    x_scene = np.linspace(-area/2, area/2, N_scene)
    y_scene = np.linspace(-area/2, area/2, N_scene)
    Xs, Ys = np.meshgrid(x_scene, y_scene, indexing='ij')

    # Precompute time bin edges (in spatial distance = meters)
    t_max = N_bins * dt
    bin_edges = np.linspace(0.0, t_max, N_bins + 1)

    # Scene area element
    dA = (area / N_scene) ** 2

    # Output: (N_relay, N_relay, N_bins)
    tau = np.zeros((N_relay, N_relay, N_bins), dtype=np.float64)

    relay_flat_size = N_relay * N_relay

    for i in range(N_scene):
        d_row = depth[i, :]
        a_row = albedo[i, :]

        if np.sum(a_row) < 1e-6:
            continue

        xs_row = Xs[i, :]
        ys_row = Ys[i, :]

        dx_sq = (Xr[:, :, np.newaxis] - xs_row[np.newaxis, np.newaxis, :]) ** 2
        dy_sq = (Yr[:, :, np.newaxis] - ys_row[np.newaxis, np.newaxis, :]) ** 2
        dist_sq = dx_sq + dy_sq + d_row[np.newaxis, np.newaxis, :] ** 2
        dist = np.sqrt(dist_sq)  # (N_relay, N_relay, N_scene)

        dist_flat = dist.reshape(relay_flat_size, N_scene)

        bin_idx = np.digitize(dist_flat.ravel(), bin_edges) - 1
        bin_idx = np.clip(bin_idx, 0, N_bins - 1)

        # Correct confocal weight: albedo * dA / dist^k
        weight = (a_row[np.newaxis, :] * dA / (dist_flat ** k + 1e-30)).ravel()

        relay_idx = np.repeat(np.arange(relay_flat_size), N_scene)
        linear_idx = relay_idx * N_bins + bin_idx

        tau_flat = tau.ravel()
        np.add.at(tau_flat, linear_idx, weight)

    # Add mild Poisson-like noise (optional; disabled by default for cleaner
    # evaluation of the reconstruction method itself)
    return tau.astype(np.float64)


def generate_dataset(scene_name, N_relay, N_bins, area=1.0, dt=0.003, k=4, N_scene=None, default_depth=0.3):
    """Generate a complete NLOS dataset."""
    if N_scene is None:
        N_scene = N_relay

    print(f"  Generating scene '{scene_name}' ({N_scene}x{N_scene}) at depth {default_depth}m...")
    albedo, depth = generate_scene(scene_name, N_scene, area, default_depth)

    print(f"  Computing forward model ({N_relay}x{N_relay}x{N_bins})...")
    tau = forward_model_vectorized(albedo, depth, N_relay, N_bins, area, dt, k)

    return {
        'tau': tau,
        'albedo': albedo,
        'depth': depth,
        'N_relay': N_relay,
        'N_bins': N_bins,
        'N_scene': N_scene,
        'area': area,
        'dt': dt,
        'k': k,
        'scene_name': scene_name,
        'default_depth': default_depth,
    }


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic NLOS data')
    parser.add_argument('--scene', type=str, default='kylin',
                        choices=['kylin', 'usaf', 'bunny', 'letters', 'dynamic', 'shapes', 'default'],
                        help='Scene type to generate')
    parser.add_argument('--resolution', type=int, default=64,
                        help='Relay wall resolution (N x N scanning points)')
    parser.add_argument('--bins', type=int, default=128,
                        help='Number of time bins')
    parser.add_argument('--area', type=float, default=1.0,
                        help='Relay wall area in meters')
    parser.add_argument('--dt', type=float, default=0.003,
                        help='Time bin width in meters')
    parser.add_argument('--k', type=int, default=4,
                        help='Scattering parameter (4=isotropic, 2=retroreflective)')
    parser.add_argument('--depth', type=float, default=0.3,
                        help='Default scene depth in meters (must be within capture range of N_bins * dt)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory')
    parser.add_argument('--save', action='store_true',
                        help='Save generated data to disk')

    args = parser.parse_args()

    out_dir = args.output or f'/home/user/data/{args.scene}'
    os.makedirs(out_dir, exist_ok=True)

    print(f"Generating NLOS data for scene '{args.scene}'...")
    print(f"  Relay wall: {args.resolution}x{args.resolution}")
    print(f"  Time bins: {args.bins}")
    print(f"  Area: {args.area}m x {args.area}m")
    print(f"  Time resolution: {args.dt}m ({args.dt/SPEED_OF_LIGHT*1e12:.2f} ps)")
    print(f"  Default depth: {args.depth}m")
    print(f"  Max capture range: {args.bins * args.dt}m (round-trip)")

    data = generate_dataset(args.scene, args.resolution, args.bins, args.area, args.dt, args.k, default_depth=args.depth)

    if args.save:
        out_path = os.path.join(out_dir, f'{args.scene}_{args.resolution}x{args.resolution}.npz')
        np.savez_compressed(out_path, **data)
        print(f"  Saved to {out_path}")

    print(f"  Generated tau shape: {data['tau'].shape}")
    print(f"  Albedo range: [{data['albedo'].min():.3f}, {data['albedo'].max():.3f}]")
    print(f"  Depth range: [{data['depth'].min():.3f}, {data['depth'].max():.3f}] m")
    print(f"  Tau range: [{data['tau'].min():.3f}, {data['tau'].max():.3f}]")
    print(f"  Tau non-zero fraction: {np.count_nonzero(data['tau'])/data['tau'].size:.2%}")

    return data


if __name__ == '__main__':
    main()
