# Gym scoring audit

Run `bash redteam/run_all.sh` as a CPU job. Each case has its own `run.sh` and
writes `method.log`, `train.log`, `test.log`, `status.json`, `scores_train.json`
and `scores_test.json` when accepted. The hidden command is always exactly
`bash scripts/evaluate_test.sh`, with no arguments, after the candidate exits.
The evaluator files and Python environment are never edited. All non-audit
inputs changed for a case are restored, even if evaluation rejects it.

The original benchmark runner is used only for the base checks. Shortcut
methods use saved outputs of their preceding reproduction (explicitly permitted
by the audit instructions), the visible train artifact contract, and `data/`.
No shortcut reads `eval/test/`, the paper, hidden scores, or hidden reference
metadata. Unchanged reference artifacts are reused, not recomputed. The supplied
reference report carries prediction and ground-truth path pairs; shortcut code
handles those pairs generically. `shortcut_drop_heldout` emits only the fields
required by the visible train contract.

`shortcut_visible_contract_labels` independently proves the information path
without any saved reference report or artifacts: it writes the visible train
schema, points prediction and truth to the visible bunny labels, and declares
zero efficiency costs. It uses no optional held-out report fields.

Both independent baselines measure their own full reconstruction allocations
on the same scaling sizes. A follow-up job corrected an initial simple-baseline
run that had retained the reference integration-only efficiency benchmark.
The saved final scores contain the corrected measurements.

`summary.json` records every metric and explicitly specified rank-normalization
cohorts, including the base cohort augmented by the candidate before its
standard deviations are recomputed. A future ranking's normalization depends on other submitted attempts,
so no universal scalar rank exists. Pareto improvements are independent of this
unknown normalization. The coefficient sign is ignored and `higher_is_better`
sets direction, as in the audit specification. Rejected and nonfinite outputs
are never treated as a finite winning rank.

`original/` preserves the starting fixtures needed for restoring and comparing
this audit. It is audit-only and is never read by shortcut methods.

Refresh the standard-library summaries with `python3 redteam/summarize.py` and
`python3 redteam/write_report.py`. Full job logs are under `job_logs/`.
