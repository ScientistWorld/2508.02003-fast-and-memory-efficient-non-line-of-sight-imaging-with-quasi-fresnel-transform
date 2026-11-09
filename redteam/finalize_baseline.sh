#!/bin/bash
set -euo pipefail
cd /home/user
date -u +'%Y-%m-%dT%H:%M:%SZ' > redteam/baseline_followup_started.txt
bash redteam/simple_peak_baseline/run.sh
python3 redteam/summarize.py
date -u +'%Y-%m-%dT%H:%M:%SZ' > redteam/baseline_followup_completed.txt
