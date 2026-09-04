#!/usr/bin/env bash
# NC-415: operational launcher for the sole-route judge graph.
# This wrapper serializes and invokes the yamlgraph adapter; the graph
# remains the judge execution route (C-6). Zero judging doctrine here (C-2).
# FR-960: backend selection (JUDGE_BACKEND=copilot|claude) and a
# per-backend-per-FR artifact path so two backends, or two FRs judged back
# to back, never delete each other's drafts (2026-09-02 clobber).
set -u

FR_PATH="${1:-}"
WORKDIR="${JUDGE_WORKDIR:-$(pwd)}"
LOCK="$WORKDIR/tmp/.judge.lock"
GRAPH=".github/skills/judge-fr/adapters/graph.yaml"
STALE_MIN=10  # 600s = graph timeout

fail() { echo "judge.sh: $1" >&2; exit "$2"; }

[ -n "$FR_PATH" ] || fail "usage: [JUDGE_BACKEND=copilot|claude] scripts/judge.sh <fr-path>" 64
[ -f "$FR_PATH" ] || fail "FR not found: $FR_PATH" 66

# FR-960: closed backend set, validated before the lock is taken so a typo
# can never select the default silently.
BACKEND="${JUDGE_BACKEND:-copilot}"
case "$BACKEND" in
  copilot|claude) ;;
  *) fail "unknown JUDGE_BACKEND '$BACKEND' (expected copilot or claude)" 64 ;;
esac

# FR-960: per-backend-per-FR artifact. Deterministic and human-readable; a
# rerun of the same backend on the same FR replaces only its own draft.
FR_SLUG="$(basename "$FR_PATH")"
FR_SLUG="${FR_SLUG%.*}"
ARTIFACT="$WORKDIR/tmp/draft-judgement-${BACKEND}-${FR_SLUG}.md"

# Lineage sentinel (NC-414 recursion guard, mechanical layer):
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

# Resolve the yamlgraph executor (PR #58 review P2 — no silent PATH assumption):
if [ -n "${YAMLGRAPH_BIN:-}" ]; then
  YG=("$YAMLGRAPH_BIN")
elif command -v yamlgraph >/dev/null 2>&1; then
  YG=(yamlgraph)
elif command -v uv >/dev/null 2>&1; then
  YG=(uv run yamlgraph)
else
  fail "no yamlgraph executor found: activate .venv (source .venv/bin/activate), install uv, or set YAMLGRAPH_BIN" 69
fi

# Sole route: the graph judges; sentinel exported for the child only.
JUDGE_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" \
  --var "fr_path=$FR_PATH" \
  --var "backend=$BACKEND" \
  --var "artifact_path=$ARTIFACT" \
  --full
GRAPH_RC=$?

# Artifact contract (NC-414: verify by artifact, never exit code):
[ -s "$ARTIFACT" ] || fail "contract violated (graph rc=$GRAPH_RC): $ARTIFACT missing or empty — the draft artifact is the proof of judgement" 65
grep -q '^\*\*Verdict:\*\*' "$ARTIFACT" || fail "contract violated: no verdict line in $ARTIFACT" 65

echo "judge.sh: draft written: $ARTIFACT (backend=$BACKEND; advisory until human-reviewed)"
