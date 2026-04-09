# Overview

- Paper: `2508.02003`
- Title: `Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform`
- Area: computational imaging / NLOS reconstruction

This workspace contains a recognizable implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `core_claim`: the method runs on a bundled real Zaragoza-style sample, reproduces the paper's lightweight efficiency behavior, and includes a separate complexity experiment showing that the sequential-loading variant reduces memory growth while preserving the same reconstruction.
