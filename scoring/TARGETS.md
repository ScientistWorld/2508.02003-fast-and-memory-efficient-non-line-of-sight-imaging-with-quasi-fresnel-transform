# Evaluation Targets

## Primary target: efficiency on confocal NLOS reconstruction
Optimize runtime and memory on the bundled real Zaragoza-style sample while keeping the Quasi-Fresnel algorithm intact.
- `runtime_s`: lower is better
- `memory_mb`: lower is better

## Secondary tracking: reconstruction sanity
The current workspace also prints proxy quality metrics on:
- the bundled real sample after downsampling the 1024x1024 ground truth to the 32x32 measurement grid
- a synthetic three-point-transport sanity scene

These proxy metrics are diagnostic only in the current milestone. They are not paper-reference targets yet.

## Secondary tracking: loading-mode consistency
The evaluator also benchmarks the paper's sequential-loading variant on the same bundled real sample and records:
- its runtime and memory in the same environment
- consistency with the traditional Quasi-Fresnel path

These numbers are diagnostic until the loading-mode benchmark has been rerun and verified in-container.
