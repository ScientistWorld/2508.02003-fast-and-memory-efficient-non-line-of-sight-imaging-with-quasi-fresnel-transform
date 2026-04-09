# Evaluation

The paper evaluates on public NLOS datasets, especially Zaragoza simulated confocal data and Stanford captured data. The strongest explicit quantitative claim in the paper is efficiency:
- around `0.17 s` runtime and under `50 MB` memory for the Zaragoza evaluation
- under `0.3 s` runtime and under `50 MB` memory on the Stanford evaluation
- about `0.003 s` per frame on the dynamic Stanford sequence

The current workspace is being retargeted to a stronger minimum experiment built around the public Zaragoza Stanford bunny confocal scene. That benchmark measures both:
- depth quality via `depth_mae_cm`, matching the numeric bunny comparison in Fig. 5
- efficiency via `runtime_s` and `memory_mb`, matching the public Zaragoza efficiency claim in the Results section

Additional public Zaragoza scenes are treated as diagnostics unless they also expose trustworthy ground truth through the HDF5 metadata.
