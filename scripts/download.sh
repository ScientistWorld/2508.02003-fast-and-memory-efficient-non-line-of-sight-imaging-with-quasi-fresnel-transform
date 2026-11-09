#!/bin/bash
# Download helper.
#
# The scored benchmark needs no downloads: visible train scenes are rendered
# deterministically by `python3 data/nlos_scenes.py --write-train` (also done
# automatically by scripts/evaluate_train.sh), and hidden test scenes are
# rendered inside eval/test/ at test time.  Python packages come from
# environment/setup.sh.
#
# Optional (not scored): public Zaragoza NLOS confocal measurements for
# qualitative experiments (they carry no 2D albedo/depth ground truth).
#   bash scripts/download.sh --public-zaragoza     # ~750 MB into data/zaragoza_public/
# Loader: data/load_zaragoza.py.  Source: https://graphics.unizar.es/nlos_dataset.html
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

if [ "${1:-}" != "--public-zaragoza" ]; then
    echo "Nothing to download for the scored benchmark."
    echo "Rendering the visible train scenes (deterministic, cached in data/train_scenes/) ..."
    python3 data/nlos_scenes.py --write-train
    echo "Optional public Zaragoza scenes: bash scripts/download.sh --public-zaragoza"
    exit 0
fi

download_if_missing() {
    local output_path="$1"
    local url="$2"
    if [ -f "$output_path" ]; then
        echo "Already present: $output_path"
        return 0
    fi
    mkdir -p "$(dirname "$output_path")"
    curl -g -L --fail --output "$output_path" "$url"
}

download_if_missing \
    "data/zaragoza_public/bunny_simple_256_conf.hdf5" \
    "https://nas-graphics.unizar.es/public.php/dav/files/2019_Z_NLOS_Dataset_backup/simple/bunny_l%5b0.00%2c-0.50%2c0.00%5d_r%5b1.57%2c0.00%2c3.14%5d_v%5b0.80%2c0.53%2c0.81%5d_s%5b256%5d_l%5b256%5d_gs%5b1.00%5d_conf.hdf5"

download_if_missing \
    "data/zaragoza_public/usaf_simple_256_conf.hdf5" \
    "https://nas-graphics.unizar.es/public.php/dav/files/2019_Z_NLOS_Dataset_backup/simple/usaf_l%5b0.00%2c-0.50%2c0.00%5d_r%5b1.57%2c0.00%2c3.14%5d_v%5b0.57%2c0.01%2c0.60%5d_s%5b256%5d_l%5b256%5d_gs%5b1.00%5d_conf.hdf5"

ls -la data/zaragoza_public/
