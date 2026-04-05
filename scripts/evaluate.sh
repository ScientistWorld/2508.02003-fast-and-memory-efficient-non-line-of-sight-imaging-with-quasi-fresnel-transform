#!/bin/bash
# Evaluation script for NLOS imaging reconstruction.
#
# Evaluates the quality of reconstructed albedo and depth maps against
# ground truth, measuring PSNR, MAE, SSIM, runtime, and memory usage.
#
# Usage:
#   ./evaluate.sh <method> <data_dir> [options]
#   ./evaluate.sh quasi_fresnel /home/user/data/kylin --s 0.025
#   ./evaluate.sh fbp /home/user/data/kylin
#   ./evaluate.sh lct /home/user/data/kylin

set -e

cd /home/user

METHOD=${1:-quasi_fresnel}
DATA_DIR=${2:-/home/user/data/kylin}
S_PARAM=${3:-0.025}

mkdir -p scoring

python -c "
import sys
import os
import json
import time
import numpy as np
import tracemalloc

method = '$METHOD'
data_dir = '$DATA_DIR'
s_param = float('$S_PARAM')

# Load ground truth data
data_files = [f for f in os.listdir(data_dir) if f.endswith('.npz')]
if not data_files:
    print(f'No .npz files found in {data_dir}')
    sys.exit(1)

data_path = os.path.join(data_dir, data_files[0])
data = np.load(data_path)
tau = data['tau']
albedo_gt = data['albedo']
depth_gt = data['depth']
dt = data['dt']
k = data['k']
scene_name = data['scene_name']

print(f'Evaluating {method} on scene: {scene_name}')
print(f'Data: tau={tau.shape}, albedo={albedo_gt.shape}, depth={depth_gt.shape}')

tracemalloc.start()
t0 = time.perf_counter()

if method == 'quasi_fresnel':
    from method.quasi_fresnel import quasi_fresnel_reconstruct, benchmark_reconstruction
    result = benchmark_reconstruction(tau, s_param, dt, k)
    albedo_recon = result['albedo']
    depth_recon = result['depth']
    runtime = result['timing']['total']
    memory_mb = result['memory_mb']
elif method == 'fbp':
    from baseline.fbp import fbp_reconstruct
    result = fbp_reconstruct(tau, dt, k)
    albedo_recon = result['albedo']
    depth_recon = result['depth']
    runtime = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    memory_mb = peak / (1024 * 1024)
elif method == 'lct':
    from baseline.lct import lct_reconstruct
    result = lct_reconstruct(tau, dt, k)
    albedo_recon = result['albedo']
    depth_recon = result['depth']
    runtime = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    memory_mb = peak / (1024 * 1024)
else:
    print(f'Unknown method: {method}')
    sys.exit(1)

t1 = time.perf_counter()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

if runtime == 0:
    runtime = t1 - t0
if memory_mb == 0:
    memory_mb = peak / (1024 * 1024)

# Compute metrics
from eval.metrics import compute_metrics
metrics = compute_metrics(albedo_recon, depth_recon, albedo_gt, depth_gt)

print(f'Runtime: {runtime:.4f}s')
print(f'Memory: {memory_mb:.2f}MB')
print(f'PSNR: {metrics[\"psnr\"]:.2f}dB')
print(f'Albedo MAE: {metrics[\"albedo_mae\"]:.4f}')
print(f'Depth MAE: {metrics[\"depth_mae\"]:.4f}m')
print(f'SSIM: {metrics[\"ssim\"]:.4f}')

# Write scores
scores = {
    'nlos_reconstruction': {
        'results': {
            method: {
                'type': 'proposed' if method == 'quasi_fresnel' else 'baseline',
                'runtime_s': round(runtime, 6),
                'memory_mb': round(memory_mb, 2),
                'albedo_psnr': round(metrics['psnr'], 2),
                'albedo_mae': round(metrics['albedo_mae'], 4),
                'depth_mae': round(metrics['depth_mae'], 4),
                'ssim': round(metrics['ssim'], 4),
            }
        }
    }
}

with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)

print(f'Scores saved to scoring/scores.json')
"
