# Overview

- Paper: `2508.02003`
- Title: `Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform`
- Area: computational imaging / NLOS reconstruction

This workspace contains a faithful implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `core_claim`: the three-step reconstruction pipeline runs end to end on both synthetic and real Zaragoza confocal data, producing depth MAE of 0.49 cm on the tracked 64x64 quality proxy. The efficiency target now scores the paper's FDH-style aggregated path on public Zaragoza bunny measurements, with full-histogram and sequential-loading runs kept as diagnostics.
