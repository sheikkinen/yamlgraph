#!/usr/bin/env bash
# FR-765: operational launcher for the sole-route graph-authoring adapter.
# This wrapper serializes and invokes the yamlgraph adapter; the graph
# is the authoring execution route. Zero authoring doctrine here.
# Lineage: scripts/judge.sh (FR-758 / NC-415).
set -u

TASK_PATH="${1:-}"
WORKDIR="${AUTHOR_WORKDIR:-$(pwd)}"
LOCK="$WORKDIR/tmp/.author.lock"
ARTIFACT="$WORKDIR/tmp/draft-authoring-report.md"
GRAPH=".github/skills/graph-authoring/adapters/graph.yaml"
STALE_MIN=15  # 900s = graph timeout

fail() { echo "author.sh: $1" >&2; exit "$2"; }

[ -n "$TASK_PATH" ] || fail "usage: scripts/author.sh <task-brief.md>" 64
[ -f "$TASK_PATH" ] || fail "task brief not found: $TASK_PATH" 66

# Lineage sentinel (NC-414 recursion guard, mechanical layer):
if [ -n "${AUTHOR_EXECUTION:-}" ]; then
  fail "you are inside an authoring execution — author directly, do not re-invoke" 70
fi

mkdir -p "$WORKDIR/tmp"

# Atomic lock:
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_MIN 2>/dev/null)" ]; then
    echo "author.sh: stale lock (older than ${STALE_MIN}m): $LOCK" >&2
    [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
    echo "author.sh: inspect, then remove manually with: rm -rf $LOCK" >&2
    exit 75
  fi
  echo "author.sh: another authoring run holds the lock: $LOCK" >&2
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

# Sole route: the graph authors; sentinel exported for the child only.
AUTHOR_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" --var "task_path=$TASK_PATH" --full
GRAPH_RC=$?

# Artifact contract (verify by artifact, never exit code):
[ -s "$ARTIFACT" ] || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT missing or empty — tmp/draft-authoring-report.md is the proof of authoring" 65
for heading in "Artifacts" "Precedent" "Validation" "Repairs" "Blocked validation"; do
  grep -q "$heading" "$ARTIFACT" || fail "contract violated: no '$heading' heading in $ARTIFACT" 65
done

# At least one listed repo-relative artifact path must exist (R-2).
# Extract candidate paths from the Artifacts section: backticked or bare
# tokens containing a slash and a file extension.
FOUND_ARTIFACT=""
while IFS= read -r candidate; do
  if [ -e "$WORKDIR/$candidate" ]; then
    FOUND_ARTIFACT="$candidate"
    break
  fi
done < <(awk '/^#+ *Artifacts/{flag=1; next} /^#+ /{flag=0} flag' "$ARTIFACT" \
  | grep -oE '[A-Za-z0-9_.\/-]+\.[A-Za-z0-9]+' | grep '/' | sort -u)
[ -n "$FOUND_ARTIFACT" ] || fail "contract violated: no listed artifact path under 'Artifacts' exists in $WORKDIR" 65

echo "author.sh: report written: $ARTIFACT (artifact verified: $FOUND_ARTIFACT; advisory until human-reviewed and committed)"
