#!/usr/bin/env bash
# FR-890: operational launcher for the sole-route research graph.
# This wrapper serializes and invokes the research adapter; the graph
# is the research execution route. Zero research doctrine here.
# Lineage: scripts/judge.sh (FR-758) / scripts/author.sh (FR-765).
set -u

BRIEF_PATH="${1:-}"
WORKDIR="${RESEARCH_WORKDIR:-$(pwd)}"
LOCK="$WORKDIR/tmp/.research.lock"
ARTIFACT="$WORKDIR/tmp/draft-alternatives.md"
GRAPH="examples/demos/research-route/graph.yaml"
STALE_MIN=10  # 600s = graph timeout

fail() { echo "research.sh: $1" >&2; exit "$2"; }

[ -n "$BRIEF_PATH" ] || fail "usage: scripts/research.sh <problem-brief.md>" 64
[ -f "$BRIEF_PATH" ] || fail "problem brief not found: $BRIEF_PATH" 66

# Lineage sentinel (re-entry guard, mechanical layer):
if [ -n "${RESEARCH_EXECUTION:-}" ]; then
  fail "you are inside a research execution — produce the findings, do not re-invoke" 70
fi

# Closure preflight (R-2): deterministic stdlib check, no tokens spent
# on a contaminated brief. The brief is the input-closure boundary.
PYBIN=$(command -v python3 || command -v python) \
  || fail "python3 required for brief preflight" 69
"$PYBIN" "$(dirname "$0")/research_preflight.py" "$BRIEF_PATH" \
  || fail "brief closure preflight failed; see violations above" 64

mkdir -p "$WORKDIR/tmp"

# Atomic lock:
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_MIN 2>/dev/null)" ]; then
    echo "research.sh: stale lock (older than ${STALE_MIN}m): $LOCK" >&2
    [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
    echo "research.sh: inspect, then remove manually with: rm -rf $LOCK" >&2
    exit 75
  fi
  echo "research.sh: another research run holds the lock: $LOCK" >&2
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
  fail "no yamlgraph executor found: activate .venv (source .venv/bin/activate), install uv, or set YAMLGRAPH_BIN" 69
fi

# Sole route: the graph researches; sentinel exported for the child only.
RESEARCH_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" --var "brief_path=$BRIEF_PATH" --full
GRAPH_RC=$?

# Artifact contract: verify by schema/shape, never exit code (AC-08).
[ -s "$ARTIFACT" ] || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT missing or empty — tmp/draft-alternatives.md is the proof of research" 65
"$PYBIN" "$(dirname "$0")/research_preflight.py" --verify-artifact "$ARTIFACT" \
  || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT fails the frozen schema" 65

# Provenance stamp (FR-896 R-3): committed run log line. Same-actor log —
# this records hash consistency for later integrity checks, not proof of
# execution. Verify with: research_preflight.py --verify-promotion.
RUN_LOG="$WORKDIR/feature-requests/research-runs.jsonl"
mkdir -p "$WORKDIR/feature-requests"
sha256() { "$PYBIN" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }
BRIEF_SHA=$(sha256 "$BRIEF_PATH")
ARTIFACT_SHA=$(sha256 "$ARTIFACT")
CODE_SHA=$(git -C "$(dirname "$0")/.." rev-parse HEAD 2>/dev/null || echo unknown)
printf '{"timestamp":"%s","brief_path":"%s","brief_sha256":"%s","artifact_sha256":"%s","code_git_sha":"%s","graph":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BRIEF_PATH" "$BRIEF_SHA" "$ARTIFACT_SHA" "$CODE_SHA" "$GRAPH" >> "$RUN_LOG"
echo "research.sh: provenance line appended: $RUN_LOG"

echo "research.sh: draft written: $ARTIFACT (promote to feature-requests/FR-XXX.research.md on acceptance)"
