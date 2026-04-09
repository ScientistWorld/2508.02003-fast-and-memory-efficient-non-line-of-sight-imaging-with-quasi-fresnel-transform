#!/bin/bash
# End-to-end reproduction entrypoint for the current workspace state.
# This runs the packaged method benchmarks and then scores the emitted report.
set -euo pipefail

cd /home/user
bash scripts/method.sh
