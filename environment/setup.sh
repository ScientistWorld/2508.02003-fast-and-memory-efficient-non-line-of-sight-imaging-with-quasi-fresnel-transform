#!/bin/bash
# Install Python packages into the container overlay.
set -e

uv pip install --system numpy scipy numba Pillow
