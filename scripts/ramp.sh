#!/usr/bin/env bash
# FR-865: ramp installer entry point. Thin wrapper — all logic and
# manifest validation live in scripts/ramp_installer.py.
set -euo pipefail
exec python3 "$(dirname "$0")/ramp_installer.py" "$@"
