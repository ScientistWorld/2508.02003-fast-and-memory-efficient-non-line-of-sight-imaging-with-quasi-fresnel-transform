# Evaluation

## Method contract

A method is a command registered in `scoring/methods.json`:

```json
{"methods": {"my_method": {"command": ["python3", "path/to/my_method.py"]}}}
```

For every scene, the evaluator runs, as a fresh process with the workspace as working directory,

```
<command> --scene <scene_dir> --output <prediction.npz>
```

`<scene_dir>` contains:
- `transient.npy` — uint16 photon counts, layout `[time_bin, x_index, y_index]`, C order (so each time bin is a contiguous N x N slice and the file can be read one bin at a time);
- `meta.json` — acquisition geometry: `wall_points_per_axis` N, `wall_size_m` (1.0; wall coordinates `x_i = y_i = -0.5 + i/(N-1)` m, wall plane z = 0, scene at z > 0), `time_bins` (512), `bin_width_m` (0.0015: bin t collects returns whose one-way wall-to-scene distance lies in `[t, t+1) * 1.5 mm`, i.e. 3 mm of photon path per bin), `falloff_exponent` (4), `max_observable_depth_m` (0.768).

The method must write `<prediction.npz>` with two real arrays of shape exactly (N, N): `albedo` (finite, non-negative, not constant; any global scale) and `depth` (finite, metres, within `[0, max_observable_depth_m]`), indexed like the wall grid. Nothing else the method writes is read. Methods run single-threaded (thread environment variables are set to 1). `bash scripts/method.sh` registers the reference method.

## Scenes

Procedurally generated hidden scenes: one to three surface objects (disks, ellipses, rectangles, annuli, triangles, crosses, L-shapes; plain or striped albedo; tilted planes or curved patches at 0.2–0.62 m depth), rendered with a confocal three-bounce model (Lambertian wall and object, inverse-square falloff on each leg, no occlusion between objects) and Poisson photon noise with a small background.

- **Train (visible):** 6 scenes — five 256 x 256 scans and one 384 x 384 scan — rendered deterministically into `data/train_scenes/` (`python3 data/nlos_scenes.py --write-train`), with ground truth in `ground_truth.npz` for inspection.
- **Test (hidden):** 12 scenes from the same family with private seeds — ten 256 x 256 and two 512 x 512 scans — rendered inside the hidden evaluator at test time into a temporary directory and deleted after use.

## Metrics (per split, means over its scenes unless noted)

`surface_reconstruction` (weight 0.6)
- `depth_mae_cm` (primary, lower is better): mean absolute depth error in cm over wall pixels fully covered by an object.
- `albedo_ncc` (higher is better): Pearson correlation between predicted and true albedo over all wall pixels.
- `albedo_psnr_db` (higher is better): PSNR after the least-squares global scale fit of the prediction to the true albedo normalised to peak 1.

`working_memory` (weight 0.4)
- `peak_memory_mb` (primary, lower is better): the evaluator samples the method's process tree from `/proc` (per-process high-water mark and summed resident memory, which includes memory-mapped file pages the process touches) and reports the maximum over the split's scenes, rounded to 4 MB (identical runs vary by about 1 MB; raw values are in `_status` / `_details`). The largest scans set it. Wall-clock time is recorded for debugging only and never scored.

## Constraints (a violation fails the whole run)

- a valid prediction on every scene (shape, dtype, finiteness, ranges as above), exit status 0;
- peak memory ≤ 256 MB on every scene (runs are killed when they exceed it);
- ≤ 300 s per scene;
- task success: mean `depth_mae_cm` ≤ 0.5 x the error of the best constant-depth answer, and mean `albedo_ncc` ≥ 0.2.

A failed run receives the same bounded values on every metric — the best-constant depth error, correlation 0, the PSNR of an empty image, and the full 256 MB — so it can never rank above a run that solves the task.

## Entry points

- `bash scripts/evaluate_train.sh` → `scoring/scores_train.json` (visible scenes; predictions kept in `outputs/<method>/train_predictions/`).
- `bash scripts/evaluate.sh` → `scoring/scores.json` (same visible evaluation).
- `bash scripts/evaluate_test.sh` → `scoring/scores_test.json` (hidden scenes).

All score every registered method with no arguments. Score files also carry `_status` (validity and failure reasons) and `_details` (per-scene values).
