"""Install one candidate, exit its process, run unmodified test with no args.

This runner changes only authorized method/artifact inputs. It never modifies
eval, evaluator imports, Python environment, or evaluation shell scripts.
Every changed non-audit file is restored in finally, including ignored outputs.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT=Path('/home/user')
sys.path.insert(0,str(ROOT/'redteam/common'))
NAME='quasi_fresnel_scaled_reproduction'


def capture(folder):
    for name in ['raw_results.json','diagnostics.json','scores_train.json','scores_test.json']:
        path=ROOT/'scoring'/name
        if path.exists():
            shutil.copy2(path,folder/name)
    report_path=folder/'raw_results.json'
    if not report_path.exists():
        return
    report=json.loads(report_path.read_text())
    for exp in report['experiments'].values():
        for payload in exp['results'].values():
            for key,value in list(payload.items()):
                if key.endswith('_path') and value.startswith('outputs/'):
                    source=ROOT/value
                    dest=folder/'artifacts'/source.name
                    dest.parent.mkdir(exist_ok=True)
                    shutil.copy2(source,dest)
                    payload[key]=str(dest.relative_to(ROOT))
    report_path.write_text(json.dumps(report,indent=2)+'\n')


def main(case):
    folder=ROOT/'redteam'/case
    folder.mkdir(exist_ok=True,parents=True)
    backup=folder/'restore'
    backup.mkdir(exist_ok=True)
    relative=['method/redteam_shortcut.py']
    relative += [str(p.relative_to(ROOT)) for p in (ROOT/'scoring').glob('*.json')]
    relative += [str(p.relative_to(ROOT)) for p in (ROOT/'outputs'/NAME).glob('*') if p.is_file()]
    if case=='shortcut_replace_fixed_truth':
        relative += ['data/bunny/bunny_64x64.npz','data/shapes/shapes_64x64.npz']
    existed={}
    for rel in relative:
        p=ROOT/rel; existed[rel]=p.exists()
        if p.exists():
            out=backup/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
    environment=os.environ.copy()
    # No evaluation overrides survive a fresh-container test.
    for key in ['DIAGNOSTICS_PATH','TRAIN_SCORES_PATH','PYTHONPATH','PYTHONSTARTUP']:
        environment.pop(key,None)
    for key in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        environment[key]='1'
    environment['NUMBA_NUM_THREADS']='4'
    status={'case':case,'started':time.time(),'test_command':['bash','scripts/evaluate_test.sh'],
            'fresh_process':True,'evaluator_sha256':hashlib.sha256((ROOT/'eval/test/score_nlos_test.py').read_bytes()).hexdigest()}
    def run(command,label):
        with (folder/(label+'.log')).open('w') as handle:
            result=subprocess.run(command,cwd=ROOT,env=environment,stdout=handle,stderr=subprocess.STDOUT)
        status[label+'_exit_code']=result.returncode
        return result.returncode
    try:
        if case.startswith('shortcut_'):
            shutil.copy2(ROOT/'redteam/common/shortcut_method.py',ROOT/'method/redteam_shortcut.py')
            code=run(['python3','method/redteam_shortcut.py',case],'method')
        else:
            code=run(['python3','redteam/common/base_checks.py',case],'method')
        if code:
            return
        # Check train without leaving stale method keys if train rejects a case.
        (ROOT/'scoring/scores_train.json').unlink(missing_ok=True)
        run(['bash','scripts/evaluate_train.sh'],'train')
        # Remove old scores so a failed test cannot be mistaken for a result.
        # Retain the explicit score-writing shortcut until test overwrites it.
        if case!='shortcut_write_scores_only':
            (ROOT/'scoring/scores_test.json').unlink(missing_ok=True)
        run(['bash','scripts/evaluate_test.sh'],'test')
        capture(folder)
    finally:
        status['seconds']=time.time()-status['started']
        (folder/'status.json').write_text(json.dumps(status,indent=2)+'\n')
        for rel,was_present in existed.items():
            path=ROOT/rel
            if was_present:
                shutil.copy2(backup/rel,path)
            else:
                path.unlink(missing_ok=True)
        shutil.rmtree(backup)
        print(case,json.dumps(status),flush=True)


if __name__=='__main__':
    main(sys.argv[1])
