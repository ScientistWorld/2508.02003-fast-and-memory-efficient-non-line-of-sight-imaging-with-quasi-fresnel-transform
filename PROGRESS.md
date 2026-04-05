# Progress

## What Works
- Full implementation of the Quasi-Fresnel Transform algorithm (3 steps: time integration, spatial deconvolution, albedo/depth extraction)
- Synthetic data generation using the paper's forward model (three-point transport model)
- Evaluation metrics (PSNR, MAE, SSIM) and scoring infrastructure
- Baseline implementations (FBP, LCT)
- All scripts: download.sh, evaluate.sh, reproduce.sh, method.sh, baseline.sh

## Results
- Paper reports: ~0.17s runtime, <50MB memory, good reconstruction quality
- Need to run experiments on compute node to validate (login node has threading issues)

## Remaining
1. Run GPU job to validate the method works end-to-end
2. Test on synthetic scenes (shapes, kylin, bunny, usaf)
3. Compare against baselines (FBP, LCT)
4. Verify runtime and memory efficiency claims
5. Test at higher resolution (64x64, 128x128)
6. Fill in scoring/scores.json with actual results
7. Write TARGETS.md, CONSTRAINTS.md, DIRECTION.md

## Issues
- Login node has OpenBLAS threading issues causing timeouts — must run on compute node
- Forward model generation at large resolutions can be slow on login node
- The depth extraction from phase may need calibration for accurate absolute depth values

## Deviations from Paper
- Using synthetic data instead of Zaragoza/Stanford datasets (datasets not publicly downloadable via script)
- Testing at smaller resolutions (32x32, 64x64) vs paper's 256x256 and 512x512 due to compute constraints
- The depth extraction is approximate (from phase only, without finite-difference derivative)
- Memory and runtime comparisons will be measured on CPU, matching the paper's methodology
