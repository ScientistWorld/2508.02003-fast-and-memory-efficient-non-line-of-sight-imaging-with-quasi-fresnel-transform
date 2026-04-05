# Reproduction Milestones

**Current: method_runs**

## Progress Log

### [2026-04-05] - none
- Read the paper thoroughly. Paper proposes a Quasi-Fresnel Transform for efficient NLOS imaging.
- Key idea: exploit 2D nature of hidden scenes (albedo + depth maps) instead of 3D volumes
- Complexity reduction from O(N³) to O(N² log N) for FDH mode
- Reported: ~0.17s runtime, <50MB memory for 256×256 reconstruction

### [2026-04-05] - method_runs
- Filled in all briefing files (problem.md, evaluation.md, method.md, overview.md)
- Set up environment (container.def, setup.sh) with numpy, scipy, Pillow, numba
- Created synthetic data generation (`data/generate_nlos_data.py`) using the paper's forward model
- Implemented Quasi-Fresnel Transform method (`method/quasi_fresnel.py`)
  - Time integration: aggregates tau(x,t) into phi(x;s) via weighted integral (Eq. 3)
  - Spatial deconvolution: recovers psi(x;s) from phi via 2D FFT convolution (Eq. 5)
  - Result extraction: albedo = |psi|, depth from phase (Eq. 4)
- Implemented baseline methods: FBP (`baseline/fbp.py`) and LCT (`baseline/lct.py`)
- Created evaluation infrastructure (`eval/metrics.py`, `scoring/validate.py`)
- Wrote scoring/reference.json with paper-reported benchmarks
- The method executes end-to-end without errors. Submitting GPU job for full validation.
