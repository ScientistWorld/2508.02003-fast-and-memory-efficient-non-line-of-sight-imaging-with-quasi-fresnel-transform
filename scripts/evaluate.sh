#!/bin/bash
# Standard evaluation entrypoint.
# Runs the honest paper-aligned evaluation currently supported by this workspace:
# 1) real Zaragoza-style sample efficiency benchmark
# 2) synthetic sanity-check reconstruction
set -euo pipefail

cd /home/user
python3 scripts/evaluate_nlos.py
