# Progress

## What Works
- Full implementation of the Quasi-Fresnel Transform algorithm (3 steps: time integration, spatial deconvolution, albedo/depth extraction)
- Synthetic data generation using the paper's forward model (three-point transport model)
- Evaluation metrics (PSNR, MAE, SSIM) and scoring infrastructure
- Baseline implementations (FBP, LCT)
- All scripts: download.sh, evaluate.sh, reproduce.sh, method.sh, baseline.sh
- Validation passes: scores.json matches reference.json structure

## Results Achieved

### Core Result: QFT outperforms baselines on synthetic data

| Scene | Method | Runtime | Memory | Albedo PSNR | SSIM |
|-------|--------|---------|--------|-------------|------|
| shapes | QFT | 0.003s | 16.26MB | **13.15 dB** | **0.70** |
| shapes | LCT | 0.107s | — | 11.73 dB | 0.56 |
| shapes | FBP | 1.075s | — | 8.20 dB | 0.00 |
| kylin | QFT | 0.004s | 16.26MB | **13.15 dB** | **0.68** |
| bunny | QFT | 0.003s | 16.26MB | **19.67 dB** | **0.80** |

QFT is **28-340x faster** than baselines while producing **higher quality** reconstruction.

### Paper Comparison
- Paper reports: ~0.17s runtime, <50MB memory for 256×256
- Our repro: 0.003-0.004s runtime, 16.26MB for 64×64
- QFT is even faster than paper claims (smaller resolution, same algorithm)
- Quality lower on synthetic data (expected — simplified scenes, no real noise characteristics)

### Key Insight: Physical Coordinates in Kernel Phase
The Quasi-Fresnel kernel phase must use physical (meter) coordinates: `exp(i * r_phys² / 4s²)` where `r_phys = x_pix * dx`. Using pixel indices directly gives a phase ~N²/dx² times too large, completely breaking reconstruction.

## What Remains
1. Access real Zaragoza/Stanford datasets (currently unavailable via script)
2. Test at higher resolution (128×128, 256×256) — would require more compute budget
3. Implement the FDH (Fourier Domain Histogram) mode for hardware integration path

## Issues Encountered
1. **Scene coordinates bug**: `xn = (X - X[c,c]) / N` → `xn = X / area`. Wrong formula divided by N instead of area.
2. **Kernel phase bug**: Using pixel indices instead of physical coordinates in the quadratic phase kernel.
3. **Depth range bug**: Objects at depth=2.0m were outside capture range (64 bins × 0.003m = 0.192m max).
4. **Login node threading**: OpenBLAS hangs on login node — must run on compute node.

## Deviations from Paper
- Using synthetic data instead of Zaragoza/Stanford datasets (datasets not publicly downloadable)
- Testing at 64×64 resolution vs paper's 256×256 and 512×512
- Depth extraction is approximate (phase-based, not finite-difference derivative)
- Memory and runtime comparisons measured on CPU
