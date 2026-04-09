#!/bin/bash
# Download helper for public NLOS resources.
#
# Estimated download size from this script as currently written: 0 MB
# Estimated extra disk usage: 0 MB
#
# Notes:
# - The workspace already includes one bundled Zaragoza-style sample at
#   /home/user/data/zaragoza/bunny_conf64.{hdf5,npz}
# - Official public resources identified for later expansion:
#   https://graphics.unizar.es/nlos_dataset.html
#   https://github.com/computational-imaging/nlos-fk
#
# This script is intentionally idempotent and lightweight until a concrete
# downloader is added for the larger public datasets.
set -euo pipefail

cd /home/user
mkdir -p data/zaragoza shared/datasets

echo "Bundled data present:"
ls -1 data/zaragoza || true
echo "No additional downloads performed."
