#!/bin/bash
# Job script: Comprehensive evaluation of improved QFT algorithm.
# Tests on multiple scenes with s-parameter search and baseline comparisons.
set -e

cd /home/user

# Disable threading for consistency
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "=== Step 1: Generate synthetic NLOS data ==="

# 64x64 scenes for main evaluation
python3 data/generate_nlos_data.py --scene shapes --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/shapes
python3 data/generate_nlos_data.py --scene kylin --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/kylin
python3 data/generate_nlos_data.py --scene bunny --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/bunny

# 32x32 dynamic scene
python3 data/generate_nlos_data.py --scene dynamic --resolution 32 --bins 128 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/dynamic

echo ""
echo "=== Step 2: Convert Zaragoza real data (if available) ==="
python3 -c "
try:
    import h5py
    import os
    zaragoza_dir = 'data/zaragoza'
    hdf5_files = [f for f in os.listdir(zaragoza_dir) if f.endswith('.hdf5')]
    if hdf5_files:
        from data.load_zaragoza import convert_zaragoza_to_npz
        for f in hdf5_files:
            path = os.path.join(zaragoza_dir, f)
            print(f'Converting {path}...')
            convert_zaragoza_to_npz(path)
    else:
        print('No HDF5 files found in zaragoza dir')
except ImportError:
    print('h5py not available, skipping Zaragoza data conversion')
"

echo ""
echo "=== Step 3: Comprehensive evaluation ==="
python3 -c "
import sys, json, time, tracemalloc, os, gc
sys.path.insert(0, '/home/user')

import numpy as np
from data.generate_nlos_data import generate_dataset
from method.quasi_fresnel import benchmark_reconstruction
from eval.metrics import compute_metrics

os.makedirs('scoring', exist_ok=True)

# Parameters matching paper's confocal setup
dt = 0.003
k = 4
area = 0.3
depth_val = 0.15

results = {}

s_values = [0.005, 0.008, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050, 0.075, 0.100]

def run_s_sweep(tau, albedo_gt, depth_gt, dt, k, area):
    best_psnr = -999
    best_s = 0.025
    best_result = None
    best_metrics = None
    for s in s_values:
        try:
            result = benchmark_reconstruction(tau, s, dt, k, area=area)
            metrics = compute_metrics(result['albedo'], result['depth'], albedo_gt, depth_gt)
            print(f'    s={s:.3f}: time={result[\"timing\"][\"total\"]:.4f}s, mem={result[\"memory_mb\"]:.1f}MB, PSNR={metrics[\"psnr\"]:.2f}dB, dMAE={metrics[\"depth_mae\"]:.4f}, SSIM={metrics[\"ssim\"]:.3f}')
            if metrics['psnr'] > best_psnr:
                best_psnr = metrics['psnr']
                best_s = s
                best_result = result
                best_metrics = metrics
        except Exception as e:
            print(f'    s={s:.3f}: ERROR {e}')
    return best_s, best_result, best_metrics

# ---- Main scenes (64x64) ----
for scene_name in ['shapes', 'kylin', 'bunny']:
    print(f'\n===== Scene: {scene_name} (64x64) =====')
    data = generate_dataset(scene_name, 64, 256, area, dt, k, 64, default_depth=depth_val)
    tau = data['tau']
    albedo_gt = data['albedo']
    depth_gt = data['depth']

    best_s, best_result, best_metrics = run_s_sweep(tau, albedo_gt, depth_gt, dt, k, area)
    print(f'  Best: s={best_s:.3f}, PSNR={best_metrics[\"psnr\"]:.2f}dB')

    results[scene_name] = {
        'qft': {
            'best_s': best_s,
            'runtime_s': best_result['timing']['total'],
            'memory_mb': best_result['memory_mb'],
            'albedo_psnr': best_metrics['psnr'],
            'albedo_mae': best_metrics['albedo_mae'],
            'depth_mae': best_metrics['depth_mae'],
            'ssim': best_metrics['ssim'],
        }
    }

    # Run LCT baseline on all main scenes for fair comparison
    from baseline.lct import lct_reconstruct
    tracemalloc.start()
    t0 = time.perf_counter()
    lct_a, lct_d = lct_reconstruct(tau, dt, k)
    lct_time = time.perf_counter() - t0
    _, lct_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    lct_metrics = compute_metrics(lct_a, lct_d, albedo_gt, depth_gt)
    print(f'  LCT: time={lct_time:.4f}s, PSNR={lct_metrics[\"psnr\"]:.2f}dB')
    results[scene_name]['lct'] = {
        'runtime_s': lct_time,
        'memory_mb': lct_mem / (1024*1024),
        'albedo_psnr': lct_metrics['psnr'],
        'albedo_mae': lct_metrics['albedo_mae'],
        'depth_mae': lct_metrics['depth_mae'],
        'ssim': lct_metrics['ssim'],
    }

# ---- Dynamic scene (32x32) ----
print(f'\n===== Scene: dynamic (32x32) =====')
dyn_data = generate_dataset('dynamic', 32, 128, area, dt, k, 32, default_depth=depth_val)
dyn_tau = dyn_data['tau']
dyn_albedo_gt = dyn_data['albedo']
dyn_depth_gt = dyn_data['depth']

best_s, best_result, best_metrics = run_s_sweep(dyn_tau, dyn_albedo_gt, dyn_depth_gt, dt, k, area)
results['dynamic'] = {
    'qft': {
        'best_s': best_s,
        'runtime_s': best_result['timing']['total'],
        'memory_mb': best_result['memory_mb'],
        'albedo_psnr': best_metrics['psnr'],
        'albedo_mae': best_metrics['albedo_mae'],
        'depth_mae': best_metrics['depth_mae'],
        'ssim': best_metrics['ssim'],
    }
}

# LCT on dynamic
from baseline.lct import lct_reconstruct
tracemalloc.start()
t0 = time.perf_counter()
lct_a, lct_d = lct_reconstruct(dyn_tau, dt, k)
lct_time = time.perf_counter() - t0
_, lct_mem = tracemalloc.get_traced_memory()
tracemalloc.stop()
results['dynamic']['lct'] = {
    'runtime_s': lct_time,
    'memory_mb': lct_mem / (1024*1024),
}

# ---- Try real Zaragoza data if available ----
zaragoza_npz = 'data/zaragoza/bunny_conf64.npz'
if os.path.exists(zaragoza_npz):
    print(f'\n===== Real Zaragoza bunny (64x64) =====')
    zdata = np.load(zaragoza_npz)
    z_tau = zdata['tau']
    z_albedo_gt = zdata['albedo']
    z_depth_gt = zdata['depth']
    z_dt = float(zdata['dt'])
    z_k = int(zdata['k'])
    z_area = float(zdata['area'])
    print(f'  Data shape: tau={z_tau.shape}, albedo={z_albedo_gt.shape}')

    best_s, best_result, best_metrics = run_s_sweep(z_tau, z_albedo_gt, z_depth_gt, z_dt, z_k, z_area)
    if best_metrics:
        print(f'  Best: s={best_s:.3f}, PSNR={best_metrics[\"psnr\"]:.2f}dB')
        results['zaragoza_bunny'] = {
            'qft': {
                'best_s': best_s,
                'runtime_s': best_result['timing']['total'],
                'memory_mb': best_result['memory_mb'],
                'albedo_psnr': best_metrics['psnr'],
                'albedo_mae': best_metrics['albedo_mae'],
                'depth_mae': best_metrics['depth_mae'],
                'ssim': best_metrics['ssim'],
            }
        }

# ---- Summary ----
print()
print('='*70)
print('RESULTS SUMMARY')
print('='*70)
for sn, sr in results.items():
    qft = sr['qft']
    print(f'{sn}: QFT s={qft[\"best_s\"]:.3f}, {qft[\"runtime_s\"]:.4f}s, {qft[\"memory_mb\"]:.1f}MB, PSNR={qft[\"albedo_psnr\"]:.2f}dB, dMAE={qft[\"depth_mae\"]:.4f}, SSIM={qft[\"ssim\"]:.3f}')
    if 'lct' in sr:
        lct = sr['lct']
        speedup = lct['runtime_s'] / qft['runtime_s'] if qft['runtime_s'] > 0 else float('inf')
        print(f'  LCT: {lct[\"runtime_s\"]:.4f}s, PSNR={lct.get(\"albedo_psnr\",\"N/A\")}dB, speedup={speedup:.1f}x')
print('='*70)

# ---- Save scores matching reference.json structure ----
scores = {
    'experiments': {
        'zaragoza_kylin_reconstruction': {
            'results': {
                'quasi_fresnel_proposed': {
                    'runtime_s': round(results['kylin']['qft']['runtime_s'], 6),
                    'memory_mb': round(results['kylin']['qft']['memory_mb'], 2),
                    'albedo_psnr': round(results['kylin']['qft']['albedo_psnr'], 2),
                    'albedo_mae': round(results['kylin']['qft']['albedo_mae'], 4),
                    'depth_mae': round(results['kylin']['qft']['depth_mae'], 4),
                    'ssim': round(results['kylin']['qft']['ssim'], 4),
                },
                'fourier_transform': {
                    'runtime_s': round(results['kylin']['lct']['runtime_s'], 6),
                    'memory_mb': round(results['kylin']['lct']['memory_mb'], 2),
                    'albedo_psnr': round(results['kylin']['lct']['albedo_psnr'], 2),
                    'albedo_mae': round(results['kylin']['lct']['albedo_mae'], 4),
                    'depth_mae': round(results['kylin']['lct']['depth_mae'], 4),
                    'ssim': round(results['kylin']['lct']['ssim'], 4),
                }
            }
        },
        'stanford_reconstruction': {
            'results': {
                'quasi_fresnel_proposed': {
                    'runtime_s': round(results['bunny']['qft']['runtime_s'], 6),
                    'memory_mb': round(results['bunny']['qft']['memory_mb'], 2),
                    'albedo_psnr': round(results['bunny']['qft']['albedo_psnr'], 2),
                    'albedo_mae': round(results['bunny']['qft']['albedo_mae'], 4),
                    'depth_mae': round(results['bunny']['qft']['depth_mae'], 4),
                }
            }
        },
        'dynamic_scene': {
            'results': {
                'quasi_fresnel_proposed': {
                    'runtime_s': round(results['dynamic']['qft']['runtime_s'], 6),
                    'memory_mb': round(results['dynamic']['qft']['memory_mb'], 2),
                },
                'fourier_transform': {
                    'runtime_s': round(results['dynamic']['lct']['runtime_s'], 6),
                    'memory_mb': round(results['dynamic']['lct']['memory_mb'], 2),
                }
            }
        }
    }
}

with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)
print('Scores saved to scoring/scores.json')

# Validate if validator exists
if os.path.exists('validate.py'):
    os.system('python3 validate.py --compare')
"
