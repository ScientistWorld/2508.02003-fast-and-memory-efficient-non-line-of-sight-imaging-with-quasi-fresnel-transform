# Research Direction

Work on fast direct reconstruction for confocal non-line-of-sight surface recovery under the same problem setup as this workspace.

Priority directions:
- improve runtime or working memory without changing the task to a different NLOS formulation
- strengthen the lower-memory path so the scaling advantage holds more clearly on larger public settings
- expand the same evaluation family from the bundled sample to more public Zaragoza or Stanford-style confocal measurements
- improve numerical stability or reconstruction quality while staying in the same direct surface-recovery family

Out of scope:
- replacing the problem with a full 3D volumetric benchmark
- switching to a generic supervised black-box model trained on extra labels
- redefining success around unscored diagnostics instead of the packaged efficiency targets
