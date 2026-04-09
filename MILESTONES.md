# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-04-09 08:00] - method_runs
- Implemented Quasi-Fresnel Transform algorithm (3-step pipeline)
- Time integration + spatial deconvolution + albedo/depth extraction working
- Basic evaluation on synthetic data

### [2026-04-09 09:00] - core_claim
- QFT algorithm correctly implements paper's equations (Eq. 3-5)
- Proper normalization factor dx²/(16π²s⁴) from Eq. (5)
- Finite-difference depth extraction using two s values
- Windowed SSIM (scipy.ndimage uniform_filter)
- Albedo-weighted depth MAE masking
- Proper dynamic scene generation (32x32)
- Fair baseline comparison (same scene for QFT vs LCT)
- Filled EXPERIMENTS.md with proper descriptions
- Results: QFT 19x faster than LCT on kylin with higher PSNR (13.22 vs 11.85 dB)
