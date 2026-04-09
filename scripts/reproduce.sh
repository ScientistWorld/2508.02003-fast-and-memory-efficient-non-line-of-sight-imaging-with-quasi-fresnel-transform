#!/bin/bash
# End-to-end reproduction entrypoint for the current workspace state.
# This runs the packaged evaluation on the bundled real sample and synthetic sanity check.
set -euo pipefail

cd /home/user
bash scripts/evaluate.sh
