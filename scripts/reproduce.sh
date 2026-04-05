#!/bin/bash
# End-to-end reproduction script.
# Runs the full pipeline: download data, generate synthetic data,
# run method and baselines, evaluate results.
set -e

cd /home/user

echo "=== Step 1: Download/Generate data ==="
bash scripts/download.sh

echo ""
echo "=== Step 2: Run Quasi-Fresnel Transform method ==="
echo "Testing synthetic kylin scene at 64x64 resolution..."
python -c "
import numpy as np
from method.quasi_fresnel import quasi_fresnel_reconstruct, benchmark_reconstruction
import json, os, time, tracemalloc

# Test on kylin scene
data = np.load('data/kylin/kylin_64x64.npz')
tau = data['tau']
albedo_gt = data['albedo']
depth_gt = data['depth']
dt = data['dt']
k = data['k']
s = 0.025

print(f'Testing Quasi-Fresnel Transform...')
print(f'Data: {tau.shape}, s={s}, k={k}')

# Benchmark reconstruction
result = benchmark_reconstruction(tau, s, dt, k)

from eval.metrics import compute_metrics
metrics = compute_metrics(result['albedo'], result['depth'], albedo_gt, depth_gt)

print(f'')
print(f'Results:')
print(f'  Runtime: {result[\"timing\"][\"total\"]:.4f}s')
print(f'  Memory: {result[\"memory_mb\"]:.2f}MB')
print(f'  PSNR: {metrics[\"psnr\"]:.2f}dB')
print(f'  Albedo MAE: {metrics[\"albedo_mae\"]:.4f}')
print(f'  Depth MAE: {metrics[\"depth_mae\"]:.4f}m')

# Save scores
scores = {
    'nlos_reconstruction': {
        'results': {
            'quasi_fresnel': {
                'type': 'proposed',
                'runtime_s': round(result['timing']['total'], 6),
                'memory_mb': round(result['memory_mb'], 2),
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
"

echo ""
echo "=== Step 3: Run baseline methods ==="
bash scripts/evaluate.sh fbp /home/user/data/kylin
bash scripts/evaluate.sh lct /home/user/data/kylin

echo ""
echo "=== Step 4: Final evaluation ==="
bash scripts/evaluate.sh quasi_fresnel /home/user/data/kylin 0.025

echo ""
echo "=== Reproduction complete ==="
echo "Results saved to scoring/scores.json"
