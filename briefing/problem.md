# Problem Definition

Non-line-of-sight (NLOS) imaging reconstructs a hidden scene from time-resolved light measurements on a visible relay wall. In the confocal setting each scanned wall point is both illuminated and observed, so a measurement is a 3D photon-count histogram over wall position (x, y) and time of flight.

Hidden objects in this benchmark are surface-like: each wall position (x, y) sees at most one surface point, described by an albedo a(x, y) and a depth d(x, y) (distance from the wall plane). The task is to recover both maps, at the wall's sampling resolution, from noisy confocal histograms.

The practical difficulty is scale. A histogram for an N x N scan with M time bins has N²M entries (256 x 256 x 512 counts is 64 MB as uint16; 512 x 512 x 512 is 256 MB), and reconstruction methods that operate on full 3D volumes need several times that in working memory. The benchmark therefore asks for reconstructions that are accurate **and** fit in a small, fixed memory budget, measured on the largest scans.

Success is measured by:
- depth accuracy on object pixels,
- albedo fidelity (correlation and scale-aligned PSNR against the true albedo),
- peak working memory of the reconstruction process, measured by the evaluator,
- subject to hard constraints: valid outputs on every scene, a 256 MB memory budget, a per-scene time limit, and a minimum reconstruction quality (a run that does not recover the scene is failed).
