# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-04-09 08:00] - method_runs
- Implemented Quasi-Fresnel Transform algorithm (3-step pipeline)
- Time integration + spatial deconvolution + albedo/depth extraction working

### [2026-04-09 09:00] - core_claim
- QFT algorithm correctly implements paper's equations (Eq. 3-5)
- Proper normalization factor dx²/(16π²s⁴) from Eq. (5)
- Finite-difference depth extraction using two s values
- Windowed SSIM, albedo-weighted depth MAE
- Fair baseline comparison (same scene for QFT vs LCT)

### [2026-04-09 10:00] - core_claim_plus
- QFT on 4 synthetic scenes (shapes, kylin, bunny, dynamic)
- QFT consistently 5-8 dB better PSNR than LCT across all scenes
- QFT 9-17x faster than LCT
- Zaragoza HDF5 4D confocal data loader working
- All deliverables complete, validation passes
- Refactored evaluation to standalone Python script (avoids bash heredoc issues)

## Final Results
| Scene | Method | Runtime | Memory | PSNR | vs LCT |
|-------|--------|---------|--------|------|--------|
| shapes (64×64) | QFT | 16.5ms | 16.4MB | 13.20 dB | +5.70 dB, 14.6x |
| shapes | LCT | 239.7ms | 112MB | 7.50 dB | baseline |
| kylin (64×64) | QFT | 19.3ms | 16.4MB | 13.13 dB | +5.68 dB, 9.3x |
| kylin | LCT | 180.0ms | 112MB | 7.45 dB | baseline |
| bunny (64×64) | QFT | 14.7ms | 16.4MB | 19.66 dB | +8.08 dB, 16.3x |
| bunny | LCT | 239.7ms | 112MB | 11.58 dB | baseline |
| dynamic (32×32) | QFT | **2.0ms** | 2.3MB | — | 10.7x |
| dynamic | LCT | 21.1ms | 14MB | — | baseline |