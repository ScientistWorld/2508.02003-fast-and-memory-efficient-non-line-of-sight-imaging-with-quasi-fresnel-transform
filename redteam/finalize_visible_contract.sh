#!/bin/bash
set -euo pipefail
cd /home/user
bash redteam/shortcut_visible_contract_labels/run.sh
python3 redteam/summarize.py
