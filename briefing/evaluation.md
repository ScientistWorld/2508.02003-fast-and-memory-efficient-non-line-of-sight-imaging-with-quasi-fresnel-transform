# Evaluation

The paper evaluates on public NLOS datasets, especially Zaragoza simulated confocal data and Stanford captured data. The strongest explicit quantitative claim in the paper is efficiency:
- around `0.17 s` runtime and under `50 MB` memory for the Zaragoza evaluation
- under `0.3 s` runtime and under `50 MB` memory on the Stanford evaluation
- about `0.003 s` per frame on the dynamic Stanford sequence

The current workspace can evaluate:
- a bundled public Zaragoza bunny confocal sample in `data/zaragoza/`
- an additional lightweight public Zaragoza confocal sample in `data/zaragoza/public/`
- a synthetic sanity-check scene generated from the same three-point transport model

Current scoring is therefore limited to the paper's explicitly reported efficiency metrics on the bundled real sample:
- `runtime_s`
- `memory_mb`

Proxy quality metrics are only used when trustworthy ground truth is available in the workspace. Public HDF5 files without ground truth are treated as efficiency-only benchmarks.
