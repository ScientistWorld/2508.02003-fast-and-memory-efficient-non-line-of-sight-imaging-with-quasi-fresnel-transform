# Problem Definition

Non-line-of-sight imaging reconstructs a hidden scene from transient measurements collected on a visible relay wall. In the confocal setting, each relay-wall point is both illuminated and observed, producing a 3D histogram over wall position and time.

The practical problem is not only reconstruction quality but scalability. Hidden scenes in this benchmark are surface-like objects described by albedo and depth maps, and the goal is to recover those maps with useful fidelity while keeping working memory low.

Success is measured by:
- whether a reconstruction algorithm runs end-to-end on transient confocal measurements
- whether working memory stays low on the fixed public-scene benchmark
- whether the recovered hidden object remains geometrically and visually meaningful
