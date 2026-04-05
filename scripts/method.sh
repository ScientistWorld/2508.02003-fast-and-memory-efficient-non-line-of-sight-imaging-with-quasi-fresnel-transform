#!/bin/bash
# Quasi-Fresnel Transform method main script
set -e

cd /home/user

# Generate synthetic NLOS data (using method from the paper)
python data/generate_nlos_data.py \
    --scene kylin \
    --resolution 64 \
    --bins 128 \
    --area 1.0 \
    --dt 0.003 \
    --k 4 \
    --save

# Run reconstruction
python -c "
import numpy as np
from method.quasi_fresnel import quasi_fresnel_reconstruct, benchmark_reconstruction
import json, os

# Load data
data = np.load('data/kylin/kylin_64x64.npz')
tau = data['tau']
albedo_gt = data['albedo']
depth_gt = data['depth']
dt = data['dt']
k = data['k']

# Parameters from the paper
s = 0.025

# Run reconstruction
result = benchmark_reconstruction(tau, s, dt, k)

# Compute metrics
from eval.metrics import compute_metrics
metrics = compute_metrics(result['albedo'], result['depth'], albedo_gt, depth_gt)

print(f'Runtime: {result[\"timing\"][\"total\"]:.4f}s')
print(f'Memory: {result[\"memory_mb\"]:.2f}MB')
print(f'Albedo PSNR: {metrics[\"psnr\"]:.2f}dB')
print(f'Albedo MAE: {metrics[\"albedo_mae\"]:.4f}')
print(f'Depth MAE: {metrics[\"depth_mae\"]:.4f}m')

# Save results
os.makedirs('scoring', exist_ok=True)
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
            }
        }
    }
}
with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)
print('Results saved to scoring/scores.json')
"
