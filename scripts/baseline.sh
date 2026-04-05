#!/bin/bash
# Baseline evaluation script.
set -e

cd /home/user

METHOD=${1:-fbp}
DATA_DIR=${2:-/home/user/data/kylin}

echo "Running $METHOD baseline on $DATA_DIR..."
bash scripts/evaluate.sh $METHOD $DATA_DIR
