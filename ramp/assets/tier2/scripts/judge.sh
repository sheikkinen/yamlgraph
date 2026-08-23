#!/usr/bin/env bash
# Operational launcher for the sole-route judge graph (ramp Tier-2
# curated copy — see ramp/curation-diffs.md#judge-sh in the source repo).
# This wrapper serializes and invokes the yamlgraph adapter; the graph
# remains the judge execution route. Zero judging doctrine here.
set -u

FR_PATH="${1:-}"
WORKDIR="${JUDGE_WORKDIR:-$(pwd)}"
LOCK="$WORKDIR/tmp/.judge.lock"
ARTIFACT="$WORKDIR/tmp/draft-judgement.md"
GRAPH=".github/skills/judge-fr/adapters/graph.yaml"
STALE_MIN=10  # 600s = graph timeout

fail() { echo "judge.sh: $1" >&2; exit "$2"; }

[ -n "$FR_PATH" ] || fail "usage: scripts/judge.sh <fr-path>" 64
[ -f "$FR_PATH" ] || fail "FR not found: $FR_PATH" 66

# Ramp curation: the adapter graph is not shipped by the installer —
# author it in this repo per the skill doctrine before first use.
[ -f "$GRAPH" ] || fail "judge adapter graph not installed: $GRAPH — see .github/skills/judge-fr/doctrine.md for the sole-route contract" 78

# Lineage sentinel (recursion guard, mechanical layer):
if [ -n "${JUDGE_EXECUTION:-}" ]; then
  fail "you are inside a judge execution — render the verdict, do not re-invoke" 70
fi

mkdir -p "$WORKDIR/tmp"

# Atomic lock:
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_MIN 2>/dev/null)" ]; then
    echo "judge.sh: stale lock (older than ${STALE_MIN}m): $LOCK" >&2
    [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
    echo "judge.sh: inspect, then remove manually with: rm -rf $LOCK" >&2
    exit 75
  fi
  echo "judge.sh: another judge run holds the lock: $LOCK" >&2
  [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
  exit 73
fi
echo "pid=$$ started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOCK/holder"
trap 'rm -rf "$LOCK"' EXIT INT TERM

rm -f "$ARTIFACT"

# Resolve the yamlgraph executor (no silent PATH assumption):
if [ -n "${YAMLGRAPH_BIN:-}" ]; then
  YG=("$YAMLGRAPH_BIN")
elif command -v yamlgraph >/dev/null 2>&1; then
  YG=(yamlgraph)
elif command -v uv >/dev/null 2>&1; then
  YG=(uv run yamlgraph)
else
  fail "no yamlgraph executor found: activate a venv, install uv, or set YAMLGRAPH_BIN" 69
fi

# Sole route: the graph judges; sentinel exported for the child only.
JUDGE_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" --var "fr_path=$FR_PATH" --full
GRAPH_RC=$?

# Artifact contract (verify by artifact, never exit code):
[ -s "$ARTIFACT" ] || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT missing or empty — tmp/draft-judgement.md is the proof of judgement" 65
grep -q '^\*\*Verdict:\*\*' "$ARTIFACT" || fail "contract violated: no verdict line in $ARTIFACT" 65

echo "judge.sh: draft written: $ARTIFACT (advisory until human-reviewed)"
