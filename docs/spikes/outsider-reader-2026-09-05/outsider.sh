#!/usr/bin/env bash
# Outsider spike launcher — copied shape of scripts/review.sh (lock, artifact
# check, no exit-code trust), stripped of judge/review doctrine. Runs from THIS
# folder so the Copilot CLI sees no repo instructions.
#
# usage: ./outsider.sh <input.md> [model]      # input = PR title+body as markdown
#        ./outsider.sh --pr <number> [model]   # fetch from sheikkinen/yamlgraph
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 1
MODEL="gpt-5.6-sol"
if [ "${1:-}" = "--pr" ]; then
  PR="${2:?pr number}"; MODEL="${3:-$MODEL}"
  INPUT="inputs/pr-${PR}.md"
  gh pr view "$PR" -R sheikkinen/yamlgraph --json title,body -q '"# " + .title + "\n\n" + .body' > "$INPUT" || exit 66
else
  INPUT="${1:?input file}"; MODEL="${2:-$MODEL}"
fi
[ -f "$INPUT" ] || { echo "outsider.sh: input not found: $INPUT" >&2; exit 66; }
LOCK="$HERE/.outsider.lock"
if ! mkdir "$LOCK" 2>/dev/null; then echo "outsider.sh: another run holds $LOCK" >&2; exit 73; fi
trap 'rm -rf "$LOCK"' EXIT INT TERM
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="out/$(basename "${INPUT%.md}")-${MODEL}-${STAMP}.md"
LOG="out/$(basename "${INPUT%.md}")-${MODEL}-${STAMP}.log"
rm -f "$REPORT"
OUTSIDER_EXECUTION=1 yamlgraph graph run graph.yaml \
  --var "input_path=$INPUT" --var "report_path=$REPORT" --var "model=$MODEL" --full > "$LOG" 2>&1
RC=$?
# Verify by artifact, never by exit code.
if [ -s "$REPORT" ] && grep -q '^## 1\. In my own words' "$REPORT"; then
  echo "outsider.sh: report written: $REPORT (graph rc=$RC)"; exit 0
fi
echo "outsider.sh: NO REPORT (graph rc=$RC); see $LOG" >&2; tail -20 "$LOG" >&2; exit 1
