# Fast and Memory-efficient Non-line-of-sight Imaging with Quasi-Fresnel Transform

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2508.02003"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2508.02003-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2508.02003](https://arxiv.org/abs/2508.02003) |
|:---|:---|

## Summary

This workspace contains a faithful implementation of the paper's Quasi-Fresnel algorithm and packages it as a runnable benchmark. The current milestone is `core_claim`: the three-step reconstruction pipeline runs end to end on both synthetic and real Zaragoza confocal data, producing depth MAE of 0.49 cm on the tracked 64x64 quality proxy. The efficiency target now scores the paper's FDH-style aggregated path on public Zaragoza bunny measurements, with full-histogram and sequential-loading runs kept as diagnostics.

## Run it

```bash
pip install sciworld
sw research 2508.02003 --mode innovate --agent claude-code
sw evaluate 2508.02003
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

