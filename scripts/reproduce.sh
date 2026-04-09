#!/bin/bash
# End-to-end reproduction script.
# Runs the full pipeline: generate synthetic data, run method and baselines, evaluate.
set -e

cd /home/user

echo "=== Step 1: Generate synthetic NLOS data ==="
bash scripts/download.sh

echo ""
echo "=== Step 2: Run Quasi-Fresnel Transform method ==="
# Use shapes scene for evaluation
bash scripts/evaluate.sh quasi_fresnel /home/user/data/shapes 0.025

echo ""
echo "=== Step 3: Run baseline methods ==="
bash scripts/baseline.sh fbp /home/user/data/shapes
bash scripts/baseline.sh lct /home/user/data/shapes

echo ""
echo "=== Reproduction complete ==="
echo "Results saved to scoring/scores.json"
echo ""
echo "Compare your results against the paper:"
python3 validate.py --compare
