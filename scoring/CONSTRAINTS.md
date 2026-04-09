# Scientist Constraints

## Model
The scientist must implement the Quasi-Fresnel Transform algorithm or a direct improvement thereof. The method must use the 2D representation approach (representing the hidden scene as albedo + depth maps rather than 3D volumes) and the Quasi-Fresnel kernel (quadratic phase factor). Replacing the QFT with a fundamentally different NLOS reconstruction method (FBP, LCT, FK migration, Phasor field, deep learning) as the primary approach is not allowed. The scientist may modify the QFT implementation (e.g., different numerical approximations, separable implementations, hardware-friendly versions) as long as the core 2D representation and Quasi-Fresnel kernel remain.

## Data
The scientist must use the provided synthetic NLOS datasets generated via the three-point transport model. These are:
- `data/shapes/shapes_64x64.npz` — synthetic geometric shapes scene
- `data/kylin/kylin_64x64.npz` — synthetic kylin (mythical creature) scene
- `data/bunny/bunny_64x64.npz` — synthetic bunny scene

All datasets use: 64×64 relay wall resolution, 256 time bins, 0.3m × 0.3m area, 0.003m/bin, k=4 (isotropic scattering). The test set is the hidden scene albedo and depth maps in each `.npz` file. No external NLOS datasets or real captured data should be used.

## Evaluation Protocol
Reconstruction quality must be evaluated using the provided `eval/metrics.py` (PSNR, MAE, SSIM) via `scripts/evaluate.sh`. Runtime must be measured using `time.perf_counter()` and memory via `tracemalloc`. All experiments must be reproducible via `scripts/reproduce.sh`.

## Compliance Checklist
- [ ] Method uses 2D representation (albedo + depth) of the hidden scene, not 3D volumetric reconstruction
- [ ] Reconstruction involves a quadratic-phase kernel approximating the Quasi-Fresnel transform
- [ ] Evaluation uses the provided `eval/metrics.py` and `scripts/evaluate.sh`
- [ ] All experiments use the provided synthetic NLOS datasets in `data/`
- [ ] No external NLOS datasets used
- [ ] Runtime and memory reported using standard Python timing tools
