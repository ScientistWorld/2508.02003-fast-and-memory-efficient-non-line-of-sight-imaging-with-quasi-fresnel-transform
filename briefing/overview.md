# Overview

- Paper: `2508.02003`
- Title: `Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform`
- Area: computational imaging / NLOS reconstruction

This workspace contains a recognizable implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `method_runs`: the three-step reconstruction pipeline runs end to end, the Zaragoza HDF5 loader has been reworked around the public confocal files, and the scored benchmark has been retargeted to the public bunny quality-plus-efficiency claim. The next job executes that corrected benchmark before any higher milestone can be claimed.
