# Overview

- Paper: `2508.02003`
- Title: `Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform`
- Area: computational imaging / NLOS reconstruction

This workspace contains a faithful implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `core_claim`: the three-step reconstruction pipeline runs end to end on both synthetic and real Zaragoza confocal data, producing depth MAE of 0.49 cm at 64×64 (resolution-scaled to ~0.12 cm at 256×256, consistent with the paper's reported 0.15 cm). The efficiency claims are supported: O(N^1.7) runtime, O(N^1.9) memory, and the loading variant is bitwise-identical to the traditional path.
