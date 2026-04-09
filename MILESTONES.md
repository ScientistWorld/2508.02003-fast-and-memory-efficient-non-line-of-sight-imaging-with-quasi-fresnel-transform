# Reproduction Milestones

**Current: core_claim_plus**

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

### [2026-04-09 10:00] - core_claim_plus
- QFT on 3 synthetic scenes (shapes, kylin, bunny) + dynamic
- QFT 8-21x faster than LCT with 5-8 dB better PSNR
- Results: shapes 13.18 vs 7.53 dB, kylin 13.22 vs 7.42 dB, bunny 19.63 vs 11.50 dB
- Dynamic: 2.2ms/frame (under paper's 3ms target)
- Zaragoza HDF5 4D confocal data loader
- All deliverables complete (briefing, scoring, scripts, env)
- scores.json validated against reference.json
