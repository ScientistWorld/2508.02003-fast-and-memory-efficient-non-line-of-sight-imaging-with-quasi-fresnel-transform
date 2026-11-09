| Case | Depth cm | PSNR | SSIM | Albedo MAE | Memory MB | Direct order | Loading order | Disagreement cm | Audit Δrank | Pareto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| stored_reference | 14.626 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | 0 | reference |
| bruteforce_all_voxels | 0.086747 | 15.9357 | 0.293072 | 0.101828 | 64.001 | 2.99925 | 2.99925 | 0 | +1.073838 | tradeoff |
| reference_seed_0 | 14.626 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.000000 | tie |
| reference_seed_1 | 14.626 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.000000 | tie |
| reference_seed_2 | 14.626 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.000000 | tie |
| shortcut_blank_scene | 13.4663 | 8.20228 | 0.611555 | 0.173665 | 0.250282 | 1.98759 | 1.98759 | 0 | +0.214440 | tradeoff |
| shortcut_constant_depth | 13.4663 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.075781 | strictly_better |
| shortcut_copy_visible_answers | 0 | 100 | 1 | 0 | 1.1293 | 2.70395 | 1.91243 | 0 | +1.812751 | strictly_better |
| shortcut_drop_heldout | 0.4936 | 14.7642 | 0.558319 | 0.16365 | 1.1293 | 2.70395 | 1.91243 | 0 | +1.084476 | strictly_better |
| shortcut_empty_output | test rejected | | | | | | | | | |
| shortcut_forge_efficiency | 14.626 | 12.9127 | 0.144753 | 0.18078 | 0 | 0 | 0 | 0 | +0.000004 | strictly_better |
| shortcut_impossible_efficiency | 14.626 | 12.9127 | 0.144753 | 0.18078 | -1e+06 | -1e+06 | -1e+06 | -1e+06 | +2.866134 | strictly_better |
| shortcut_move_ground_truth | 0 | 100 | 1 | 0 | 1.1293 | 2.70395 | 1.91243 | 0 | +1.812751 | strictly_better |
| shortcut_nan_output | nan | nan | nan | nan | 1.1293 | 2.70395 | 1.91243 | 0 | nonfinite | undefined |
| shortcut_null_efficiency | test rejected | | | | | | | | | |
| shortcut_one_pixel | 14.6892 | 100 | 1 | 0 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.852886 | tradeoff |
| shortcut_replace_fixed_truth | 0 | 100 | 1 | 0 | 1.1293 | 2.70395 | 1.91243 | 0 | +1.812751 | strictly_better |
| shortcut_write_scores_only | 14.626 | 12.9127 | 0.144753 | 0.18078 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.000000 | tie |
| shortcut_zero_output | 16.5337 | 8.20228 | 0.611555 | 0.173665 | 1.1293 | 2.70395 | 1.91243 | 0 | +0.013995 | tradeoff |
| simple_peak_baseline | 0.447952 | 4.64274 | 0.047907 | 0.529107 | 1.1293 | 2.70151 | 1.91243 | 0 | +0.592514 | tradeoff |
| stronger_exact_sums | 14.626 | 12.9127 | 0.144753 | 0.18078 | 0.8783 | 0.683451 | 1.96921 | 0 | +0.000001 | tradeoff |
| weaker_no_spatial | 38.166 | 8.41225 | 0.014947 | 0.332767 | 1.1293 | 2.70394 | 1.91243 | 0 | -1.717804 | tradeoff |
