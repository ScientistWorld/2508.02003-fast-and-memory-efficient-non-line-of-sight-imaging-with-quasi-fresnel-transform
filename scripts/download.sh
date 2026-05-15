#!/bin/bash
# Download helper for public NLOS resources.
#
# Estimated download size from this script as currently written: about 722 MB
# Estimated extra disk usage: about 722 MB
#
# Notes:
# - The scored benchmark uses the public Zaragoza Stanford bunny confocal file.
# - This script also fetches a public Zaragoza USAF confocal file for
#   extra diagnostics and a lightweight T scene.
# - Larger public files are available from https://graphics.unizar.es/nlos_dataset.html
set -euo pipefail

cd /home/user
mkdir -p data/downloads/zaragoza/public

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
    "data/downloads/zaragoza/bunny_simple_256_conf.hdf5" \
    "https://nas-graphics.unizar.es/public.php/dav/files/2019_Z_NLOS_Dataset_backup/simple/bunny_l%5b0.00%2c-0.50%2c0.00%5d_r%5b1.57%2c0.00%2c3.14%5d_v%5b0.80%2c0.53%2c0.81%5d_s%5b256%5d_l%5b256%5d_gs%5b1.00%5d_conf.hdf5"

download_if_missing \
    "data/downloads/zaragoza/usaf_simple_256_conf.hdf5" \
    "https://nas-graphics.unizar.es/public.php/dav/files/2019_Z_NLOS_Dataset_backup/simple/usaf_l%5b0.00%2c-0.50%2c0.00%5d_r%5b1.57%2c0.00%2c3.14%5d_v%5b0.57%2c0.01%2c0.60%5d_s%5b256%5d_l%5b256%5d_gs%5b1.00%5d_conf.hdf5"

download_if_missing \
    "data/downloads/zaragoza/public/T_conf64.hdf5" \
    "https://nas-graphics.unizar.es/s/2019_Z_NLOS_Dataset_backup/download?path=%2Fsimple&files=T_l[0.00,-0.50,0.00]_r[1.57,0.00,3.14]_v[0.20]_s[64]_l[64]_gs[0.60]_conf.hdf5"

echo "Additional public data present:"
ls -1 data/downloads/zaragoza data/downloads/zaragoza/public || true
