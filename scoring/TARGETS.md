# Evaluation Targets

## Primary target: efficiency on confocal NLOS reconstruction
Optimize runtime and memory on the bundled real Zaragoza-style sample while keeping the Quasi-Fresnel algorithm intact.
- `runtime_s`: lower is better
- `memory_mb`: lower is better

## Secondary target: loading-mode complexity
Recover the paper's Table 1 claim that sequential loading preserves the Quasi-Fresnel computation while lowering the working-memory scaling from cubic to quadratic.
- `runtime_order`: lower is better
- `memory_order`: lower is better

## Diagnostic tracking: reconstruction sanity
The workspace also prints proxy quality metrics on:
- the bundled real sample after downsampling the 1024x1024 ground truth to the 32x32 measurement grid
- a synthetic three-point-transport sanity scene
- consistency between the traditional and sequential-loading reconstructions on the bundled real sample

These diagnostics are supporting evidence for the current milestone, not additional paper-reference targets.
