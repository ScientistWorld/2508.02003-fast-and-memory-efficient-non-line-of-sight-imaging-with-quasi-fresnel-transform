# Experiment Overview

## zaragoza_efficiency_real_sample
Measures whether the packaged Quasi-Fresnel implementation runs end-to-end on a bundled real Zaragoza-style confocal sample and reports runtime and memory in the same units as the paper's public efficiency claim.

## complexity_scaling_cubic_measurements
Measures whether the packaged implementation exhibits the working-memory trend described in Table 1 when the input is an N x N x N confocal measurement cube. The focus is the difference between the traditional and sequential-loading implementations, especially the reduction in working-memory order.
