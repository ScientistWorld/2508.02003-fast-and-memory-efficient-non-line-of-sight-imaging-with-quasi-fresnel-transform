# Paper's Method

The paper models the hidden scene as a 2D albedo map and a 2D depth map rather than a full 3D voxel volume. Its reconstruction pipeline has three analytical steps:

1. Aggregate the transient histogram over time with a complex quadratic-phase weighting to produce a 2D field `phi(x; s)`.
2. Recover a second complex 2D field `psi(x; s)` by spatial deconvolution in the relay-wall plane.
3. Extract albedo from `|psi|` and depth from the derivative of `psi` with respect to `s`.

This workspace already implements that three-step Quasi-Fresnel pipeline directly from the paper equations.

What is not yet fully reproduced:
- the FDH acquisition path
- a faithful published volumetric baseline for direct comparison
- the full public Zaragoza and Stanford benchmark suite at paper scale
