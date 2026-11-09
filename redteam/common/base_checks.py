"""Run reference and genuine variants through the original benchmark driver.

This is audit-only orchestration, not an input read by any shortcut method.
All evaluator files and evaluation processes remain unmodified.
"""
from pathlib import Path
import importlib.util
import numpy as np
import sys
import time
import json

ROOT = Path('/home/user')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'redteam/common'))


def main(case):
    import scripts.evaluate_nlos as driver
    import method.quasi_fresnel as qft
    seed = int(case.rsplit('_',1)[-1]) if case.startswith('reference_seed_') else 0
    np.random.seed(seed)
    if case == 'stronger_exact_sums':
        import stronger
        qft.quasi_fresnel_time_integral = stronger.quasi_fresnel_time_integral
        qft.quasi_fresnel_time_integral_loading = stronger.quasi_fresnel_time_integral_loading
        driver.quasi_fresnel_time_integral = stronger.quasi_fresnel_time_integral
        driver.quasi_fresnel_time_integral_loading = stronger.quasi_fresnel_time_integral_loading
    elif case == 'weaker_no_spatial':
        def no_spatial(phi, s, area=None, wall_x=None, wall_y=None):
            return phi
        qft.quasi_fresnel_spatial_deconv = no_spatial
    elif case == 'simple_peak_baseline':
        def peak(tau, s, dt, k=4, area=None, wall_x=None, wall_y=None,
                 integration_mode='traditional', use_fdh=False):
            return np.sum(tau,axis=2), (np.argmax(tau,axis=2)+0.5)*dt
        driver.quasi_fresnel_reconstruct = peak
    elif case == 'bruteforce_all_voxels':
        import bruteforce
        # JIT warmup is recorded separately, not hidden in method timing.
        t0=time.perf_counter()
        bruteforce.exhaustive(np.ones((2,2,2)), .3, .003, 4)
        (ROOT/'redteam'/case/'jit.json').write_text(json.dumps({'warmup_seconds':time.perf_counter()-t0}))
        driver.quasi_fresnel_reconstruct = bruteforce.reconstruct
        original_benchmark=driver.benchmark_qft
        def once(*args,**kwargs):
            kwargs['repeats']=1
            return original_benchmark(*args,**kwargs)
        driver.benchmark_qft=once
        # The exhaustive baseline has no QFT integration complexity experiment.
        # Measure its actual full reconstruction on the same four scaling sizes.
        def actual_scaling(sizes=(32,64,96,128),s=.02,dt=.003,k=4):
            import tracemalloc
            times=[];peaks=[]
            for n in sizes:
                tau=np.random.default_rng(250802003).random((n,n,n))
                tracemalloc.start();start=time.perf_counter()
                bruteforce.reconstruct(tau,s,dt,k,area=1.)
                times.append(time.perf_counter()-start)
                peaks.append(tracemalloc.get_traced_memory()[1]/2**20)
                tracemalloc.stop()
                print('exhaustive scaling',n,times[-1],peaks[-1],flush=True)
            d={'sizes':list(sizes),'runtime_s':times,'memory_mb':peaks,
               'runtime_order':driver._fit_scaling_order(list(sizes),times),
               'memory_order':driver._fit_scaling_order(list(sizes),peaks)}
            return {'traditional':d,'loading':d.copy()}
        driver.benchmark_complexity_scaling=actual_scaling
    driver.main()


if __name__ == '__main__':
    main(sys.argv[1])
