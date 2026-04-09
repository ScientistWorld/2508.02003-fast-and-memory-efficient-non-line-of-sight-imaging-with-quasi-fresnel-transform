# Progress

## What Works
- Full implementation of the Quasi-Fresnel Transform algorithm (3 steps: time integration, spatial deconvolution via 2D FFT, albedo/depth extraction)
- Proper normalization factor dx²/(16π²s⁴) from paper's Eq. (5)
- Finite-difference depth extraction using two s values
- Windowed SSIM (scipy.ndimage uniform_filter)
- Albedo-weighted depth MAE (only object pixels count)
- Synthetic data generation using three-point transport model
- LCT baseline implementation
- Zaragoza HDF5 4D confocal data loader
- Standalone evaluation script (scripts/evaluate_nlos.py)
- All scripts: download.sh, evaluate.sh, reproduce.sh, baseline.sh
- Validation passes: scores.json matches reference.json structure

## Results Achieved

### QFT vs LCT on Synthetic Data (64×64, depth=0.15m)

| Scene | Method | Runtime | Memory | PSNR | Speedup | PSNR Gain |
|-------|--------|---------|--------|------|---------|-----------|
| shapes | QFT | 16.5ms | 16.4MB | **13.20 dB** | **14.6x** | +5.70 dB |
| shapes | LCT | 239.7ms | 112MB | 7.50 dB | baseline | — |
| kylin | QFT | 19.3ms | 16.4MB | **13.13 dB** | **9.3x** | +5.68 dB |
| kylin | LCT | 180.0ms | 112MB | 7.45 dB | baseline | — |
| bunny | QFT | 14.7ms | 16.4MB | **19.66 dB** | **16.3x** | +8.08 dB |
| bunny | LCT | 239.7ms | 112MB | 11.58 dB | baseline | — |
| dynamic (32×32) | QFT | **2.0ms** | 2.3MB | — | 10.7x | — |
| dynamic | LCT | 21.1ms | 14MB | — | baseline | — |

### Key Observations
- QFT is 9-16x faster than LCT across all scenes
- QFT produces 5-8 dB better PSNR than LCT on all scenes
- Dynamic scene: QFT at 2.0ms/frame (paper target: 3ms)
- Memory: QFT uses 16MB vs LCT's 112MB (7x less)
- Optimal s parameter varies by scene: 0.025-0.075

## What Remains
1. Real Zaragoza/Stanford NLOS datasets (ground truth mismatch — GT albedo 1024×1024 vs tau 32×32)
2. Higher resolution testing (128×128, 256×256) for scaling validation
3. FDH (Fourier Domain Histogram) mode for hardware integration path

## Issues Encountered
1. **Scene coordinates**: `xn = (X - X[c,c]) / N` → `xn = X / area` (divided by N instead of area)
2. **Kernel phase**: Using pixel indices instead of physical coordinates in quadratic phase kernel
3. **Depth range**: Objects at depth=2.0m outside capture range → fixed to depth=0.15m
4. **Login node threading**: OpenBLAS hangs on login node → must run on compute node
5. **Zaragoza 4D data**: Shape (1024,6,64,64) requires confocal extraction logic
6. **Bash heredoc escaping**: Python code inside bash heredocs had quote escaping issues → refactored to standalone script
7. **LCT depth units**: LCT depth normalization used wrong scale → fixed to spatial distance bins

## Deviations from Paper
- Using synthetic data (64×64) instead of real Zaragoza (256×256) or Stanford (512×512) datasets
- Simplified synthetic scenes (geometric shapes, Gaussian blob bunny) vs real objects
- Testing at smaller resolution due to compute budget