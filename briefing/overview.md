# Overview

- Paper: `2508.02003`
- Title: `Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform`
- Area: computational imaging / NLOS reconstruction

This workspace contains a recognizable implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `method_runs`: the three-step reconstruction pipeline runs end to end, the Zaragoza HDF5 metadata path has been corrected, and the evaluation now covers both the bundled bunny sample and an additional public Zaragoza scene. The next job re-runs the benchmark after these integrity fixes before any higher milestone can be claimed.
