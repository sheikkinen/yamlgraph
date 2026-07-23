#!/usr/bin/env bash
# NC-413: operational launcher for the sole-route review graph.
# This wrapper serializes and invokes the yamlgraph adapter; the graph
# remains the review execution route. Zero review doctrine here.
# Pattern: scripts/judge.sh (NC-415).
set -u

PR="${1:-}"
FR_PATH="${2:-}"
WORKDIR="${REVIEW_WORKDIR:-$(pwd)}"
LOCK="$WORKDIR/tmp/.review.lock"
ARTIFACT="$WORKDIR/tmp/draft-review.md"
GRAPH=".github/skills/review-pr/adapters/graph.yaml"
STALE_MIN=10  # 600s = graph timeout

fail() { echo "review.sh: $1" >&2; exit "$2"; }

[ -n "$PR" ] && [ -n "$FR_PATH" ] || fail "usage: scripts/review.sh <pr-number-or-branch> <fr-path>" 64
[ -f "$FR_PATH" ] || fail "FR not found: $FR_PATH" 66

# Lineage sentinel (NC-414 lesson, mechanical layer):
if [ -n "${REVIEW_EXECUTION:-}" ]; then
  fail "you are inside a review execution — render the review, do not re-invoke" 70
fi

mkdir -p "$WORKDIR/tmp"

# Atomic lock:
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_MIN 2>/dev/null)" ]; then
    echo "review.sh: stale lock (older than ${STALE_MIN}m): $LOCK" >&2
    [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
    echo "review.sh: inspect, then remove manually with: rm -rf $LOCK" >&2
    exit 75
  fi
  echo "review.sh: another review run holds the lock: $LOCK" >&2
  [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
  exit 73
fi
echo "pid=$$ started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOCK/holder"
trap 'rm -rf "$LOCK"' EXIT INT TERM

rm -f "$ARTIFACT"

# Resolve the yamlgraph executor (NC-415 P2 lesson — no silent PATH assumption):
if [ -n "${YAMLGRAPH_BIN:-}" ]; then
  YG=("$YAMLGRAPH_BIN")
elif command -v yamlgraph >/dev/null 2>&1; then
  YG=(yamlgraph)
elif command -v uv >/dev/null 2>&1; then
  YG=(uv run yamlgraph)
else
  fail "no yamlgraph executor found: activate .venv (source .venv/bin/activate), install uv, or set YAMLGRAPH_BIN" 69
fi

# Sole route: the graph reviews; sentinel exported for the child only.
REVIEW_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" --var "pr=$PR" --var "fr_path=$FR_PATH" --full
GRAPH_RC=$?

# Artifact contract (verify by artifact, never exit code):
[ -s "$ARTIFACT" ] || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT missing or empty — tmp/draft-review.md is the proof of review" 65
head -1 "$ARTIFACT" | grep -q '^\*\*Merge verdict:\*\*' || fail "contract violated: merge verdict must be LINE ONE of $ARTIFACT (doctrine: front-load the verdict)" 65

echo "review.sh: draft written: $ARTIFACT (advisory until the human merge decision)"
