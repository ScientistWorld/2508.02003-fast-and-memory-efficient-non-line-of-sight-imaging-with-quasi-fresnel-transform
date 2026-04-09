# Research Direction

## Research Problem
Non-line-of-sight (NLOS) imaging reconstructs hidden objects from time-resolved SPAD measurements on a relay wall. The challenge is computational: existing methods represent the hidden scene as 3D volumetric data, leading to O(N³) complexity. This makes real-time, high-resolution NLOS imaging impractical on resource-constrained devices.

## Core Contribution
The paper introduces a 2D representation approach that exploits the inherent 2D nature of hidden scenes (albedo + depth maps) combined with the Quasi-Fresnel Transform — a quadratic-phase kernel that maps 3D volumetric albedo to 2D via an analytical formula. This reduces complexity to O(N² log N) and memory to O(N²). The scientist must work within this framework: improve reconstruction quality, efficiency, or robustness of 2D-representation-based NLOS imaging using quasi-Fresnel-type transforms.

## Approach Scope
The scientist may work on any aspect that improves 2D-representation NLOS reconstruction:
- **Better kernel design**: modifying the Quasi-Fresnel kernel (different parameterizations, adaptive s selection, learned kernels)
- **Improved deconvolution**: better solvers for the spatial deconvolution step (regularization, Wiener filter, learned priors)
- **Enhanced depth extraction**: more accurate depth from the complex phase field
- **Noise robustness**: handling noisy or sparse measurements better
- **Super-resolution**: reconstructing at higher resolution than the relay wall
- **Multi-depth handling**: improving reconstruction when objects exist at very different depths
- **Real-time optimization**: GPU implementations, hardware-friendly versions, parallelization

## Out of Bounds
- Replacing the 2D representation with a 3D volumetric approach (FBP, LCT, FK migration, Phasor field back-projection). These methods fundamentally contradict the paper's core insight about 2D representation.
- Using deep learning / neural network approaches as the primary reconstruction method (e.g., NLOT, NLST Transformer). The paper's contribution is analytical/inverse-problem based, not data-driven.
- Ensemble methods combining QFT with volumetric baselines as the core approach.
- Working on the forward model (data acquisition, SPAD hardware) rather than the reconstruction algorithm.
- Simply scaling to larger models or datasets without methodological innovation.
