# Experiment Overview

## zaragoza_kylin_reconstruction
Tests reconstruction quality and computational efficiency on a complex hidden object (kylin) with 256x256 scanning points. This experiment measures whether the method can recover fine geometric details (legs, horn, body) at varying depths while maintaining sub-second runtime and low memory usage. Compares against established volumetric NLOS reconstruction methods.

## stanford_reconstruction
Tests reconstruction on real-captured NLOS measurements at 512x512 scanning points. This experiment evaluates whether the method generalizes to real sensor data (with real noise, calibration imperfections, and non-ideal reflectance) while maintaining the efficiency advantages demonstrated on simulated data.

## dynamic_scene
Tests per-frame reconstruction time for a moving hidden object at 32x32 scanning resolution. This experiment evaluates whether the method is fast enough for real-time NLOS imaging of dynamic scenes, targeting sub-5ms per frame reconstruction.
