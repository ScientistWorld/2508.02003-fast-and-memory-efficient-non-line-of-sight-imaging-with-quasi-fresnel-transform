"""
Load Zaragoza NLOS dataset (HDF5 format) and convert to NPZ.

The Zaragoza dataset stores confocal NLOS measurements in HDF5 files.
Typical structure:
  - 'data': 3D histogram (N x N x N_bins) — confocal measurements
  - 'albedo': ground truth albedo (N x N)
  - 'depth': ground truth depth map (N x N)
  - metadata attributes on the file/group

Reference: https://graphics.unizar.es/nlos_dataset.html
"""

import numpy as np
import os


def load_zaragoza_hdf5(hdf5_path, dt=0.003, k=4, area=0.6):
    """
    Load a Zaragoza NLOS HDF5 file and return data in standard format.

    Parameters:
      hdf5_path: path to .hdf5 file
      dt: spatial distance per time bin (meters). Default 0.003 for Zaragoza.
      k: scattering parameter (4=isotropic)
      area: relay wall area in meters (0.6 for Zaragoza)

    Returns:
      dict with keys: tau, albedo, depth, dt, k, area, scene_name
    """
    import h5py

    with h5py.File(hdf5_path, 'r') as f:
        # Print available keys for debugging
        keys = list(f.keys())
        print(f"  HDF5 keys: {keys}")

        # Print attributes
        for attr_name in f.attrs:
            print(f"  Attr {attr_name}: {f.attrs[attr_name]}")

        # Load measurement data
        if 'data' in f:
            tau = np.array(f['data'], dtype=np.float64)
        elif 'hist' in f:
            tau = np.array(f['hist'], dtype=np.float64)
        elif 'measurements' in f:
            tau = np.array(f['measurements'], dtype=np.float64)
        else:
            # Try first dataset
            for key in keys:
                ds = f[key]
                if isinstance(ds, h5py.Dataset) and ds.ndim == 3:
                    tau = np.array(ds, dtype=np.float64)
                    print(f"  Using dataset '{key}' as tau")
                    break
            else:
                raise ValueError(f"No 3D dataset found. Available keys: {keys}")

        # Try to load ground truth
        albedo = None
        depth = None

        for key in keys:
            ds = f[key]
            if not isinstance(ds, h5py.Dataset):
                continue
            if key in ('data', 'hist', 'measurements'):
                continue
            if ds.ndim == 2:
                if 'albedo' in key.lower():
                    albedo = np.array(ds, dtype=np.float64)
                elif 'depth' in key.lower() or 'z' in key.lower():
                    depth = np.array(ds, dtype=np.float64)

        # If no ground truth found, create dummy (real evaluation uses visual inspection)
        if albedo is None:
            N = tau.shape[0]
            albedo = np.ones((N, N), dtype=np.float64)
            print("  Warning: No ground truth albedo found, using dummy")

        if depth is None:
            N = tau.shape[0]
            depth = np.ones((N, N), dtype=np.float64) * 0.5
            print("  Warning: No ground truth depth found, using dummy")

        # Read metadata from attributes
        scene_name = os.path.basename(hdf5_path).split('_')[0]

        # Try to read dt from attributes
        if 'delta_t' in f.attrs:
            dt = float(f.attrs['delta_t'])
            print(f"  Using dt={dt} from file attributes")

    print(f"  tau shape: {tau.shape}")
    print(f"  tau range: [{tau.min():.6f}, {tau.max():.6f}]")

    # Handle Zaragoza data format:
    # Confocal: data shape is (N_laser_points, N_patterns, N_time, N_scan_per_axis)
    # or (N_laser_points, N_patterns, N_time_bins) for some files.
    # For confocal measurement: laser_i == camera_i, extract diagonal.
    #
    # Typical confocal 4D shape: (N^2, patterns, T, N_scan) where N^2 is laser grid
    # We need to reshape to (N_scan, N_scan, N_time) for confocal extraction.
    if tau.ndim == 4:
        n_laser = tau.shape[0]
        n_pat = tau.shape[1]
        n_t = tau.shape[2]
        n_scan = tau.shape[3]
        print(f"  4D data detected: ({n_laser}, {n_pat}, {n_t}, {n_scan})")

        # For confocal: grid size is sqrt(n_laser) x sqrt(n_laser)
        grid_size = int(np.sqrt(n_laser))
        scan_grid = n_scan  # scan points per axis

        if grid_size * grid_size == n_laser:
            print(f"  Laser grid: {grid_size}x{grid_size}, scan: {scan_grid}, patterns: {n_pat}, time: {n_t}")
            # Confocal extraction: for each laser position i, take measurement at
            # matching scan position. Pattern dim is averaged or first used.
            # Reshape laser dim to 2D grid
            conf_tau = np.zeros((grid_size, grid_size, n_t), dtype=np.float64)
            for i in range(grid_size):
                for j in range(grid_size):
                    laser_idx = i * grid_size + j
                    # Average over patterns, extract this laser's time signal
                    conf_tau[i, j, :] = tau[laser_idx, :, :, j].mean(axis=0)
            tau = conf_tau
            print(f"  Extracted confocal: {tau.shape}")
        else:
            print(f"  Warning: n_laser={n_laser} not a perfect square, taking first pattern")
            tau = tau[:, 0, :, :]  # (N_laser, N_time, N_scan)
    elif tau.ndim == 3:
        if tau.shape[0] != tau.shape[1]:
            print(f"  Warning: non-square spatial dims {tau.shape[:2]}")

    return {
        'tau': tau,
        'albedo': albedo,
        'depth': depth,
        'dt': dt,
        'k': k,
        'area': area,
        'scene_name': scene_name,
    }


def convert_zaragoza_to_npz(hdf5_path, output_dir=None):
    """Convert Zaragoza HDF5 to NPZ format."""
    data = load_zaragoza_hdf5(hdf5_path)

    if output_dir is None:
        output_dir = os.path.dirname(hdf5_path)
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(hdf5_path))[0]
    out_path = os.path.join(output_dir, f'{base}.npz')
    np.savez_compressed(out_path, **data)
    print(f"  Saved to {out_path}")

    return out_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('hdf5_path', help='Path to Zaragoza HDF5 file')
    parser.add_argument('--output', help='Output directory')
    args = parser.parse_args()
    convert_zaragoza_to_npz(args.hdf5_path, args.output)
