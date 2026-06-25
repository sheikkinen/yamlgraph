#!/usr/bin/env bash
# FR-591 spike driver — per-character L5 multi-perspective conversion.
#
# Replaces the retired Python harness (spike_perspective.py): the conversion now
# lives in the graphs (perspective_l5.yaml + perspective_agent.yaml), so the
# spike is just orchestration — run the graph over every fixture, then dissect
# the result with the unchanged confusion x-ray. The encode contract is
# PROVISIONAL (recall-preserving, precision-open — FR-591 J1).
#
# Usage:
#   examples/plot_modeller/spike_perspective.sh            # all genres
#   examples/plot_modeller/spike_perspective.sh detective  # one genre
#
# Env: reads .env for ANTHROPIC_API_KEY etc.; PROVIDER/ANTHROPIC_MODEL select
# the model (defaults: anthropic / claude-haiku-4-5).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Capture caller-provided overrides before .env clobbers them.
_CALLER_PROVIDER="${PROVIDER:-}"
_CALLER_MODEL="${ANTHROPIC_MODEL:-}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PYTHON="${PYTHON:-.venv/bin/python}"
export PROVIDER="${_CALLER_PROVIDER:-${PROVIDER:-anthropic}}"
export ANTHROPIC_MODEL="${_CALLER_MODEL:-${ANTHROPIC_MODEL:-claude-haiku-4-5}}"

GENRE_ARG=()
if [[ $# -ge 1 ]]; then
  GENRE_ARG=(--genre "$1")
fi

echo "▶ perspective conversion (provider=$PROVIDER model=$ANTHROPIC_MODEL)"
"$PYTHON" examples/plot_modeller/run.py --mode perspective ${GENRE_ARG[@]+"${GENRE_ARG[@]}"}

echo
echo "▶ L5 confusion x-ray (post-operation, separate from conversion)"
"$PYTHON" examples/plot_modeller/analyze_l5_confusion.py --summary
