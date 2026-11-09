"""Small, standard-library audit ranking calculation; never a scorer input."""
from pathlib import Path
import json
import math
import statistics

ROOT = Path('/home/user/redteam')
NAME = 'quasi_fresnel_scaled_reproduction'
contract = json.loads((ROOT/'original/scoring/reference.json').read_text())['experiments']
columns = [(e, m) for e, p in contract.items() for m in p['metrics']]
weights = [contract[e]['weight']*abs(contract[e]['metrics'][m]['coefficient']) for e, m in columns]
directions = [1 if contract[e]['metrics'][m]['higher_is_better'] else -1 for e, m in columns]


def vector(path):
    scores = json.loads(path.read_text())['experiments']
    return [float(scores[e]['results'][NAME][m]) for e, m in columns]


def scales(population):
    return [statistics.pstdev(values) for values in zip(*population)]


def delta_rank(values, original, sd):
    return sum(w*d*(v-r)/s if s else 0.0
               for w, d, v, r, s in zip(weights, directions, values, original, sd))


def main():
    original = vector(ROOT/'original/scoring/scores_test.json')
    rows = {}
    for status_path in sorted(ROOT.glob('*/status.json')):
        folder = status_path.parent
        status = json.loads(status_path.read_text())
        row = {'status': status}
        if status.get('test_exit_code') == 0:
            values = vector(folder/'scores_test.json')
            row.update(metrics=values, finite=all(math.isfinite(v) for v in values))
        rows[folder.name] = row
    finite = {k: row['metrics'] for k, row in rows.items() if row.get('finite')}
    cohorts = {'all_finite_audit_attempts': list(finite),
               'base_checks': [k for k in finite if not k.startswith('shortcut_')]}
    stats = {}
    for cohort, names in cohorts.items():
        sd = scales([original]+[finite[k] for k in names])
        stats[cohort] = {'attempts': ['stored_reference']+names, 'std': sd}
        for k, values in finite.items():
            if k not in names:
                continue
            rows[k].setdefault('rank_delta', {})[cohort] = delta_rank(values, original, sd)
    for k, values in finite.items():
        # Include each candidate in its own population, so a zero-variance
        # metric in the base cohort becomes active if this candidate changes it.
        names = cohorts['base_checks'].copy()
        if k not in names:
            names.append(k)
        sd = scales([original]+[finite[n] for n in names])
        rows[k]['rank_delta']['base_plus_case'] = delta_rank(values, original, sd)
        rows[k]['base_plus_case_cohort'] = {'attempts': ['stored_reference']+names, 'std': sd}
        improvement = [d*(v-r) for d, v, r in zip(directions, values, original)]
        rows[k]['pareto_vs_stored_reference'] = (
            'tie' if all(x == 0 for x in improvement) else
            'strictly_better' if all(x >= 0 for x in improvement) else
            'strictly_worse' if all(x <= 0 for x in improvement) else 'tradeoff')
        rows[k]['pairwise_rank_delta'] = sum(
            2*w*(1 if x > 0 else -1 if x < 0 else 0)
            for w, x in zip(weights, improvement))
    seeds = [finite['reference_seed_'+str(i)] for i in range(3)]
    output = {'columns': [{'experiment': e, 'metric': m, 'weight': w, 'direction': d}
                         for (e, m), w, d in zip(columns, weights, directions)],
              'stored_reference': original, 'cohorts': stats, 'cases': rows,
              'seed_range': [max(v)-min(v) for v in zip(*seeds)]}
    (ROOT/'summary.json').write_text(json.dumps(output, indent=2, allow_nan=True)+'\n')
    lines = [
        '| Case | Depth cm | PSNR | SSIM | Albedo MAE | Memory MB | Direct order | Loading order | Disagreement cm | All-finite Δrank | Base + case Δrank | Pareto |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
        '| stored_reference | '+' | '.join(f'{x:.6g}' for x in original)+' | 0 | 0 | reference |']
    for name, row in rows.items():
        values = row.get('metrics')
        if values is None:
            lines.append('| '+name+' | test rejected |'+' |'*10)
            continue
        ranks = [(f"{row['rank_delta'][cohort]:+.6f}" if row.get('finite') else 'nonfinite')
                 for cohort in ['all_finite_audit_attempts', 'base_plus_case']]
        lines.append('| '+name+' | '+' | '.join(f'{x:.6g}' for x in values)+' | '+
                     ' | '.join(ranks)+' | '+row.get('pareto_vs_stored_reference', 'undefined')+' |')
    (ROOT/'scores_table.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines), flush=True)


if __name__ == '__main__':
    main()
