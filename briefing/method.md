# Paper's Method (Quasi-Fresnel transform, Wei et al. 2025)

The hidden scene is modelled as a 2D albedo map a(x) and a 2D depth map d(x) instead of a 3D voxel volume. Reconstruction (Alg. 1) has three analytical steps, for a fixed parameter s:

1. **Integration over time (Eq. 3).** phi(x; s) = sum_t r_t^k exp(-i r_t^2 / (4 s^2)) tau(x, t) dr, with r_t the one-way distance of bin t. This collapses the N x N x M histogram to a complex N x N field.
2. **Deconvolution in space (Eq. 5).** psi(x; s) = (1 / (16 pi^2 s^4)) * integral exp(i |x~ - x|^2 / (4 s^2)) phi(x~; s) dx~, a separable chirp convolution evaluated with 1D FFTs along each wall axis.
3. **Result extraction (Eq. 4).** albedo = |psi|, depth = (-2 i s^3 psi^-1 dpsi/ds)^(1/2), with dpsi/ds from two very close s values (s +/- 1e-7 m here) and the real part of the radicand.

Memory variants (Table 1): "Traditional" loads the full histogram (O(N^3) memory); "Loading" folds each time bin into phi as it is read (O(N^2) memory); "FDH" receives phi from hardware (O(N^2 log N) time).

## This workspace
- `method/quasi_fresnel.py`: the three steps (`quasi_fresnel_time_integral[_stream|_loading]`, `quasi_fresnel_spatial_deconv`, `extract_albedo_depth`, `quasi_fresnel_reconstruct[_from_phi]`).
- `method/run_qf.py`: benchmark command (default: the paper's Loading variant reading `transient.npy` one time bin at a time; `--mode traditional` loads the full histogram).
- `method/select_s.py` + `method/qf_params.json`: the paper sets s per dataset (0.02 m for its noise-free Zaragoza simulations, 0.025 m USAF, 0.05–0.10 m Stanford) and ties its admissible range to sampling density and SNR. Here s is chosen once from the grid {0.02, 0.025, 0.03, 0.035, 0.04, 0.05} m on the visible train scenes only (`bash scripts/method.sh --select-s`).
