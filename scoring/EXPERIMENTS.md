# Experiment Overview

## `surface_reconstruction`
Establishes whether a method actually recovers the hidden geometry and appearance of surface-like objects from noisy confocal measurements at a realistic scan size (256 x 256 points over a 1 m wall, with additional 384 x 384 / 512 x 512 scans). Depth error on object pixels is the headline quantity; albedo correlation and scale-aligned albedo PSNR check that the recovered image shows the right objects in the right places. Scores are averages over several scenes so that one easy or hard scene does not decide the ranking. Runs that do not recover the scene beyond what a constant-depth guess or an uninformative image would give are counted as failures.

## `working_memory`
Establishes how much working memory a method needs to produce those reconstructions, measured by the evaluator from the operating system while the method runs, on the largest scans of the split. It captures the practical claim that hidden-scene reconstruction can be done on memory-limited devices; methods above a fixed budget fail. It is reported alongside, not instead of, reconstruction quality: memory savings only count for runs that still solve the reconstruction task.
