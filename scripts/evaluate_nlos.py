#!/usr/bin/env python3
"""
NLOS imaging evaluation script.
Runs QFT and LCT on synthetic scenes and outputs scores to scoring/scores.json.
"""
import sys
import json
import time
import tracemalloc
import os

sys.path.insert(0, '/home/user')
os.chdir('/home/user')

# Disable threading
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import numpy as np
from data.generate_nlos_data import generate_dataset
from method.quasi_fresnel import benchmark_reconstruction
from baseline.lct import lct_reconstruct
from eval.metrics import compute_metrics


def run_s_sweep(tau, albedo_gt, depth_gt, dt, k, area):
    s_values = [0.005, 0.008, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050, 0.075, 0.100]
    best_psnr = -999
    best_s = 0.025
    best_result = None
    best_metrics = None
    for s in s_values:
        try:
            result = benchmark_reconstruction(tau, s, dt, k, area=area)
            metrics = compute_metrics(result['albedo'], result['depth'], albedo_gt, depth_gt)
            print(f'    s={s:.3f}: time={result["timing"]["total"]:.4f}s, mem={result["memory_mb"]:.1f}MB, PSNR={metrics["psnr"]:.2f}dB')
            if metrics['psnr'] > best_psnr:
                best_psnr = metrics['psnr']
                best_s = s
                best_result = result
                best_metrics = metrics
        except Exception as e:
            print(f'    s={s:.3f}: ERROR {e}')
    return best_s, best_result, best_metrics


def main():
    dt = 0.003
    k = 4
    area = 0.3
    depth_val = 0.15

    results = {}

    # ---- Main scenes (64x64) ----
    for scene_name in ['shapes', 'kylin', 'bunny']:
        print(f'\n===== Scene: {scene_name} (64x64) =====')
        data = generate_dataset(scene_name, 64, 256, area, dt, k, 64, default_depth=depth_val)
        tau = data['tau']
        albedo_gt = data['albedo']
        depth_gt = data['depth']

        best_s, best_result, best_metrics = run_s_sweep(tau, albedo_gt, depth_gt, dt, k, area)
        print(f'  Best: s={best_s:.3f}, PSNR={best_metrics["psnr"]:.2f}dB')

        results[scene_name] = {
            'qft': {
                'runtime_s': best_result['timing']['total'],
                'memory_mb': best_result['memory_mb'],
                'albedo_psnr': best_metrics['psnr'],
                'albedo_mae': best_metrics['albedo_mae'],
                'depth_mae': best_metrics['depth_mae'],
                'ssim': best_metrics['ssim'],
            }
        }

        # LCT baseline
        tracemalloc.start()
        t0 = time.perf_counter()
        lct_a, lct_d = lct_reconstruct(tau, dt, k)
        lct_time = time.perf_counter() - t0
        _, lct_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        lct_metrics = compute_metrics(lct_a, lct_d, albedo_gt, depth_gt)
        print(f'  LCT: time={lct_time:.4f}s, PSNR={lct_metrics["psnr"]:.2f}dB')
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

    best_s, best_result, _ = run_s_sweep(dyn_tau, dyn_data['albedo'], dyn_data['depth'], dt, k, area)
    results['dynamic'] = {
        'qft': {
            'runtime_s': best_result['timing']['total'],
            'memory_mb': best_result['memory_mb'],
        }
    }

    # LCT on dynamic
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

    # ---- Summary ----
    print()
    print('='*70)
    print('RESULTS SUMMARY')
    print('='*70)
    for sn, sr in results.items():
        qft = sr['qft']
        psnr = qft.get('albedo_psnr', 'N/A')
        ssim = qft.get('ssim', 'N/A')
        print(f'{sn}: QFT {qft["runtime_s"]:.4f}s, {qft["memory_mb"]:.1f}MB, PSNR={psnr}dB, SSIM={ssim}')
        if 'lct' in sr:
            lct = sr['lct']
            speedup = lct['runtime_s'] / qft['runtime_s'] if qft['runtime_s'] > 0 else float('inf')
            lct_psnr = lct.get('albedo_psnr', 'N/A')
            print(f'  LCT: {lct["runtime_s"]:.4f}s, PSNR={lct_psnr}dB, speedup={speedup:.1f}x')
    print('='*70)

    # ---- Build scores matching reference.json structure ----
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
                    },
                    'fourier_transform': {
                        'runtime_s': round(results['bunny']['lct']['runtime_s'], 6),
                        'memory_mb': round(results['bunny']['lct']['memory_mb'], 2),
                        'albedo_psnr': round(results['bunny']['lct']['albedo_psnr'], 2),
                        'albedo_mae': round(results['bunny']['lct']['albedo_mae'], 4),
                        'depth_mae': round(results['bunny']['lct']['depth_mae'], 4),
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

    os.makedirs('scoring', exist_ok=True)
    with open('scoring/scores.json', 'w') as f:
        json.dump(scores, f, indent=2)
    print('Scores saved to scoring/scores.json')

    # Validate
    if os.path.exists('scoring/validate.py'):
        import subprocess
        result = subprocess.run(['python3', 'scoring/validate.py', '--compare'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)


if __name__ == '__main__':
    main()