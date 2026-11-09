"""Method-agnostic evaluation harness (train-slice copy).

The harness never imports method code.  A method is a registered command
line; for every scene the harness runs

    <command> --scene <scene_dir> --output <prediction.npz>

as a fresh process, measures that process tree's peak resident memory from
the operating system, validates the written prediction and recomputes every
metric against ground truth it computes itself.  Nothing a method writes
besides its prediction arrays is read.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]

QUALITY_EXPERIMENT = "surface_reconstruction"
MEMORY_EXPERIMENT = "working_memory"

MEMORY_BUDGET_MB = 256.0
TIMEOUT_S_PER_SCENE = 300.0
DEPTH_GATE_FRACTION = 0.5
NCC_GATE = 0.2
POLL_INTERVAL_S = 0.003
METHOD_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,63}$")
THREAD_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


# ── registry ────────────────────────────────────────────────────────────────


def load_registry(path: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return (valid commands, invalid entries -> reason)."""
    data = json.loads(Path(path).read_text())
    methods = data.get("methods") if isinstance(data, dict) else None
    if not isinstance(methods, dict) or not methods:
        raise SystemExit(f"{path}: no registered methods (expected {{'methods': {{name: {{'command': [...]}}}}}})")
    valid: dict[str, list[str]] = {}
    invalid: dict[str, str] = {}
    for name, entry in methods.items():
        if not isinstance(name, str) or not METHOD_NAME_RE.match(name):
            invalid[str(name)] = "invalid method name"
            continue
        command = entry.get("command") if isinstance(entry, dict) else None
        if not (isinstance(command, list) and command and all(isinstance(c, str) and c for c in command)):
            invalid[name] = "registry entry needs a non-empty 'command' list of strings"
            continue
        valid[name] = list(command)
    return valid, invalid


# ── process runner with OS-level memory accounting ──────────────────────────


def _method_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP", "NLOS_AUDIT_DIR")}
    for key in THREAD_VARS:
        env[key] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _children(pid: int) -> list[int]:
    kids: list[int] = []
    try:
        for tid in os.listdir(f"/proc/{pid}/task"):
            try:
                with open(f"/proc/{pid}/task/{tid}/children") as handle:
                    kids.extend(int(x) for x in handle.read().split())
            except OSError:
                continue
    except OSError:
        pass
    return kids


def _proc_memory(pid: int) -> tuple[int, int] | None:
    """(VmRSS, VmHWM) in bytes for one live process, from /proc/<pid>/status.

    VmHWM is the high-water mark of the process's own address space; it is
    reset when the process execs, so it never includes the evaluator's memory
    (unlike getrusage's ru_maxrss, which inherits the parent's high-water
    mark across fork + exec).
    """
    rss = hwm = None
    try:
        with open(f"/proc/{pid}/status") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1]) * 1024
                elif line.startswith("VmHWM:"):
                    hwm = int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    if rss is None or hwm is None:  # zombie / kernel thread: no address space
        return None
    return rss, hwm


def _sample_tree(root_pid: int, hwm_by_pid: dict[int, int]) -> int:
    """Sum of current RSS over the process tree; updates per-process high-water marks."""
    total = 0
    stack = [root_pid]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        mem = _proc_memory(pid)
        if mem is not None:
            total += mem[0]
            if mem[1] > hwm_by_pid.get(pid, 0):
                hwm_by_pid[pid] = mem[1]
        stack.extend(_children(pid))
    return total


def _kill_group(pgid: int) -> None:
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def scratch_root() -> Path:
    """Scratch space for scene inputs and predictions (the container /tmp is tiny)."""
    root = Path(os.environ.get("NLOS_SCRATCH_DIR", str(ROOT / "outputs" / ".scratch")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_method(command: list[str], scene_dir: Path, output_path: Path, log_path: Path,
               budget_mb: float = MEMORY_BUDGET_MB, timeout_s: float = TIMEOUT_S_PER_SCENE) -> dict:
    """Run one method on one scene; peak memory = max(per-process VmHWM, summed tree RSS)."""
    cmd = list(command) + ["--scene", str(scene_dir), "--output", str(output_path)]
    budget_bytes = budget_mb * 1024.0 * 1024.0
    tree_peak = 0
    hwm_by_pid: dict[int, int] = {}
    killed: str | None = None
    start = time.monotonic()
    with open(log_path, "wb") as log:
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(ROOT), env=_method_env(), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
        except OSError as exc:
            return {"launched": False, "error": f"{type(exc).__name__}: {exc}", "exit_code": None,
                    "peak_rss_mb": 0.0, "killed": None, "wall_time_s": 0.0}
        pid = proc.pid
        while True:
            wpid, status, _ = os.wait4(pid, os.WNOHANG)
            if wpid == pid:
                break
            total = _sample_tree(pid, hwm_by_pid)
            if total > tree_peak:
                tree_peak = total
            current_peak = max(tree_peak, max(hwm_by_pid.values(), default=0))
            elapsed = time.monotonic() - start
            if killed is None:
                if current_peak > budget_bytes:
                    killed = "memory_budget_exceeded"
                    _kill_group(pid)
                elif elapsed > timeout_s:
                    killed = "timeout"
                    _kill_group(pid)
            time.sleep(POLL_INTERVAL_S)
        proc.returncode = os.waitstatus_to_exitcode(status)
    _kill_group(pid)  # nothing the method started may outlive it
    hwm_peak = max(hwm_by_pid.values(), default=0)
    peak = max(tree_peak, hwm_peak)
    return {
        "launched": True,
        "exit_code": proc.returncode,
        "peak_rss_mb": peak / 2.0 ** 20,
        "hwm_peak_mb": hwm_peak / 2.0 ** 20,
        "tree_rss_peak_mb": tree_peak / 2.0 ** 20,
        "processes_seen": len(hwm_by_pid),
        "killed": killed,
        "wall_time_s": time.monotonic() - start,  # diagnostic only, never scored
    }


# ── prediction validation and metrics ───────────────────────────────────────


def load_prediction(path: Path, n: int, depth_max: float) -> tuple[tuple[np.ndarray, np.ndarray] | None, str | None]:
    if not path.is_file():
        return None, "no prediction file written"
    try:
        with np.load(path, allow_pickle=False) as data:
            if "albedo" not in data.files or "depth" not in data.files:
                return None, "prediction must contain 'albedo' and 'depth' arrays"
            albedo = np.asarray(data["albedo"])
            depth = np.asarray(data["depth"])
    except Exception as exc:  # noqa: BLE001 - any unreadable file is a failed output
        return None, f"unreadable prediction ({type(exc).__name__})"
    for name, arr in (("albedo", albedo), ("depth", depth)):
        if arr.shape != (n, n):
            return None, f"{name} has shape {arr.shape}, expected {(n, n)}"
        if not (np.issubdtype(arr.dtype, np.floating) or np.issubdtype(arr.dtype, np.integer)):
            return None, f"{name} has non-real dtype {arr.dtype}"
    albedo = albedo.astype(np.float64)
    depth = depth.astype(np.float64)
    if not (np.all(np.isfinite(albedo)) and np.all(np.isfinite(depth))):
        return None, "non-finite values in prediction"
    if albedo.min() < 0.0:
        return None, "negative albedo"
    if depth.min() < 0.0 or depth.max() > depth_max:
        return None, f"depth outside the observable range [0, {depth_max:.3f}] m"
    if not albedo.std() > 0.0:
        return None, "albedo map is constant"
    return (albedo, depth), None


def scene_reference_stats(albedo_gt: np.ndarray, depth_gt: np.ndarray, mask: np.ndarray) -> dict:
    g = albedo_gt / albedo_gt.max()
    oracle = float(np.median(depth_gt[mask]))
    return {
        "oracle_constant_depth_mae_cm": 100.0 * float(np.mean(np.abs(depth_gt[mask] - oracle))),
        "zero_image_psnr_db": 10.0 * float(np.log10(1.0 / np.mean(g * g))),
        "object_pixels": int(mask.sum()),
    }


def scene_metrics(albedo: np.ndarray, depth: np.ndarray, albedo_gt: np.ndarray,
                  depth_gt: np.ndarray, mask: np.ndarray) -> dict:
    g = albedo_gt / albedo_gt.max()
    p = albedo
    pc = p - p.mean()
    gc = g - g.mean()
    denom = float(np.sqrt(np.sum(pc * pc) * np.sum(gc * gc)))
    ncc = float(np.sum(pc * gc) / denom) if denom > 0 else 0.0
    pp = float(np.sum(p * p))
    alpha = max(float(np.sum(p * g)) / pp, 0.0) if pp > 0 else 0.0
    mse = float(np.mean((alpha * p - g) ** 2))
    psnr = 100.0 if mse <= 1e-10 else 10.0 * float(np.log10(1.0 / mse))
    depth_mae = float(np.mean(np.abs(depth[mask] - depth_gt[mask])))
    return {
        "depth_mae_cm": 100.0 * depth_mae,
        "albedo_ncc": ncc,
        "albedo_psnr_db": psnr,
    }


# ── evaluation loop ─────────────────────────────────────────────────────────


class SceneProvider:
    """Interface: ``scenes`` is a list of (scene_id, n); subclasses implement
    ``ground_truth``, ``prepare`` (returns a directory holding transient.npy and
    meta.json) and ``release``."""

    depth_max_m: float = 0.768
    scenes: list[tuple[str, int]] = []

    def ground_truth(self, scene_id: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        raise NotImplementedError

    def prepare(self, scene_id: str) -> Path:
        raise NotImplementedError

    def release(self, scene_id: str) -> None:
        return None


def _penalty(stats: list[dict]) -> dict:
    return {
        "depth_mae_cm": float(np.mean([s["oracle_constant_depth_mae_cm"] for s in stats])),
        "albedo_ncc": 0.0,
        "albedo_psnr_db": float(np.mean([s["zero_image_psnr_db"] for s in stats])),
        "peak_memory_mb": MEMORY_BUDGET_MB,
    }


def summarize(names: list[str], invalid: dict[str, str], records: dict[str, dict],
              stats: list[dict], scene_ids: list[str]) -> dict:
    penalty = _penalty(stats)
    mean_oracle = penalty["depth_mae_cm"]
    scores: dict = {
        "experiments": {
            QUALITY_EXPERIMENT: {"results": {}},
            MEMORY_EXPERIMENT: {"results": {}},
        },
        "_status": {},
        "_details": {},
        "_protocol": {
            "scenes": scene_ids,
            "memory_budget_mb": MEMORY_BUDGET_MB,
            "timeout_s_per_scene": TIMEOUT_S_PER_SCENE,
            "depth_gate": f"mean depth_mae_cm <= {DEPTH_GATE_FRACTION} x mean oracle-constant depth MAE ({DEPTH_GATE_FRACTION * mean_oracle:.4f} cm)",
            "albedo_gate": f"mean albedo_ncc >= {NCC_GATE}",
            "failed_run_values": penalty,
        },
    }
    all_names = sorted(set(names) | set(invalid))
    for name in all_names:
        rec = records.get(name, {"failures": [invalid.get(name, "not run")], "scenes": {}})
        failures = list(rec["failures"])
        per_scene = rec["scenes"]
        if not failures and len(per_scene) != len(scene_ids):
            failures.append("not every scene was reconstructed")
        values = None
        if not failures:
            mean = {k: float(np.mean([per_scene[s][k] for s in scene_ids]))
                    for k in ("depth_mae_cm", "albedo_ncc", "albedo_psnr_db")}
            memory = float(np.max([per_scene[s]["peak_rss_mb"] for s in scene_ids]))
            if memory > MEMORY_BUDGET_MB:
                failures.append(f"peak memory {memory:.1f} MB exceeds the {MEMORY_BUDGET_MB:.0f} MB budget")
            if mean["depth_mae_cm"] > DEPTH_GATE_FRACTION * mean_oracle:
                failures.append(
                    f"task failed: depth error {mean['depth_mae_cm']:.3f} cm is not below "
                    f"{DEPTH_GATE_FRACTION} x the best constant-depth error ({mean_oracle:.3f} cm)")
            if mean["albedo_ncc"] < NCC_GATE:
                failures.append(f"task failed: albedo correlation {mean['albedo_ncc']:.3f} < {NCC_GATE}")
            values = dict(mean, peak_memory_mb=memory)
        if failures:
            values = dict(penalty)
        scores["experiments"][QUALITY_EXPERIMENT]["results"][name] = {
            "depth_mae_cm": round(values["depth_mae_cm"], 6),
            "albedo_ncc": round(values["albedo_ncc"], 6),
            "albedo_psnr_db": round(values["albedo_psnr_db"], 6),
        }
        scores["experiments"][MEMORY_EXPERIMENT]["results"][name] = {
            "peak_memory_mb": round(values["peak_memory_mb"], 3),
        }
        scores["_status"][name] = {"valid": not failures, "failures": failures,
                                   "scenes_completed": len(per_scene)}
        scores["_details"][name] = {
            sid: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}
            for sid, m in per_scene.items()
        }
    return scores


def evaluate(provider: SceneProvider, registry_path: Path, output_path: Path,
             keep_dir: Path | None = None, keep_predictions_under_outputs: bool = False,
             rescore_dir: Path | None = None, log=print) -> dict:
    scene_ids = [sid for sid, _ in provider.scenes]
    sizes = dict(provider.scenes)
    stats = []
    truths = {}
    for sid in scene_ids:
        truths[sid] = provider.ground_truth(sid)
        stats.append(scene_reference_stats(*truths[sid]))

    if rescore_dir is not None:
        records = json.loads((rescore_dir / "run_records.json").read_text())
        names = sorted(records["methods"])
        invalid = records.get("invalid", {})
        out_records: dict[str, dict] = {}
        for name in names:
            rec = {"failures": list(records["methods"][name]["failures"]), "scenes": {}}
            for sid, run in records["methods"][name]["scenes"].items():
                pred, err = load_prediction(rescore_dir / name / f"{sid}.npz", sizes[sid], provider.depth_max_m)
                if err:
                    rec["failures"].append(f"{sid}: {err}")
                    break
                metrics = scene_metrics(*pred, *truths[sid])
                metrics["peak_rss_mb"] = run["peak_rss_mb"]
                rec["scenes"][sid] = metrics
            out_records[name] = rec
        scores = summarize(names, invalid, out_records, stats, scene_ids)
        output_path.write_text(json.dumps(scores, indent=2) + "\n")
        return scores

    commands, invalid = load_registry(registry_path)
    names = sorted(commands)
    records: dict[str, dict] = {name: {"failures": [], "scenes": {}} for name in names}
    raw_runs: dict[str, dict] = {name: {"failures": [], "scenes": {}} for name in names}
    work = Path(tempfile.mkdtemp(prefix="nlos_eval_", dir=str(scratch_root())))
    try:
        for sid in scene_ids:
            active = [name for name in names if not records[name]["failures"]]
            if not active:
                break
            n = sizes[sid]
            scene_dir = provider.prepare(sid)
            log(f"[{sid}] n={n}: running {len(active)} method(s)")
            for name in active:
                out_dir = work / name
                out_dir.mkdir(parents=True, exist_ok=True)
                pred_path = out_dir / f"{sid}.npz"
                log_path = out_dir / f"{sid}.log"
                run = run_method(commands[name], scene_dir, pred_path, log_path)
                raw_runs[name]["scenes"][sid] = {k: run[k] for k in ("exit_code", "peak_rss_mb", "killed", "wall_time_s")}
                failure = None
                if not run["launched"]:
                    failure = f"could not launch command: {run['error']}"
                elif run["killed"] == "memory_budget_exceeded" or run["peak_rss_mb"] > MEMORY_BUDGET_MB:
                    failure = f"peak memory exceeded the {MEMORY_BUDGET_MB:.0f} MB budget"
                elif run["killed"] == "timeout":
                    failure = f"exceeded the {TIMEOUT_S_PER_SCENE:.0f} s per-scene time limit"
                elif run["exit_code"] != 0:
                    failure = f"exited with status {run['exit_code']}"
                pred = None
                if failure is None:
                    pred, err = load_prediction(pred_path, n, provider.depth_max_m)
                    if err:
                        failure = err
                if failure is not None:
                    records[name]["failures"].append(f"{sid}: {failure}")
                    raw_runs[name]["failures"].append(f"{sid}: {failure}")
                    tail = log_path.read_bytes()[-600:].decode("utf-8", "replace") if log_path.exists() else ""
                    log(f"  {name}: FAILED on {sid}: {failure}\n    log tail: {tail.strip()[-300:]}")
                    continue
                metrics = scene_metrics(*pred, *truths[sid])
                metrics["peak_rss_mb"] = run["peak_rss_mb"]
                records[name]["scenes"][sid] = metrics
                log(f"  {name}: depth={metrics['depth_mae_cm']:.3f}cm ncc={metrics['albedo_ncc']:.4f} "
                    f"psnr={metrics['albedo_psnr_db']:.2f}dB mem={run['peak_rss_mb']:.1f}MB t={run['wall_time_s']:.1f}s")
                if keep_dir is not None:
                    (keep_dir / name).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pred_path, keep_dir / name / f"{sid}.npz")
                if keep_predictions_under_outputs:
                    dest = ROOT / "outputs" / name / "train_predictions"
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pred_path, dest / f"{sid}.npz")
                    shutil.copy2(log_path, dest / f"{sid}.log")
                pred_path.unlink(missing_ok=True)
            provider.release(sid)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if keep_dir is not None:
        keep_dir.mkdir(parents=True, exist_ok=True)
        (keep_dir / "run_records.json").write_text(
            json.dumps({"methods": raw_runs, "invalid": invalid}, indent=2) + "\n")
    scores = summarize(names, invalid, records, stats, scene_ids)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scores, indent=2) + "\n")
    return scores


def print_summary(scores: dict, log=print) -> None:
    q = scores["experiments"][QUALITY_EXPERIMENT]["results"]
    m = scores["experiments"][MEMORY_EXPERIMENT]["results"]
    for name in sorted(q):
        st = scores["_status"][name]
        flag = "valid" if st["valid"] else "FAILED: " + "; ".join(st["failures"])[:200]
        log(f"{name}: depth_mae_cm={q[name]['depth_mae_cm']:.4f} albedo_ncc={q[name]['albedo_ncc']:.4f} "
            f"albedo_psnr_db={q[name]['albedo_psnr_db']:.3f} peak_memory_mb={m[name]['peak_memory_mb']:.2f} [{flag}]")
