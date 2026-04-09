#!/bin/bash
# Download helper for public NLOS resources.
#
# Estimated download size from this script as currently written: about 2.1 MB
# Estimated extra disk usage: about 2.1 MB
#
# Notes:
# - The workspace already includes one bundled Zaragoza-style bunny sample at
#   /home/user/data/zaragoza/bunny_conf64.{hdf5,npz}
# - This script fetches one additional lightweight public confocal Zaragoza
#   scene so evaluation can run on more than one public scene without pulling
#   the much larger 256x256 files by default.
# - Larger public files are available from https://graphics.unizar.es/nlos_dataset.html
set -euo pipefail

cd /home/user
mkdir -p data/zaragoza/public shared/datasets

download_if_missing() {
    local output_path="$1"
    local url="$2"
    if [ -f "$output_path" ]; then
        echo "Already present: $output_path"
        return 0
    fi
    curl -g -L --fail --output "$output_path" "$url"
}

echo "Bundled data present:"
ls -1 data/zaragoza || true

download_if_missing \
    "data/zaragoza/public/T_conf64.hdf5" \
    "https://nas-graphics.unizar.es/s/2019_Z_NLOS_Dataset_backup/download?path=%2Fsimple&files=T_l[0.00,-0.50,0.00]_r[1.57,0.00,3.14]_v[0.20]_s[64]_l[64]_gs[0.60]_conf.hdf5"

echo "Additional public data present:"
ls -1 data/zaragoza/public || true
