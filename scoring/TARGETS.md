# Evaluation Targets

Every scored target below corresponds to one experiment in [`scores.json`](/home/user/scoring/scores.json).
Run all scored targets with:

```bash
bash scripts/evaluate.sh /home/user/scoring/raw_results.json /home/user/scoring/scores.json
```

The paper implementation that produces the report artifact is run with:

```bash
bash scripts/method.sh
```

## `zaragoza_efficiency_real_sample`
Type: Primary + Constraint

What it tests:
End-to-end efficiency on the bundled real Zaragoza-style confocal sample, using the same task and output format as the paper-aligned benchmark in this workspace.

Primary metric:
- `runtime_s` — lower is better

Constraint metric:
- `memory_mb` — lower is better

Interpretation:
Scientists should improve speed without increasing working memory. A method that is faster only because it uses much more memory should score worse after the weighted comparison.

## `complexity_scaling_cubic_measurements`
Type: Ablation-style constraint check

What it tests:
Whether the lower-memory execution path preserves the intended scaling advantage on cubic confocal measurement tensors instead of collapsing back toward the standard higher-memory behavior.

Primary metric:
- `memory_order` for `quasi_fresnel_loading` — lower is better

Constraint / comparison target:
- `memory_order` for `quasi_fresnel_traditional` is included as the reference behavior that the lower-memory path should improve upon

Interpretation:
This is the scored check for what breaks if the memory-saving idea is ineffective. Improvements should move the lower-memory path downward without redefining the benchmark or changing tensor scaling.

## Unscored diagnostics
`scoring/diagnostics.json` may include extra sanity metrics, but those diagnostics are not gym targets and do not affect the score.
