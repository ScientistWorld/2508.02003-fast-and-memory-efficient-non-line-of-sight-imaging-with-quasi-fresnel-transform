# Problem Definition

What problem does this paper address? Write this so that someone with no knowledge of the paper can understand what needs to be solved and how success is measured.

Do NOT describe the paper's method or solution here — only the problem itself. Think about if a future scientist agent try to solve this problem from scratch without knowing what approach the paper took. If you leak the solution, you compromise the benchmark.

## Research Question

Non-line-of-sight (NLOS) imaging reconstructs hidden objects by analyzing reflections from an intermediary relay wall. In a typical setup, a laser illuminates a relay wall, light bounces to the hidden scene, reflects back to the relay wall, and is captured by a single-photon avalanche diode (SPAD) sensor. The sensor records time-resolved photon counts across many scan points on the relay wall over many time bins, producing a 3D data cube (2D spatial × 1D time).

**The core challenge**: Existing NLOS reconstruction methods represent both measurement data and the hidden scene as 3D volumetric data, leading to O(N³) computational and memory complexity. This makes real-time, high-resolution NLOS imaging impractical on resource-constrained devices.

## Why It Matters

NLOS imaging has wide applications: surveillance, autonomous navigation, medical imaging, and archaeology. However, current methods are too computationally expensive and memory-intensive for real-time, high-resolution reconstruction — especially on lightweight devices like mobile phones or embedded systems. Practical NLOS imaging requires algorithms that can reconstruct 1024×1024 hidden scenes in under 1 second using less than 50 MB of memory.

## Success Criteria

A successful solution should:
- Reconstruct the hidden scene (albedo and depth maps) from time-resolved SPAD measurements
- Achieve O(N² log N) computational complexity or better for N×N scanning points
- Achieve O(N²) memory complexity or better
- Run reconstruction of a 512×512 hidden scene in under 0.3 seconds
- Use less than 50 MB of memory for 512×512 reconstruction
- Maintain reconstruction quality comparable to existing state-of-the-art methods (visual fidelity, MAE on depth)
