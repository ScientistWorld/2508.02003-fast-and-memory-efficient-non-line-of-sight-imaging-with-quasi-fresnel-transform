# Evaluation

How success is measured. Describe only the metrics, targets, and evaluation procedure — do NOT describe the paper's method or how they achieved these results. Think of this as a general evaluation protocol for other scientists trying to solve the same problem, where they should not see this paper's solution.

## Metrics

### Primary Metrics

1. **Albedo reconstruction quality** — Peak Signal-to-Noise Ratio (PSNR) and Mean Absolute Error (MAE) between reconstructed albedo and ground truth. Higher PSNR / lower MAE is better.

2. **Depth reconstruction quality** — Mean Absolute Error (MAE) between reconstructed depth map and ground truth depth. Lower MAE is better.

3. **Runtime** — Time in seconds to reconstruct a single frame from measurement data. Lower is better.

4. **Memory usage** — Peak memory consumption in MB during reconstruction. Lower is better.

### Secondary Metrics (contextual)

5. **Complexity class** — Theoretical computational complexity (Big-O) and memory complexity. Should be O(N² log N) or better for computation, O(N²) or better for memory.

## Baselines and Targets

The paper compares against several established NLOS reconstruction methods:

| Method | Reported Runtime (512×512) | Reported Memory | Paper's Method |
|--------|---------------------------|-----------------|----------------|
| FBP (Filtered Back Projection) | >6.39 s | >13.105 GB | ~0.17 s, <50 MB |
| LCT (Light-Cone Transform) | >6.39 s | >13.105 GB | ~0.17 s, <50 MB |
| FK (f-k Migration) | >6.39 s | >13.105 GB | ~0.17 s, <50 MB |
| Phasor Field | >6.39 s | >13.105 GB | ~0.17 s, <50 MB |
| **Proposed** | **~0.17–0.3 s** | **<50 MB** | baseline |

For Zaragoza dataset (256×256 scanning, kylin object):
- Paper's method: ~0.17 s, <50 MB memory
- Other methods: >6.39 s, >13.105 GB memory

For dynamic scene (32×32 scanning):
- Reconstruction time per frame: ~0.003 s (3 ms)

## Evaluation Protocol

### Dataset

Evaluations are performed on public NLOS datasets:
1. **Zaragoza dataset** — Simulated time-resolved NLOS measurements. Hidden objects include kylin, USAF resolution chart, Stanford bunny, and others. Resolution: 256×256 scanning points.
2. **Stanford dataset** — Real captured time-resolved NLOS measurements with real hidden objects (dragon, bunny, teaser, resolution chart). Resolution: 512×512 scanning points.
3. **Dynamic scene** — Time-resolved NLOS measurements of a moving human, captured at 32×32 scanning points with 0.25 s per frame.

### Evaluation Procedure

1. Load the time-resolved measurement data (histogram) for a given hidden scene.
2. Run the reconstruction algorithm to produce albedo and depth maps.
3. Compute metrics against ground truth (where available):
   - Albedo: PSNR, MAE between reconstructed and ground truth albedo
   - Depth: MAE between reconstructed and ground truth depth
4. Measure runtime and peak memory usage during reconstruction.
5. For qualitative evaluation, visually compare reconstructed albedo and depth against ground truth images.

### Evaluation Conditions

- Computational and memory measurements should be taken on a single CPU (no GPU acceleration).
- Runtime is measured as mean over 5 independent runs.
- Memory is the peak usage recorded during reconstruction.
- All methods are evaluated on the same hardware under identical conditions.
