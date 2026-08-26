#!/usr/bin/env bash
# FR-893: diary trap recurrence census — month×decade batched corpus_census
# runs, then LLM-free aggregation with hidden-canary validation.
set -euo pipefail
cd "$(dirname "$0")/.."

DIARY=docs/diary
OUT=tmp/diary-census
ADAPTERS=examples/demos/corpus_census/adapters
RUBRIC='List the NAMED cognitive traps, failure patterns, or recurring heuristics this diary entry itself identifies (its own trap/insight vocabulary). Output them as comma-separated canonical snake_case labels in the judgement field (e.g. stale_msg_file, line_pinned_gates, heading_consumption). Use the entry'"'"'s own naming, normalized. If the entry names no trap or heuristic, abstain.'

mkdir -p "$OUT"
start=$SECONDS
sha=$(git rev-parse --short HEAD)

months=$(ls $DIARY/*.md | grep -oE '20[0-9]{2}-[0-9]{2}' | sort -u)
ledgers=()
for ym in $months; do
  for decade in 0 1 2 3; do
    needle="${ym}-${decade}"
    count=$(ls $DIARY/*.md 2>/dev/null | grep -c "$needle" || true)
    [ "$count" -eq 0 ] && continue
    batch="$OUT/ledger-${needle}"
    echo "→ batch $needle ($count entries)"
    PYTHONPATH=$PWD yamlgraph graph run examples/demos/corpus_census/graph.yaml \
      --tool discover="$ADAPTERS/diary-discover.tool.yaml" \
      --tool extract="$ADAPTERS/diary-extract.tool.yaml" \
      --var source="$DIARY:$needle" \
      --var rubric="$RUBRIC" \
      --var output_path="$batch.md" \
      --json > "$OUT/run-$needle.json" 2> "$OUT/run-$needle.log"
    ledgers+=("$batch.jsonl")
  done
done

duration=$((SECONDS - start))
PYTHONPATH=$PWD python -m examples.demos.corpus_census.adapters.diary_recurrence \
  "${ledgers[@]}" \
  --output-dir docs/diary/census \
  --canary 'msg_txt|msg_file|msgfile=3' --canary 'line_pin|line_number|stale_line=3' \
  --exclude-scripture .github/copilot-instructions.md \
  --inbox-threshold 10 \
  --meta model=claude-haiku-4-5 --meta git_sha="$sha" \
  --meta duration_s="$duration" --meta corpus="$DIARY (all months, decade-batched)"
echo "diary_census: done in ${duration}s"
