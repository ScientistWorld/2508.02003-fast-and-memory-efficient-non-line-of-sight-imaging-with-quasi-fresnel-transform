# Overview

- Paper: `2508.02003` — Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform
- Area: computational imaging / confocal NLOS reconstruction
- Milestone: `core_claim`

The benchmark asks for reconstructions of surface-like hidden objects (albedo + depth maps) from noisy confocal transients at the paper's Zaragoza acquisition scale (1 m wall, 256 x 256 scans, 3 mm of photon path per bin; plus 384 x 384 / 512 x 512 scans), scored on depth error, albedo fidelity and evaluator-measured peak working memory under a 256 MB budget. Methods are commands the evaluators run themselves on visible train scenes and on hidden test scenes rendered at test time (`briefing/evaluation.md`).

The reference (`quasi_fresnel`) is the paper's three-step Quasi-Fresnel pipeline in its sequential-loading form. See `HARDENING.md` for its scores, the audit of variants, baselines and shortcuts, and known limitations.
