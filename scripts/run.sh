#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Verify the FDH-style aggregation path is numerically equivalent to the
# sequential-loading path on a tiny deterministic tensor, then refresh the
# scored artifacts through the standard method/eval interface. Extra public
# Zaragoza scenes are enabled for diagnostics when they are present locally.
python3 - <<'PY'
import numpy as np
from method.quasi_fresnel import quasi_fresnel_reconstruct

rng = np.random.default_rng(250802003)
tau = rng.random((8, 8, 12), dtype=np.float64)
kwargs = dict(s=0.02, dt=0.003, k=4, area=1.0)
albedo_loading, depth_loading = quasi_fresnel_reconstruct(
    tau, integration_mode="loading", **kwargs
)
albedo_fdh, depth_fdh = quasi_fresnel_reconstruct(tau, use_fdh=True, **kwargs)
np.testing.assert_allclose(albedo_loading, albedo_fdh, rtol=1e-10, atol=1e-12)
np.testing.assert_allclose(depth_loading, depth_fdh, rtol=1e-10, atol=1e-12)
print("FDH smoke test passed")
PY

NLOS_EXTRA_PUBLIC=1 bash scripts/method.sh
bash scripts/evaluate_train.sh "${ROOT}/scoring/raw_results.json" "${ROOT}/scoring/scores_train.json"
bash scripts/evaluate_test.sh "${ROOT}/scoring/raw_results.json" "${ROOT}/scoring/scores_test.json"
python3 validate.py --compare
