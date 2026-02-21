#!/bin/bash
# scripts/diary_digest.sh — Run diary_digest graph with proper environment
# Called by launchd agent com.yamlgraph.diary-digest.plist
set -euo pipefail

# Change to project root
cd "$(dirname "$0")/.."

# Source environment variables (API keys)
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

# Activate venv and run
source .venv/bin/activate

# Run the graph
yamlgraph graph run examples/diary_digest/graph.yaml

# Commit result if diary was modified
if git diff --quiet docs/diary.md; then
    echo "No diary changes"
else
    git add docs/diary.md
    git commit -m "docs(diary): World Digest $(date +%Y-%m-%d)"
    git push
fi
