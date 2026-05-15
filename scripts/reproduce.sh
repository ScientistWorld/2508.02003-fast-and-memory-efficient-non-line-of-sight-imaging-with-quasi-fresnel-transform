#!/bin/bash
# End-to-end reproduction entrypoint for the current workspace state.
# This runs the packaged method benchmarks and then scores the emitted report.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"
bash scripts/method.sh
