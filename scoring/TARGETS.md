# Evaluation Targets

This file defines what a scientist should optimize when improving on this paper's results.

## Primary: reconstruction_quality
Reconstruct hidden NLOS scenes with high fidelity albedo and depth maps from time-resolved SPAD measurements.
- **Metric**: albedo_psnr (higher is better)
- **Also tracked**: albedo_mae (lower is better), ssim (higher is better), depth_mae (lower is better)

## Constraint: computational_efficiency
The paper's core contribution is dramatic runtime and memory reduction. A scientist must maintain or improve efficiency.
- **Metric**: runtime_s (lower is better) — reconstruction time per frame
- **Metric**: memory_mb (lower is better) — peak memory during reconstruction
- The paper reports ~0.17s runtime and <50MB memory for 256×256 reconstruction

## Ablation: vs_volumetric_baselines
Removing the QFT's 2D approach and using traditional 3D volumetric methods (FBP, LCT) should produce worse efficiency.
- **Metric**: albedo_psnr gap (QFT should match or beat baselines)
- **Metric**: runtime_s ratio (QFT should be 10x+ faster than baselines)
