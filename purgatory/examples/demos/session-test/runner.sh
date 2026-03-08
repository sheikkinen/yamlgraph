#!/usr/bin/env bash
# Session Continuation Test Runner
# Provides mock input for the interrupt node (no real stop)
#
# Usage: ./runner.sh [genre] [place]
# Example: ./runner.sh noir "a smoke-filled jazz club"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
GENRE="${1:-noir}"
PLACE="${2:-a rain-soaked phone booth at midnight}"

echo "=== Session Continuation Test ==="
echo "Genre: $GENRE"
echo "Meeting place: $PLACE"
echo ""

# Run the graph with the Python runner that handles interrupts
python3 run_demo.py --genre "$GENRE" --place "$PLACE"
