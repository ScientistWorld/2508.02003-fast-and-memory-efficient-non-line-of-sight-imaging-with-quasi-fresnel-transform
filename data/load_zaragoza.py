"""
Load Zaragoza NLOS datasets from HDF5.

The public Zaragoza files are not fully uniform: measurements can appear with
different axis orders, optional bounce dimensions, and nested metadata/groups.
This loader normalizes the confocal measurement to ``(Nx, Ny, T)`` and tries to
recover 2D ground-truth albedo/depth maps when the file exposes them directly or
via a hidden-scene voxel volume.
"""

from __future__ import annotations

import os
from typing import Iterable

import numpy as np


def _iter_datasets(group, prefix="") -> Iterable[tuple[str, object]]:
    import h5py

    for key, value in group.items():
        path = f"{prefix}/{key}" if prefix else key
        if isinstance(value, h5py.Dataset):
            yield path, value
        elif isinstance(value, h5py.Group):
            yield from _iter_datasets(value, path)


def _find_first(datasets, keywords, ndim=None):
    keywords = tuple(keyword.lower() for keyword in keywords)
    for path, dataset in datasets:
        leaf = path.rsplit("/", 1)[-1].lower()
        if any(keyword in leaf for keyword in keywords):
            if ndim is None or dataset.ndim == ndim:
                return path, dataset
    return None, None


def _read_numeric_dataset(dataset):
    return np.asarray(dataset[()], dtype=np.float64)


def _read_scalar_like(datasets, keywords, default):
    _, dataset = _find_first(datasets, keywords)
    if dataset is None:
        return default
    value = np.asarray(dataset[()]).reshape(-1)
    if value.size == 0:
        return default
    return float(value[0])


def _read_extent_like(datasets, keywords, default):
    _, dataset = _find_first(datasets, keywords)
    if dataset is None:
        return default
    value = np.asarray(dataset[()], dtype=np.float64)
    if value.ndim >= 2 and value.shape[-1] >= 2:
        coords = value.reshape(-1, value.shape[-1])[:, :2]
        spans = np.ptp(coords, axis=0)
        finite_spans = spans[np.isfinite(spans) & (spans > 0)]
        if finite_spans.size:
            return float(np.max(finite_spans))
    value = value.reshape(-1)
    if value.size == 0:
        return default
    if value.size == 1:
        return float(abs(value[0]))
    finite = np.abs(value[np.isfinite(value)])
    positive = finite[finite > 0]
    if positive.size:
        return float(np.max(positive[: min(2, positive.size)]))
    return default


def _extract_wall_coordinates(datasets, tau_shape):
    _, points_ds = _find_first(datasets, ("cameraGridPoints", "laserGridPoints"))
    points = None
    if points_ds is not None:
        points = np.asarray(points_ds[()]).reshape(-1)

    _, positions_ds = _find_first(datasets, ("cameraGridPositions", "laserGridPositions"))
    if positions_ds is None:
        return None, None

    positions = np.asarray(positions_ds[()], dtype=np.float64)
    positions = np.squeeze(positions)

    if positions.ndim == 3 and positions.shape[2] >= 2:
        wall_x = positions[:, 0, 0]
        wall_y = positions[0, :, 1]
    elif positions.ndim == 2 and positions.shape[1] >= 2:
        if points is not None and points.size >= 2:
            nx, ny = int(points[0]), int(points[1])
        else:
            nx = tau_shape[0]
            ny = tau_shape[1]
        if nx * ny != positions.shape[0]:
            return None, None
        grid = positions.reshape(nx, ny, positions.shape[1])
        wall_x = grid[:, 0, 0]
        wall_y = grid[0, :, 1]
    else:
        return None, None

    if len(wall_x) != tau_shape[0] or len(wall_y) != tau_shape[1]:
        return None, None
    return wall_x.astype(np.float64), wall_y.astype(np.float64)


def _extract_confocal_measurement(raw_tau):
    tau = np.asarray(raw_tau, dtype=np.float64)
    tau = np.squeeze(tau)

    # Some files carry extra singleton/color/bounce dimensions. Peel those off
    # conservatively until only spatial x/y and time remain.
    while tau.ndim > 3:
        shape = tau.shape
        time_axis = int(np.argmax(shape))
        candidate_axes = [axis for axis in range(tau.ndim) if axis != time_axis]
        small_axes = [axis for axis in candidate_axes if shape[axis] <= 8]
        if small_axes:
            bounce_axis = min(small_axes, key=lambda axis: shape[axis])
            bounce_index = 1 if shape[bounce_axis] > 1 else 0
            tau = np.take(tau, indices=bounce_index, axis=bounce_axis)
            continue
        reduce_axis = min(candidate_axes, key=lambda axis: shape[axis])
        tau = tau.mean(axis=reduce_axis)

    if tau.ndim != 3:
        raise ValueError(f"Expected a 3D confocal tensor after squeezing, got {tau.shape}")

    shape = tau.shape
    if shape[0] == shape[1] and shape[2] != shape[0]:
        return tau
    if shape[1] == shape[2] and shape[0] != shape[1]:
        return np.moveaxis(tau, 0, 2)
    if shape[0] == shape[2] and shape[1] != shape[0]:
        return np.moveaxis(tau, 1, 2)

    time_axis = int(np.argmax(shape))
    tau = np.moveaxis(tau, time_axis, 2)
    if tau.shape[0] != tau.shape[1]:
        raise ValueError(f"Unable to identify square spatial axes in measurement shape {shape}")
    return tau


def _select_depth_axis(volume):
    shape = volume.shape
    if shape[0] == shape[1] and shape[2] != shape[0]:
        return 2
    if shape[1] == shape[2] and shape[0] != shape[1]:
        return 0
    if shape[0] == shape[2] and shape[1] != shape[0]:
        return 1
    return 2


def _derive_surface_maps(volume, origin=None, size=None):
    voxel = np.asarray(volume, dtype=np.float64)
    voxel = np.squeeze(voxel)
    if voxel.ndim != 3:
        return None, None, False

    depth_axis = _select_depth_axis(voxel)
    if depth_axis != 2:
        voxel = np.moveaxis(voxel, depth_axis, 2)

    albedo = np.max(voxel, axis=2)
    depth_index = np.argmax(voxel, axis=2)

    if (
        origin is not None
        and size is not None
        and len(origin) >= 3
        and len(size) >= 3
        and np.isfinite(origin[2])
        and np.isfinite(size[2])
        and size[2] > 0
    ):
        depth_coords = origin[2] + (np.arange(voxel.shape[2], dtype=np.float64) + 0.5) * (
            float(size[2]) / voxel.shape[2]
        )
        depth = depth_coords[depth_index]
        return albedo, depth, True

    return albedo, depth_index.astype(np.float64), False


def load_zaragoza_hdf5(hdf5_path, dt=0.003, k=4, area=0.6):
    """
    Load a Zaragoza HDF5 file and return a normalized confocal example.

    Returns:
      dict with keys: tau, albedo, depth, dt, k, area, scene_name,
      has_albedo_gt, has_depth_gt, depth_metric_scale, wall_x, wall_y
    """
    import h5py

    with h5py.File(hdf5_path, "r") as handle:
        datasets = list(_iter_datasets(handle))
        dataset_paths = [path for path, _ in datasets]
        print(f"  HDF5 datasets: {dataset_paths[:12]}")

        measurement_path, measurement_ds = _find_first(
            datasets, ("data", "hist", "measurement", "transient")
        )
        if measurement_ds is None:
            raise ValueError(f"No measurement dataset found in {hdf5_path}")

        raw_tau = _read_numeric_dataset(measurement_ds)
        tau = _extract_confocal_measurement(raw_tau)

        dt = _read_scalar_like(datasets, ("deltaT", "delta_t", "deltat"), dt)
        area = _read_extent_like(
            datasets,
            ("cameraGridSize", "laserGridSize", "cameraGridPositions", "laserGridPositions"),
            area,
        )
        wall_x, wall_y = _extract_wall_coordinates(datasets, tau.shape)
        if wall_x is not None and wall_y is not None:
            area = float(max(wall_x.max() - wall_x.min(), wall_y.max() - wall_y.min()))
        area = abs(float(area)) if np.isfinite(area) and area != 0 else 1.0

        scene_name = os.path.basename(hdf5_path).split("_")[0]

        albedo = None
        depth = None
        depth_metric_scale = False

        _, albedo_ds = _find_first(datasets, ("albedo", "reflectance"), ndim=2)
        if albedo_ds is not None:
            albedo = _read_numeric_dataset(albedo_ds)

        _, depth_ds = _find_first(datasets, ("depth",), ndim=2)
        if depth_ds is not None:
            depth = _read_numeric_dataset(depth_ds)
            depth_metric_scale = True

        if albedo is None or depth is None:
            _, voxel_ds = _find_first(datasets, ("voxel", "volume", "groundtruth", "gt"), ndim=3)
            if voxel_ds is not None:
                origin = None
                size = None
                _, origin_ds = _find_first(
                    datasets,
                    ("hiddenVolumePosition", "volumePosition", "volumeOrigin", "origin"),
                )
                if origin_ds is not None:
                    origin = np.asarray(origin_ds[()]).reshape(-1)
                _, size_ds = _find_first(
                    datasets,
                    ("hiddenVolumeSize", "volumeSize", "volumeExtent", "extent"),
                )
                if size_ds is not None:
                    size = np.asarray(size_ds[()]).reshape(-1)

                voxel_albedo, voxel_depth, voxel_depth_metric_scale = _derive_surface_maps(
                    voxel_ds[()], origin=origin, size=size
                )
                if albedo is None:
                    albedo = voxel_albedo
                if depth is None:
                    depth = voxel_depth
                    depth_metric_scale = voxel_depth_metric_scale

    has_albedo_gt = albedo is not None
    has_depth_gt = depth is not None

    if albedo is None:
        albedo = np.ones(tau.shape[:2], dtype=np.float64)
        print("  Warning: no albedo GT found in HDF5; using placeholder")
    if depth is None:
        depth = np.ones(tau.shape[:2], dtype=np.float64)
        print("  Warning: no depth GT found in HDF5; using placeholder")

    print(f"  measurement path: {measurement_path}")
    print(f"  tau normalized shape: {tau.shape}")
    print(f"  tau range: [{tau.min():.6f}, {tau.max():.6f}]")
    print(
        "  gt status: "
        f"albedo={'yes' if has_albedo_gt else 'no'}, "
        f"depth={'yes' if has_depth_gt else 'no'}, "
        f"metric_depth_scale={'yes' if depth_metric_scale else 'no'}"
    )

    return {
        "tau": tau,
        "albedo": np.asarray(albedo, dtype=np.float64),
        "depth": np.asarray(depth, dtype=np.float64),
        "has_albedo_gt": has_albedo_gt,
        "has_depth_gt": has_depth_gt,
        "depth_metric_scale": depth_metric_scale,
        "dt": float(dt),
        "k": int(k),
        "area": float(area),
        "scene_name": scene_name,
        "wall_x": wall_x,
        "wall_y": wall_y,
    }


def convert_zaragoza_to_npz(hdf5_path, output_dir=None):
    """Convert Zaragoza HDF5 to NPZ format."""
    data = load_zaragoza_hdf5(hdf5_path)

    if output_dir is None:
        output_dir = os.path.dirname(hdf5_path)
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(hdf5_path))[0]
    out_path = os.path.join(output_dir, f"{base}.npz")
    np.savez_compressed(out_path, **data)
    print(f"  Saved to {out_path}")

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("hdf5_path", help="Path to Zaragoza HDF5 file")
    parser.add_argument("--output", help="Output directory")
    args = parser.parse_args()
    convert_zaragoza_to_npz(args.hdf5_path, args.output)
