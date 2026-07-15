#!/usr/bin/env bash
# FR-733 runner — classify a vulnerability description file (or stdin)
# and print only the answer. Every run is archived for crosscheck:
# full state dump + extracted classification JSON under
# logs/cwe-classifier/, keyed by input name and timestamp.
#
# Usage:
#   examples/cwe-classifier/classify.sh path/to/description.md
#   echo "Heap overflow in the parser" | examples/cwe-classifier/classify.sh
set -euo pipefail

# Read input BEFORE changing directory (arg paths are caller-relative).
if [[ $# -ge 1 ]]; then
  description="$(cat "$1")"
  name="$(basename "${1%.*}")"
else
  description="$(cat)"
  name="stdin"
fi

cd "$(dirname "$0")"

# Resolve the runner robustly: the venv console script can vanish for
# seconds during a parallel `pip install`, so prefer python -c on the
# venv interpreter, which survives reinstalls.
ROOT="$(cd ../.. && pwd)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  yg() { "$ROOT/.venv/bin/python" -c 'from yamlgraph.cli import main; main()' "$@"; }
else
  yg() { yamlgraph "$@"; }
fi

run_dir="../../logs/cwe-classifier"
mkdir -p "$run_dir"
stamp="$(date +%Y%m%d_%H%M%S)"
log="$run_dir/${name}-${stamp}.log"
result="$run_dir/${name}-${stamp}.result.json"

yg graph run graph.yaml \
  --var description="$description" --full > "$log" 2>&1 || {
    python3 nodes/show_result.py "$log" || true
    echo "full log: ${log#../../}" >&2
    exit 1
  }

python3 nodes/show_result.py --json "$log" > "$result"
python3 nodes/show_result.py "$log"
echo "run archived: ${log#../../} + $(basename "$result")"
