# Evaluation

The paper evaluates on public NLOS datasets, especially Zaragoza simulated confocal data and Stanford captured data. The strongest explicit quantitative claim in the paper is efficiency:
- around `0.17 s` runtime and under `50 MB` memory for the Zaragoza evaluation
- under `0.3 s` runtime and under `50 MB` memory on the Stanford evaluation
- about `0.003 s` per frame on the dynamic Stanford sequence

The current workspace can evaluate:
- a bundled real Zaragoza-style confocal sample in `data/zaragoza/`
- a synthetic sanity-check scene generated from the same three-point transport model

Current scoring is therefore limited to the paper's explicitly reported efficiency metrics on the bundled real sample:
- `runtime_s`
- `memory_mb`

Proxy quality metrics are also printed for debugging, but they are not yet used as paper-reference scores because the current packaged sample and paper do not provide a direct one-to-one quantitative quality table in the workspace.
