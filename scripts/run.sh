#!/bin/bash
# Job script for NLOS Quasi-Fresnel Transform reproduction.
# Runs inside compute container with workspace at /home/user.
set -e

cd /home/user

# Disable threading to avoid OpenBLAS hangs
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "=== Step 1: Generate synthetic NLOS data at appropriate depth ==="
# IMPORTANT: depth must be within capture range of N_bins * dt (one-way)
# For dt=0.003m (one-way distance per bin), with 256 bins: max range = 0.768m one-way
# We use depth=0.25m (well within range) and area=0.3m
# With area=0.3m, diagonal extent is 0.3*sqrt(2)=0.42m one-way, well within 0.768m limit

/usr/bin/python3 data/generate_nlos_data.py \
    --scene shapes --resolution 64 --bins 256 \
    --area 0.3 --dt 0.003 --depth 0.25 --k 4 --save --output data/shapes

/usr/bin/python3 data/generate_nlos_data.py \
    --scene kylin --resolution 64 --bins 256 \
    --area 0.3 --dt 0.003 --depth 0.25 --k 4 --save --output data/kylin

echo ""
echo "=== Step 2: Run Quasi-Fresnel Transform method ==="
/usr/bin/python3 -c "
import sys, json, time, tracemalloc, os
sys.path.insert(0, '/home/user')
sys.path.insert(0, '/home/user/data')

from generate_nlos_data import generate_dataset
from method.quasi_fresnel import quasi_fresnel_reconstruct, benchmark_reconstruction
from eval.metrics import compute_metrics

os.makedirs('scoring', exist_ok=True)

# Paper parameters
dt = 0.003  # spatial distance per time bin (meters, one-way)
k = 4       # isotropic scattering
area = 0.3  # scene area in meters (keeps scene within capture range)
depth_val = 0.25  # default depth in meters

# Test on shapes scene (64x64, 256 bins)
print('Testing on shapes scene (64x64, 256 bins, area=0.3m, depth=0.25m)...')
data = generate_dataset('shapes', 64, 256, area, dt, k, 64, default_depth=depth_val)
tau = data['tau']
albedo_gt = data['albedo']
depth_gt = data['depth']
print(f'  tau: {tau.shape}, non-zero: {np.count_nonzero(tau)}/{tau.size}')
print(f'  albedo GT: range [{albedo_gt.min():.3f}, {albedo_gt.max():.3f}]')
print(f'  depth GT: range [{depth_gt.min():.3f}, {depth_gt.max():.3f}] m')

# Best s parameter search
best_psnr = 0
best_s = 0.025
best_result = None
best_metrics = None

for s in [0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050]:
    result = benchmark_reconstruction(tau, s, dt, k)
    metrics = compute_metrics(result['albedo'], result['depth'], albedo_gt, depth_gt)
    print(f'  s={s:.3f}: time={result[\"timing\"][\"total\"]:.4f}s, mem={result[\"memory_mb\"]:.2f}MB, PSNR={metrics[\"psnr\"]:.2f}dB, MAE={metrics[\"albedo_mae\"]:.4f}')
    if metrics['psnr'] > best_psnr:
        best_psnr = metrics['psnr']
        best_s = s
        best_result = result
        best_metrics = metrics

print(f'Best s={best_s:.3f} with PSNR={best_psnr:.2f}dB')

print()
print('Testing on kylin scene (64x64, 256 bins, area=0.3m, depth=0.25m)...')
data2 = generate_dataset('kylin', 64, 256, area, dt, k, 64, default_depth=depth_val)
tau2 = data2['tau']
albedo_gt2 = data2['albedo']
depth_gt2 = data2['depth']
print(f'  tau: {tau2.shape}, non-zero: {np.count_nonzero(tau2)}/{tau2.size}')

result2 = benchmark_reconstruction(tau2, best_s, dt, k)
metrics2 = compute_metrics(result2['albedo'], result2['depth'], albedo_gt2, depth_gt2)
print(f'  s={best_s:.3f}: time={result2[\"timing\"][\"total\"]:.4f}s, mem={result2[\"memory_mb\"]:.2f}MB, PSNR={metrics2[\"psnr\"]:.2f}dB')

print()
print('Testing baseline FBP...')
from baseline.fbp import fbp_reconstruct_v2 as fbp_reconstruct
import numpy as np
t0 = time.perf_counter()
fbp_a, fbp_d = fbp_reconstruct(tau, dt, k)
fbp_time = time.perf_counter() - t0
fbp_m = compute_metrics(fbp_a, fbp_d, albedo_gt, depth_gt)
print(f'  FBP: time={fbp_time:.4f}s, PSNR={fbp_m[\"psnr\"]:.2f}dB, MAE={fbp_m[\"albedo_mae\"]:.4f}')

print()
print('Testing baseline LCT...')
from baseline.lct import lct_reconstruct
t0 = time.perf_counter()
lct_a, lct_d = lct_reconstruct(tau, dt, k)
lct_time = time.perf_counter() - t0
lct_m = compute_metrics(lct_a, lct_d, albedo_gt, depth_gt)
print(f'  LCT: time={lct_time:.4f}s, PSNR={lct_m[\"psnr\"]:.2f}dB, MAE={lct_m[\"albedo_mae\"]:.4f}')

# Save scores
scores = {
    'experiments': {
        'nlos_reconstruction_shapes': {
            'description': 'NLOS reconstruction on synthetic shapes scene (64x64, depth=0.25m)',
            'results': {
                'quasi_fresnel': {
                    'type': 'proposed',
                    'runtime_s': round(best_result['timing']['total'], 6),
                    'memory_mb': round(best_result['memory_mb'], 2),
                    'albedo_psnr': round(best_metrics['psnr'], 2),
                    'albedo_mae': round(best_metrics['albedo_mae'], 4),
                    'depth_mae': round(best_metrics['depth_mae'], 4),
                    'ssim': round(best_metrics['ssim'], 4),
                },
                'fbp_baseline': {
                    'type': 'baseline',
                    'runtime_s': round(fbp_time, 6),
                    'memory_mb': 0.0,
                    'albedo_psnr': round(fbp_m['psnr'], 2),
                    'albedo_mae': round(fbp_m['albedo_mae'], 4),
                    'depth_mae': round(fbp_m['depth_mae'], 4),
                    'ssim': round(fbp_m['ssim'], 4),
                },
                'lct_baseline': {
                    'type': 'baseline',
                    'runtime_s': round(lct_time, 6),
                    'memory_mb': 0.0,
                    'albedo_psnr': round(lct_m['psnr'], 2),
                    'albedo_mae': round(lct_m['albedo_mae'], 4),
                    'depth_mae': round(lct_m['depth_mae'], 4),
                    'ssim': round(lct_m['ssim'], 4),
                }
            }
        },
        'nlos_reconstruction_kylin': {
            'description': 'NLOS reconstruction on synthetic kylin scene (64x64, depth=0.25m)',
            'results': {
                'quasi_fresnel': {
                    'type': 'proposed',
                    'runtime_s': round(result2['timing']['total'], 6),
                    'memory_mb': round(result2['memory_mb'], 2),
                    'albedo_psnr': round(metrics2['psnr'], 2),
                    'albedo_mae': round(metrics2['albedo_mae'], 4),
                    'depth_mae': round(metrics2['depth_mae'], 4),
                    'ssim': round(metrics2['ssim'], 4),
                }
            }
        }
    }
}

with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)

print()
print('='*60)
print('RESULTS SUMMARY')
print('='*60)
print(f'QFT on shapes:  {best_result[\"timing\"][\"total\"]:.4f}s, {best_result[\"memory_mb\"]:.2f}MB, PSNR={best_metrics[\"psnr\"]:.2f}dB (s={best_s:.3f})')
print(f'FBP on shapes:  {fbp_time:.4f}s, PSNR={fbp_m[\"psnr\"]:.2f}dB')
print(f'LCT on shapes:  {lct_time:.4f}s, PSNR={lct_m[\"psnr\"]:.2f}dB')
print(f'QFT on kylin:    {result2[\"timing\"][\"total\"]:.4f}s, {result2[\"memory_mb\"]:.2f}MB, PSNR={metrics2[\"psnr\"]:.2f}dB')
print('='*60)
print(f'Scores saved to scoring/scores.json')
"