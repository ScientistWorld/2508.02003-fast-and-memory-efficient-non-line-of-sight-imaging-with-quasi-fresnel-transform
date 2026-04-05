# Paper's Method

How the paper approaches the problem, i.e. the paper's core contributions.

## Key Contribution

The paper introduces a **Quasi-Fresnel Transform** to exploit the inherent 2D nature of hidden scenes. Instead of representing the hidden scene as a 3D volume, the method represents it using 2D functions (albedo map a(x) and depth map d(x)), enabling direct inversion from time-resolved measurements to the hidden scene with dramatically reduced complexity.

## Approach

### Core Insight

The volumetric albedo f(y) of the hidden scene is modeled as f(x, z) = a(x)·δ(z − d(x)), where a(x) is the albedo map and d(x) is the depth map — both purely 2D functions. This parameterization reduces the problem from 3D to 2D.

### Algorithm (3 steps)

1. **Time integration**: Aggregate the 3D time-resolved measurement τ(x, t) into a 2D function φ(x; s) using a weighted 1D integral over time. This is the Quasi-Fresnel transform. The paper shows this can be done on hardware (FDH mode), or by sequential loading (O(N²) memory).

2. **Spatial deconvolution**: Recover ψ(x; s) from φ(x; s) via a 2D convolution with a separable kernel. This can be efficiently implemented with 2D FFT (O(N² log N) computation).

3. **Result extraction**: Extract albedo as a(x) = |ψ| and depth as d(x) = (−2i·s³·ψ⁻¹·∂ψ/∂s)^(1/2).

### Complexity

| Implementation | Runtime | Memory |
|---|---|---|
| FBP/LCT/FK/Phasor | O(N³ log N) | O(N³) |
| Paper (Traditional) | O(N³) | O(N³) |
| Paper (Sequential Loading) | O(N³) | O(N²) |
| **Paper (FDH)** | **O(N² log N)** | **O(N²)** |

The FDH mode (Fourier Domain Histogram) obtains φ directly from hardware and achieves the best complexity.

### Key Parameters

- **s**: The Quasi-Fresnel parameter controlling wavefront spread. Paper uses s ∈ [0.02, 0.1] depending on the scene.
- **k**: Scattering parameter — k=4 for isotropic scattering, k=2 for retroreflective materials.
- **c**: Speed of light (constant).

## Main Claims

1. **Primary**: The Quasi-Fresnel transform enables real-time, high-resolution NLOS reconstruction with O(N² log N) computational and O(N²) memory complexity — orders of magnitude better than existing methods.

2. **Secondary**: The method achieves comparable reconstruction quality to state-of-the-art methods (FBP, LCT, FK, Phasor Field) while being 37× faster and using 260× less memory.

3. **Ablation**: Removing or mis-tuning parameter s degrades reconstruction quality.
