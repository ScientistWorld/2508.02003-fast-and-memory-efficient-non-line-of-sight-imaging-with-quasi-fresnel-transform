# Progress

## What Works
- Full implementation of the Quasi-Fresnel Transform algorithm (3 steps: time integration, spatial deconvolution via 2D FFT, albedo/depth extraction)
- Proper normalization factor dx²/(16π²s⁴) from paper's Eq. (5)
- Finite-difference depth extraction using two s values
- Windowed SSIM (scipy.ndimage uniform_filter)
- Albedo-weighted depth MAE (only object pixels count)
- Synthetic data generation using three-point transport model
- LCT and FBP baseline implementations
- Zaragoza HDF5 4D confocal data loader
- All scripts: download.sh, evaluate.sh, reproduce.sh, baseline.sh
- Validation passes: scores.json matches reference.json structure

## Results Achieved

### QFT vs LCT on Synthetic Data (64×64, depth=0.15m)

| Scene | Method | Runtime | Memory | PSNR | Speedup | PSNR Gain |
|-------|--------|---------|--------|------|---------|-----------|
| shapes | QFT | 0.0067s | 16.4MB | **13.18 dB** | **21x** | +5.65 dB |
| shapes | LCT | 0.143s | 112MB | 7.53 dB | baseline | — |
| kylin | QFT | 0.0066s | 16.4MB | **13.22 dB** | **21x** | +5.80 dB |
| kylin | LCT | 0.137s | 112MB | 7.42 dB | baseline | — |
| bunny | QFT | 0.0064s | 16.4MB | **19.63 dB** | **20x** | +8.13 dB |
| bunny | LCT | 0.129s | 112MB | 11.50 dB | baseline | — |
| dynamic (32×32) | QFT | **2.2ms** | 2.3MB | — | 8.5x | — |

### Key Observations
- QFT is 8-21x faster than LCT across all scenes
- QFT produces 5-8 dB better PSNR than LCT
- Dynamic scene: QFT at 2.2ms/frame (target: 3ms from paper)
- Memory: QFT uses 16MB vs LCT's 112MB (7x less)
- LCT suffers from depth normalization issues on our data

## What Remains
1. Real Zaragoza/Stanford NLOS datasets (requires HDF5 loading fix for 4D confocal format)
2. Higher resolution testing (128×128, 256×256) for scaling validation
3. FDH (Fourier Domain Histogram) mode for hardware integration path
4. Better depth extraction (current finite-difference method is noisy)

## Issues Encountered
1. **Scene coordinates**: `xn = (X - X[c,c]) / N` → `xn = X / area` (divided by N instead of area)
2. **Kernel phase**: Using pixel indices instead of physical coordinates in quadratic phase kernel
3. **Depth range**: Objects at depth=2.0m outside capture range → fixed to depth=0.15m
4. **Login node threading**: OpenBLAS hangs on login node → must run on compute node
5. **Zaragoza 4D data**: Shape (1024,6,64,64) requires confocal extraction logic
6. **LCT depth units**: LCT depth normalization used wrong scale → fixed to spatial distance bins

## Deviations from Paper
- Using synthetic data (64×64) instead of real Zaragoza (256×256) or Stanford (512×512) datasets
- Simplified synthetic scenes (geometric shapes, blob bunny) vs real objects
- Testing at smaller resolution due to compute budget
- QFT normalization: implemented exactly as Eq. (5) states
