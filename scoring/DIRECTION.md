# Research Direction

Work on fast direct reconstruction for confocal non-line-of-sight surface recovery under the same public Zaragoza setup as this workspace.

Priority directions:
- improve bunny depth accuracy while staying within the same direct surface-reconstruction problem setting
- improve runtime or working memory on the same scored bunny scene
- strengthen the lower-memory loading path and test it on additional public Zaragoza scenes
- expand the same evaluation family to more public confocal scenes without changing the task definition

Out of scope:
- replacing the problem with an unrelated volumetric or learned black-box benchmark
- switching to a generic supervised predictor trained on extra labels
- redefining success around unscored diagnostics instead of the packaged quality-plus-efficiency targets
