#!/usr/bin/env bash
set -euo pipefail
exec bash "$(cd "$(dirname "$0")" && pwd)/ops/run_gpu_pipeline.sh" "$@"
