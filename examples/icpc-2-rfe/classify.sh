#!/usr/bin/env bash
# FR-722 runner — classify a transcript file (or stdin) and print only
# the answer. The --full state dump goes to logs/ for forensics.
#
# Usage:
#   examples/icpc-2-rfe/classify.sh path/to/transcript.md
#   echo "Patient calls about a rash" | examples/icpc-2-rfe/classify.sh
set -euo pipefail

# Read input BEFORE changing directory (arg paths are caller-relative).
if [[ $# -ge 1 ]]; then
  transcript="$(cat "$1")"
else
  transcript="$(cat)"
fi

cd "$(dirname "$0")"

mkdir -p ../../logs
log="../../logs/icpc2-rfe-last-run.log"

yamlgraph graph run graph.yaml \
  --var transcript="$transcript" --full > "$log" 2>&1 || {
    python3 nodes/show_result.py "$log" || true
    echo "full log: logs/icpc2-rfe-last-run.log" >&2
    exit 1
  }

python3 nodes/show_result.py "$log"
