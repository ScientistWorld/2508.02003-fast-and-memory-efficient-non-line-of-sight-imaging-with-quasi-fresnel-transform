#!/bin/bash
# Hardening job: (1) smoke tests of the evaluator's measurement and of the
# method's streaming path, (2) render the visible scenes, (3) score the
# reference alone through the no-argument entrypoints, (4) run the audit cohort
# (reference rerun, better/weaker variants, baselines, brute force, shortcuts)
# through the same no-argument entrypoints, (5) uncapped memory diagnostics,
# (6) final reference-only scoring, analysis and validation.
# Steps are idempotent; finished audit steps are skipped on a restart.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
H=redteam/hardening
A=outputs/hardening_audit
mkdir -p "$H/logs" "$A"
step() { echo "=== $(date -u +%FT%TZ) $*"; }

step "environment"
python3 -c "import sys, numpy, scipy, numba; print(sys.version); print('numpy', numpy.__version__, 'scipy', scipy.__version__, 'numba', numba.__version__)"
nproc || true

step "smoke tests"
python3 - <<'PY' 2>&1 | tee "$H/logs/smoke.log"
import json, sys, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, "method"); sys.path.insert(0, "eval/train"); sys.path.insert(0, "redteam/hardening")
from quasi_fresnel import quasi_fresnel_reconstruct
import train_harness as h

rng = np.random.default_rng(250802003)
tau = rng.random((8, 8, 12))
kw = dict(s=0.02, dt=0.003, k=4, area=1.0)
ref = quasi_fresnel_reconstruct(tau, integration_mode="traditional", **kw)
for kwargs in (dict(integration_mode="loading"), dict(use_fdh=True)):
    out = quasi_fresnel_reconstruct(tau, **kwargs, **kw)
    np.testing.assert_allclose(out[0], ref[0], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(out[1], ref[1], rtol=1e-10, atol=1e-12)
print("loading / FDH / traditional agree")

# file-streaming CLI path vs in-memory traditional path vs lean audit variant
from run_qf import reconstruct
import variants
with tempfile.TemporaryDirectory() as tmp:
    scene = Path(tmp)
    counts = rng.poisson(3.0, size=(64, 32, 32)).astype(np.uint16)
    np.save(scene / "transient.npy", counts)
    (scene / "meta.json").write_text(json.dumps({"wall_points_per_axis": 32, "wall_size_m": 1.0, "time_bins": 64,
        "bin_width_m": 0.0015, "falloff_exponent": 4, "max_observable_depth_m": 0.096}))
    a1, d1 = reconstruct(scene)
    a2, d2 = reconstruct(scene, mode="traditional")
    a3, d3 = variants.lean_reconstruct(scene)
    np.testing.assert_allclose(a1, a2, rtol=1e-9); np.testing.assert_allclose(d1, d2, rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(a1, a3, rtol=1e-7); np.testing.assert_allclose(d1, d3, rtol=1e-5, atol=1e-7)
print("streaming CLI == traditional == lean variant")

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    alloc = ["python3", "-c", "import numpy as np, time; a = np.ones(150 * 2**20 // 8); time.sleep(0.3); print(a.sum())"]
    r = h.run_method(alloc, tmp, tmp / "o.npz", tmp / "l.log")
    print("150 MB allocation measured:", round(r["peak_rss_mb"], 1), "MB", r)
    assert r["peak_rss_mb"] > 150 and r["killed"] is None
    r = h.run_method(["python3", "-c", "import numpy as np, time; a = np.ones(400 * 2**20 // 8); time.sleep(5)"], tmp, tmp / "o.npz", tmp / "l.log")
    print("400 MB allocation:", r)
    assert r["killed"] == "memory_budget_exceeded"
    ballast = np.ones(300 * 2**20 // 8)  # evaluator's own memory must not leak into the measurement
    r0 = h.run_method(["python3", "-c", "import time; time.sleep(0.2)"], tmp, tmp / "o.npz", tmp / "l.log")
    print("bare interpreter (evaluator holding 300 MB):", r0)
    r1 = h.run_method(["python3", "-c", "import numpy, time; time.sleep(0.2)"], tmp, tmp / "o.npz", tmp / "l.log")
    print("interpreter + numpy:", r1)
    del ballast
    assert r0["peak_rss_mb"] < 40 and r1["peak_rss_mb"] < 80 and r1["peak_rss_mb"] > r0["peak_rss_mb"]
print("SMOKE OK")
PY

step "render visible train scenes"
python3 data/nlos_scenes.py --write-train 2>&1 | tee "$H/logs/render_train.log"

step "select s on the visible train scenes (writes method/qf_params.json)"
bash scripts/method.sh --select-s 2>&1 | tee "$H/logs/select_s.log"

step "reference-only scoring (first pass)"
bash scripts/method.sh
bash scripts/evaluate.sh > "$H/logs/reference_run1_scores_json.log" 2>&1
bash scripts/evaluate_train.sh > "$H/logs/reference_run1_train.log" 2>&1
bash scripts/evaluate_test.sh > "$H/logs/reference_run1_test.log" 2>&1
tail -n 3 "$H/logs/reference_run1_train.log" "$H/logs/reference_run1_test.log"
cp scoring/scores_train.json "$H/scores_train_reference_run1.json"
cp scoring/scores_test.json "$H/scores_test_reference_run1.json"

step "audit cohort"
cp scoring/methods.json "$A/methods_backup.json"
mkdir -p "$A/gt_backup"
for d in data/train_scenes/*/; do cp "$d/ground_truth.npz" "$A/gt_backup/$(basename "$d").npz"; done
if [ ! -f "$H/scores_train_cohort.json" ]; then
    cp "$H/registry_train.json" scoring/methods.json
    NLOS_AUDIT_DIR="$A/train" bash scripts/evaluate_train.sh > "$H/logs/cohort_train.log" 2>&1
    cp scoring/scores_train.json "$H/scores_train_cohort.json"
fi
if [ ! -f "$H/scores_test_cohort.json" ]; then
    cp "$H/registry_test.json" scoring/methods.json
    NLOS_AUDIT_DIR="$A/test" bash scripts/evaluate_test.sh > "$H/logs/cohort_test.log" 2>&1
    cp scoring/scores_test.json "$H/scores_test_cohort.json"
fi
cp "$A/methods_backup.json" scoring/methods.json
for d in data/train_scenes/*/; do cp "$A/gt_backup/$(basename "$d").npz" "$d/ground_truth.npz"; done
rm -f outputs/forged_efficiency.json

step "uncapped diagnostics"
if [ ! -f "$H/uncapped_diagnostics.json" ]; then
    python3 "$H/uncapped.py" > "$H/logs/uncapped.log" 2>&1 || echo "uncapped diagnostics failed (see log)"
fi

step "final reference-only scoring"
bash scripts/method.sh
bash scripts/evaluate.sh > "$H/logs/final_scores_json.log" 2>&1
bash scripts/evaluate_train.sh > "$H/logs/final_train.log" 2>&1
bash scripts/evaluate_test.sh > "$H/logs/final_test.log" 2>&1
bash scripts/baseline.sh > "$H/logs/final_baseline.log" 2>&1
tail -n 3 "$H/logs/final_train.log" "$H/logs/final_test.log" "$H/logs/final_baseline.log"

step "analysis and validation"
python3 "$H/analyze.py" > "$H/logs/analyze.log" 2>&1; tail -n 80 "$H/logs/analyze.log"
python3 validate.py --post-design 2>&1 | tee "$H/logs/validate.log"
step "done"
