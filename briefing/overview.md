# Overview

- **Paper ID:** 2508.02003
- **Title:** Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform
- **Domain:** Computational Optics / Non-line-of-sight Imaging
- **TL;DR:** A novel algorithm that exploits the 2D nature of hidden scenes via a Quasi-Fresnel transform to achieve real-time, high-resolution NLOS reconstruction with O(N² log N) time and O(N²) memory complexity — orders of magnitude faster and more memory-efficient than prior methods.

## Short Summary

NLOS imaging reconstructs hidden objects from time-resolved light measurements captured on a relay wall. Existing methods treat both measurements and hidden scenes as 3D volumes, leading to prohibitive computational and memory costs. This paper observes that hidden scenes are inherently 2D (albedo and depth maps), and proposes a Quasi-Fresnel transform that directly maps time-resolved measurements to 2D scene representations. The transform reduces complexity from O(N³) to O(N² log N), enabling 1024×1024 reconstruction in under 1 second with <50 MB memory on a CPU.

## Key Results

- **Runtime**: Reconstruction at 512×512 in ~0.17–0.3 s (vs. >6.39 s for prior methods) — 37× speedup
- **Memory**: <50 MB peak usage at 512×512 resolution (vs. >13 GB for prior methods) — 260× reduction
- **Quality**: Comparable or better visual quality and depth MAE vs. FBP, LCT, FK, and Phasor Field on Zaragoza and Stanford datasets
- **Dynamic**: 32×32 dynamic scene reconstruction at ~0.003 s per frame (enabling >300 fps potential)
