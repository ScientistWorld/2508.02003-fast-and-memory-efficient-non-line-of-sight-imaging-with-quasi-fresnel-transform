#!/bin/bash
set -euo pipefail
cd /home/user
bash redteam/simple_peak_baseline/run.sh
python3 redteam/summarize.py
