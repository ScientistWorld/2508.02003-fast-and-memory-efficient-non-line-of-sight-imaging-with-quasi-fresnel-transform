"""Audit ranking calculation. Never imported by candidate methods or scorers."""
from pathlib import Path
import json
import math
import numpy as np

ROOT=Path('/home/user/redteam')
NAME='quasi_fresnel_scaled_reproduction'
contract=json.loads((ROOT/'original/scoring/reference.json').read_text())['experiments']
columns=[(e,m) for e,p in contract.items() for m in p['metrics']]
weights=np.array([contract[e]['weight']*abs(contract[e]['metrics'][m]['coefficient']) for e,m in columns])
directions=np.array([1 if contract[e]['metrics'][m]['higher_is_better'] else -1 for e,m in columns])


def vector(path):
    scores=json.loads(path.read_text())['experiments']
    return np.array([scores[e]['results'][NAME][m] for e,m in columns],dtype=float)


def main():
    original=vector(ROOT/'original/scoring/scores_test.json')
    rows={}
    for status_path in sorted(ROOT.glob('*/status.json')):
        folder=status_path.parent
        status=json.loads(status_path.read_text())
        row={'status':status}
        if status.get('test_exit_code')==0:
            v=vector(folder/'scores_test.json')
            row['metrics']=v.tolist()
            row['finite']=bool(np.isfinite(v).all())
        rows[folder.name]=row
    finite={k:np.array(v['metrics']) for k,v in rows.items() if v.get('finite')}
    # The actual future-attempt distribution is unknown. Give explicit cohorts
    # and dominance, not a false universal scalar rank.
    cohorts={'all_finite_audit_attempts':list(finite),
             'base_checks':[k for k in finite if not k.startswith('shortcut_')]}
    stats={}
    for cohort,names in cohorts.items():
        sd=np.std(np.array([original]+[finite[k] for k in names]),axis=0)
        safe=np.where(sd>0,sd,1.)
        stats[cohort]={'attempts':['stored_reference']+names,'std':sd.tolist()}
        for k,v in finite.items():
            delta=weights*directions*(v-original)/safe
            delta=np.where(sd>0,delta,0.)
            rows[k].setdefault('rank_delta',{})[cohort]=float(delta.sum())
    for k,v in finite.items():
        imp=directions*(v-original)
        rows[k]['pareto_vs_stored_reference']=('strictly_better' if np.all(imp>=0) and np.any(imp>0)
            else 'tie' if np.all(imp==0) else 'strictly_worse' if np.all(imp<=0) else 'tradeoff')
        pair_sd=np.abs(v-original)/2
        rows[k]['pairwise_rank_delta']=float(np.sum(weights*directions*np.divide(v-original,pair_sd,
                    out=np.zeros(len(v)),where=pair_sd>0)))
    seeds=np.array([finite['reference_seed_'+str(i)] for i in range(3) if 'reference_seed_'+str(i) in finite])
    output={'columns':[{'experiment':e,'metric':m,'weight':float(w),'direction':int(d)}
            for (e,m),w,d in zip(columns,weights,directions)],
            'stored_reference':original.tolist(),'cohorts':stats,'cases':rows,
            'seed_range':(np.max(seeds,axis=0)-np.min(seeds,axis=0)).tolist() if len(seeds) else None}
    (ROOT/'summary.json').write_text(json.dumps(output,indent=2,allow_nan=True)+'\n')
    lines=['| Case | Depth cm | PSNR | SSIM | Albedo MAE | Memory MB | Direct order | Loading order | Disagreement cm | Audit Δrank | Pareto |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
           '| stored_reference | '+' | '.join(f'{x:.6g}' for x in original)+' | 0 | reference |']
    for name,row in rows.items():
        vals=row.get('metrics')
        if vals is None:
            lines.append('| '+name+' | test rejected |'+ ' |'*9)
        else:
            lines.append('| '+name+' | '+' | '.join(f'{x:.6g}' for x in vals)+' | '+
                (f"{row['rank_delta']['all_finite_audit_attempts']:+.6f}" if row.get('finite') else 'nonfinite')+' | '+
                row.get('pareto_vs_stored_reference','undefined')+' |')
    (ROOT/'scores_table.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines),flush=True)


if __name__=='__main__':
    main()
