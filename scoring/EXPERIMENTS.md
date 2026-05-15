# Experiment Overview

## `zaragoza_bunny_depth_error`
Measures whether a reconstruction method preserves useful scene geometry for the Zaragoza Stanford bunny target, using depth mean absolute error in centimeters. This environment scores that target on a tracked synthetic Zaragoza-style bunny proxy with metric ground truth; the public measurement HDF5 files available in this workspace do not include the 2D ground-truth maps needed for this metric.

## `zaragoza_efficiency_public_bunny`
Measures peak working memory on an available public Zaragoza bunny measurement. This is intentionally separate from the quality proxy so public measured transient data remains part of the benchmark.
