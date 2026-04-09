# Problem Definition

Non-line-of-sight imaging reconstructs a hidden scene from transient measurements collected on a visible relay wall. In the confocal setting used by this paper, each relay-wall point is both illuminated and observed, producing a 3D histogram over wall position and time.

The practical problem is not only reconstruction quality but scalability. Prior NLOS pipelines typically reconstruct a 3D volume, which is expensive in both runtime and memory. The paper targets hidden scenes that are effectively 2D surfaces with albedo and depth, and asks whether one can reconstruct those scenes much more efficiently while keeping useful image quality.

Success is measured by:
- whether a reconstruction algorithm runs end-to-end on transient confocal measurements
- whether runtime and memory are dramatically lower than prior volumetric methods
- whether the recovered hidden object remains visually meaningful
