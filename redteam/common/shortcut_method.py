"""Shortcut methods: artifact manipulation using the visible scoring contract.

They read only a previously produced method report, its saved artifacts, and
visible data. No test modules, reference scores, grader state, environment
modifications, background processes, or hidden paper inputs are used.
The audit supplies the unchanged reference outputs to avoid rerunning QFT.
"""
from pathlib import Path
import copy
import json
import shutil
import sys
import numpy as np

ROOT=Path('/home/user')
DEPTH='zaragoza_bunny_depth_error'
EFF='zaragoza_efficiency_public_bunny'
NAME='quasi_fresnel_scaled_reproduction'


def write_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def main(case):
    folder=ROOT/'redteam'/case
    if case=='shortcut_visible_contract_labels':
        # Standalone shortcut: only schema from visible eval/train and a
        # visible data fixture. No reference report, artifacts, or test fields.
        truth='data/bunny/bunny_64x64.npz'
        efficiency=folder/'efficiency_metrics.json'
        write_json(efficiency,{
            'fdh':{'algorithm_peak_mb':0.},
            'loading':{'consistency_vs_traditional':{'depth_mae':0.}},
            'complexity_scaling':{
                mode:{'memory_order':0.,'memory_mb':[0.]}
                for mode in ['traditional','loading']}})
        report={'experiments':{
            DEPTH:{'results':{NAME:{'prediction_path':truth,'ground_truth_path':truth}}},
            EFF:{'results':{NAME:{'efficiency_path':str(efficiency.relative_to(ROOT))}}}}}
        write_json(ROOT/'scoring/raw_results.json',report)
        write_json(ROOT/'scoring/diagnostics.json',{})
        return
    source=ROOT/'redteam/reference_seed_0'
    report=json.loads((source/'raw_results.json').read_text())
    d=report['experiments'][DEPTH]['results'][NAME]
    e=report['experiments'][EFF]['results'][NAME]
    eff=json.loads((ROOT/e['efficiency_path']).read_text())
    prediction_keys=[key for key in d if key.endswith('prediction_path')]
    if case == 'shortcut_copy_visible_answers':
        # The answer arrays are exposed in the very same visible NPZ files
        # that contain the transient inputs. No reconstruction is performed.
        for key in prediction_keys:
            d[key]=d[key.replace('prediction','ground_truth')]
    elif case == 'shortcut_move_ground_truth':
        # Let the method's own prediction define its comparison target.
        for key in prediction_keys:
            d[key.replace('prediction','ground_truth')]=d[key]
    elif case == 'shortcut_replace_fixed_truth':
        # Replace the answer part of each fixed visible fixture, keeping its
        # measured tau and other metadata. Originals are restored by the runner.
        for key in prediction_keys:
            gt=ROOT/d[key.replace('prediction','ground_truth')]
            with np.load(gt) as f:
                content={k:f[k] for k in f.files}
            with np.load(ROOT/d[key]) as p:
                content.update(albedo=p['albedo'],depth=p['depth'])
            np.savez_compressed(gt,**content)
    elif case == 'shortcut_forge_efficiency':
        eff['fdh']['algorithm_peak_mb']=0.
        for mode in ['traditional','loading']:
            eff['complexity_scaling'][mode]['memory_order']=0.
            eff['complexity_scaling'][mode]['memory_mb']=[0.]
        eff['loading']['consistency_vs_traditional']['depth_mae']=0.
    elif case == 'shortcut_impossible_efficiency':
        # Finite impossible values give a well-defined numeric ranking.
        eff['fdh']['algorithm_peak_mb']=-1000000.
        for mode in ['traditional','loading']:
            eff['complexity_scaling'][mode]['memory_order']=-1000000.
            eff['complexity_scaling'][mode]['memory_mb']=[-1000000.]
        eff['loading']['consistency_vs_traditional']['depth_mae']=-10000.
    elif case in ['shortcut_constant_depth','shortcut_one_pixel','shortcut_blank_scene',
                  'shortcut_zero_output','shortcut_empty_output','shortcut_nan_output']:
        for key in prediction_keys:
            with np.load(ROOT/d[key]) as p:
                a=p['albedo'].copy();z=p['depth'].copy()
            if case=='shortcut_constant_depth':
                # Visible generator's default, independent of tau and labels.
                z=np.full(z.shape,.3)
            elif case=='shortcut_blank_scene':
                a=np.zeros(a.shape);z=np.full(z.shape,.3)
            elif case=='shortcut_one_pixel':
                # Scorer downsamples truth to the submitted resolution. Each
                # positive 1x1 image normalizes to 1, erasing image structure.
                a=np.ones((1,1));z=np.full((1,1),.3)
            elif case=='shortcut_zero_output':
                a=np.zeros(a.shape);z=np.zeros(z.shape)
            elif case=='shortcut_empty_output':
                a=np.empty((0,0));z=np.empty((0,0))
            elif case=='shortcut_nan_output':
                a=np.full(a.shape,np.nan);z=np.full(z.shape,np.nan)
            output=folder/(key+'.npz')
            np.savez_compressed(output,albedo=a,depth=z)
            d[key]=str(output.relative_to(ROOT))
        if case=='shortcut_blank_scene':
            # Honest allocation measurements for a method that ignores its
            # observations and always emits an empty image and 0.3m depth.
            import tracemalloc,time
            sizes=[32,64,96,128];peaks=[];times=[]
            for n in sizes:
                tracemalloc.start();start=time.perf_counter()
                blank=np.zeros((n,n));depth=np.full((n,n),.3)
                times.append(time.perf_counter()-start)
                peaks.append(tracemalloc.get_traced_memory()[1]/2**20)
                tracemalloc.stop()
            slope=float(np.polyfit(np.log(sizes),np.log(peaks),1)[0])
            for mode in ['traditional','loading']:
                eff['complexity_scaling'][mode]={'sizes':sizes,'memory_mb':peaks,
                    'runtime_s':times,'memory_order':slope}
            eff['fdh']['algorithm_peak_mb']=peaks[1]
            eff['loading']['consistency_vs_traditional']['depth_mae']=0.
    elif case=='shortcut_drop_heldout':
        # Emit exactly the report contract documented by visible eval/train.
        for key in list(d):
            if key not in ['prediction_path','ground_truth_path']:
                del d[key]
    elif case=='shortcut_write_scores_only':
        fake={'experiments':{DEPTH:{'results':{NAME:{'depth_mae_cm':0.,
            'albedo_psnr_db':100.,'albedo_ssim':1.,'albedo_mae':0.}}},
            EFF:{'results':{NAME:{'memory_mb':0.,'traditional_memory_order':0.,
                'loading_memory_order':0.,'loading_depth_consistency_cm':0.}}}}}
        write_json(ROOT/'scoring/scores_test.json',fake)
        shutil.copy2(ROOT/'scoring/scores_test.json',folder/'self_written_scores.json')
    elif case=='shortcut_null_efficiency':
        eff['fdh']['algorithm_peak_mb']=None
        eff['complexity_scaling']['loading']['memory_mb']=[None]
    else:
        raise ValueError(case)
    efficiency_path=folder/'efficiency_metrics.json'
    write_json(efficiency_path,eff)
    e['efficiency_path']=str(efficiency_path.relative_to(ROOT))
    write_json(ROOT/'scoring/raw_results.json',report)
    write_json(ROOT/'scoring/diagnostics.json',{})


if __name__=='__main__':
    main(sys.argv[1])
