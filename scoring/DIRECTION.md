# Research Direction

Fast, memory-lean confocal NLOS reconstruction of surface-like hidden scenes.

Priority directions:
- lower depth error and better albedo fidelity under shot noise, without volumetric working memory;
- lower peak working memory at large scan sizes (the 512 x 512 hidden scans set the memory score) without losing reconstruction quality;
- robustness across scene types (tilted and curved surfaces, textured albedo, several objects) and scan resolutions.

Out of scope:
- methods that exceed the memory budget (full 3D volumes at these sizes);
- learned predictors trained on external labels, or anything that reads ground truth or evaluator internals;
- changing the scenes, noise, metrics or constraints.
