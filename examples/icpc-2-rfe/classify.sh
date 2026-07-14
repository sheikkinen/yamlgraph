#!/usr/bin/env bash
# FR-722 runner — classify a transcript file (or stdin) and print only
# the answer. Every run is archived for crosscheck: full state dump +
# extracted classification JSON under logs/icpc2-rfe/, keyed by input
# name and timestamp (verdicts vary run-to-run; history is the audit).
#
# Usage:
#   examples/icpc-2-rfe/classify.sh path/to/transcript.md
#   echo "Patient calls about a rash" | examples/icpc-2-rfe/classify.sh
set -euo pipefail

# Read input BEFORE changing directory (arg paths are caller-relative).
if [[ $# -ge 1 ]]; then
  transcript="$(cat "$1")"
  name="$(basename "${1%.*}")"
else
  transcript="$(cat)"
  name="stdin"
fi

cd "$(dirname "$0")"

# Resolve the runner robustly: the venv console script can vanish for
# seconds during a parallel `pip install` (observed: intermittent
# "command not found" mid-baseline), so prefer python -c on the venv
# interpreter, which survives reinstalls.
ROOT="$(cd ../.. && pwd)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  yg() { "$ROOT/.venv/bin/python" -c 'from yamlgraph.cli import main; main()' "$@"; }
else
  yg() { yamlgraph "$@"; }
fi

run_dir="../../logs/icpc2-rfe"
mkdir -p "$run_dir"
stamp="$(date +%Y%m%d_%H%M%S)"
log="$run_dir/${name}-${stamp}.log"
result="$run_dir/${name}-${stamp}.result.json"

yg graph run graph.yaml \
  --var transcript="$transcript" --full > "$log" 2>&1 || {
    python3 nodes/show_result.py "$log" || true
    echo "full log: ${log#../../}" >&2
    exit 1
  }

python3 nodes/show_result.py --json "$log" > "$result"
python3 nodes/show_result.py "$log"
echo "run archived: ${log#../../} + $(basename "$result")"
