# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-04-05] - none
- Read the paper thoroughly. Paper proposes a Quasi-Fresnel Transform for efficient NLOS imaging.
- Key idea: exploit 2D nature of hidden scenes (albedo + depth maps) instead of 3D volumes
- Complexity reduction from O(N³) to O(N² log N) for FDH mode
- Reported: ~0.17s runtime, <50MB memory for 256×256 reconstruction

### [2026-04-05] - method_runs
- Filled in all briefing files (problem.md, evaluation.md, method.md, overview.md)
- Set up environment (container.def, setup.sh) with numpy, scipy, Pillow, numba
- Created synthetic data generation using the paper's forward model
- Implemented Quasi-Fresnel Transform method (time integration, spatial deconvolution, albedo/depth extraction)
- Implemented baseline methods: FBP and LCT
- Created evaluation infrastructure
- Wrote scoring/reference.json with paper-reported benchmarks

### [2026-04-08] - core_claim
- Fixed critical bugs: scene coordinates (xn=X/area) and kernel phase (physical dx² factor)
- Results: QFT=13.17dB PSNR vs LCT=11.72dB vs FBP=8.20dB on 64×64 synthetic shapes
- QFT: 0.025s, 16.26MB. Algorithm works correctly, outperforms baselines in speed and quality

### [2026-04-09] - core_claim_plus
- Comprehensive evaluation across 3 scenes (shapes, kylin, bunny) at 64×64
- Full s-parameter search (11 values tested per scene)
- QFT: 0.003-0.004s runtime, 16.26MB memory, 13-20 dB PSNR depending on scene
- LCT baseline: 0.1s, 11.73 dB PSNR
- FBP baseline: 1.07s, 8.20 dB PSNR
- QFT is 28-340x faster than baselines while achieving higher reconstruction quality
- Validation passes: scores.json matches reference.json structure
- Wrote TARGETS.md, CONSTRAINTS.md, DIRECTION.md for scientist agents
