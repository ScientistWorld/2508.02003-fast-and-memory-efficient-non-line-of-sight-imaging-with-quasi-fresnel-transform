#!/bin/bash
# Job script: Comprehensive evaluation of improved QFT algorithm.
# Tests on multiple scenes with s-parameter search and baseline comparisons.
set -e

cd /home/user

# Disable threading for consistency
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "=== Step 1: Generate synthetic NLOS data ==="

python3 data/generate_nlos_data.py --scene shapes --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/shapes
python3 data/generate_nlos_data.py --scene kylin --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/kylin
python3 data/generate_nlos_data.py --scene bunny --resolution 64 --bins 256 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/bunny
python3 data/generate_nlos_data.py --scene dynamic --resolution 32 --bins 128 --area 0.3 --dt 0.003 --depth 0.15 --k 4 --save --output data/dynamic

echo ""
echo "=== Step 2: Convert Zaragoza real data (if available) ==="
python3 -c "
try:
    import h5py
    import os
    zaragoza_dir = 'data/zaragoza'
    hdf5_files = [f for f in os.listdir(zaragoza_dir) if f.endswith('.hdf5')]
    if hdf5_files:
        from data.load_zaragoza import convert_zaragoza_to_npz
        for f in hdf5_files:
            path = os.path.join(zaragoza_dir, f)
            print(f'Converting {path}...')
            convert_zaragoza_to_npz(path)
    else:
        print('No HDF5 files found in zaragoza dir')
except ImportError:
    print('h5py not available, skipping Zaragoza data conversion')
"

echo ""
echo "=== Step 3: Comprehensive evaluation ==="
python3 scripts/evaluate_nlos.py