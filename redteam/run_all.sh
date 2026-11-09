#!/bin/bash
set -euo pipefail
cd /home/user
bash scripts/baseline.sh > redteam/packaged_baseline.log 2>&1 || true
for case in reference_seed_0 reference_seed_1 reference_seed_2 \
  stronger_exact_sums weaker_no_spatial simple_peak_baseline \
  shortcut_copy_visible_answers shortcut_move_ground_truth \
  shortcut_replace_fixed_truth shortcut_forge_efficiency \
  shortcut_impossible_efficiency shortcut_constant_depth shortcut_one_pixel shortcut_blank_scene \
  shortcut_zero_output shortcut_empty_output shortcut_nan_output \
  shortcut_drop_heldout shortcut_write_scores_only shortcut_null_efficiency \
  bruteforce_all_voxels; do
  bash "redteam/${case}/run.sh"
done
python3 redteam/summarize.py
