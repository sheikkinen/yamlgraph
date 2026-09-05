#!/usr/bin/env bash
# FR-995: operational launcher for the outsider reader (CAP-263).
# Copied shape of scripts/review.sh — lock, lineage sentinel, artifact
# verification, exit code never trusted — with ONE inversion: the graph's
# child process runs from a clean directory OUTSIDE the repo, so the Copilot
# CLI cannot load .github/copilot-instructions.md. A reader that can see the
# rulebook is not an outsider. Zero reader doctrine here (doctrine.md).
#
# usage: scripts/outsider.sh <pr-number> [--comment] [--repo owner/name]
#        scripts/outsider.sh --input <file.md> [--label <name>]   # any title+body text; no ledger row
#        scripts/outsider.sh --selftest                          # fixtures must derive NO/NO/NO/YES
set -u
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$REPO_ROOT/.github/skills/outsider-view"
GRAPH="$SKILL/adapters/graph.yaml"
TOOLS="$SKILL/adapters/outsider_tools.py"
FIXTURES="$SKILL/fixtures"
LEDGER="${OUTSIDER_LEDGER:-$REPO_ROOT/docs/census/outsider-ledger.jsonl}"
WORKDIR="${OUTSIDER_WORKDIR:-$REPO_ROOT}"
LOCK="$WORKDIR/tmp/.outsider.lock"
STALE_MIN=10
GH_REPO="${OUTSIDER_GH_REPO:-sheikkinen/yamlgraph}"
MODEL="gpt-5.6-sol"   # pinned literally in the adapter; echoed here for the ledger

fail() { echo "outsider.sh: $1" >&2; exit "$2"; }

MODE=""; PR=""; INPUT=""; LABEL=""; COMMENT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --selftest) MODE=selftest; shift ;;
    --input)    MODE=input; INPUT="${2:-}"; shift 2 ;;
    --label)    LABEL="${2:-}"; shift 2 ;;
    --comment)  COMMENT=1; shift ;;
    --repo)     GH_REPO="${2:-}"; shift 2 ;;
    -*)         fail "unknown flag: $1" 64 ;;
    *)          [ -z "$MODE" ] && MODE=pr; PR="$1"; shift ;;
  esac
done
[ -n "$MODE" ] || fail "usage: scripts/outsider.sh <pr-number> [--comment] | --input <file> | --selftest" 64
[ -n "${OUTSIDER_EXECUTION:-}" ] && fail "you are inside an outsider execution — render the report, do not re-invoke" 70
[ -f "$GRAPH" ] && [ -f "$TOOLS" ] || fail "adapter missing: $GRAPH / $TOOLS" 66

if command -v yamlgraph >/dev/null 2>&1; then YG=(yamlgraph)
elif [ -x "$REPO_ROOT/.venv/bin/yamlgraph" ]; then YG=("$REPO_ROOT/.venv/bin/yamlgraph")
elif command -v uv >/dev/null 2>&1; then YG=(uv run --project "$REPO_ROOT" yamlgraph)
else fail "no yamlgraph executor found: activate .venv or install uv" 69; fi
PY="${REPO_ROOT}/.venv/bin/python"; [ -x "$PY" ] || PY=python3

# The clean directory: outside the repo, no .github/, removed on exit.
CHILD_CWD="$(mktemp -d "${TMPDIR:-/tmp}/outsider-XXXXXX")"
cleanup_dir() { rm -rf "$CHILD_CWD"; }
trap cleanup_dir EXIT INT TERM

mkdir -p "$WORKDIR/tmp"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +$STALE_MIN 2>/dev/null)" ]; then
    echo "outsider.sh: stale lock (older than ${STALE_MIN}m): $LOCK" >&2; [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2
    echo "outsider.sh: inspect, then remove manually with: rm -rf $LOCK" >&2; exit 75
  fi
  echo "outsider.sh: another outsider run holds the lock: $LOCK" >&2; [ -f "$LOCK/holder" ] && cat "$LOCK/holder" >&2; exit 73
fi
# Only the acquiring process may remove the lock (a losing process must leave the holder intact).
cleanup() { rm -rf "$CHILD_CWD"; rm -rf "$LOCK"; }
trap cleanup EXIT INT TERM
echo "pid=$$ started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOCK/holder"

PROMPT_DIGEST="$(shasum -a 256 "$SKILL/adapters/prompts/outsider.yaml" | cut -c1-16)"
TOOL_SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

# run_one <input-file> <label> -> prints "verdict s3 s4 report" ; returns 0 only on a validated report
run_one() {
  local input="$1" label="$2" stamp report log
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  report="$WORKDIR/tmp/outsider-${label}-${stamp}.md"
  log="$WORKDIR/tmp/outsider-${label}-${stamp}.log"
  cp "$input" "$CHILD_CWD/input.md"
  ( cd "$CHILD_CWD" && OUTSIDER_EXECUTION=1 "${YG[@]}" graph run "$GRAPH" \
      --var "input_path=$CHILD_CWD/input.md" --var "report_path=$report" --var "model=$MODEL" --full ) > "$log" 2>&1
  rm -f "$CHILD_CWD/input.md"
  # Verify by artifact and contract, never by exit code.
  if [ -s "$report" ] && "$PY" - "$report" "$TOOLS" <<'EOF' >/dev/null 2>&1
import importlib.util, sys
report, tools = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("ot", tools); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
text = open(report, encoding="utf-8").read()
assert text.startswith("**Derived verdict:** ")
m.parse_report(text)
EOF
  then
    local verdict s3 s4
    verdict="$(head -1 "$report" | sed -E 's/^\*\*Derived verdict:\*\* (YES|NO).*/\1/')"
    s3="$(awk '/^## 3\./{f=1;next} /^## 4\./{f=0} f && /^- \*\*/{n++} END{print n+0}' "$report")"
    s4="$(awk '/^## 4\./{f=1;next} f && /^- /{n++} END{print n+0}' "$report")"
    echo "$verdict $s3 $s4 $report"; return 0
  fi
  echo "outsider.sh: NO VALID REPORT for $label; see $log" >&2; tail -5 "$log" >&2; return 1
}

case "$MODE" in
  selftest)
    [ -d "$FIXTURES" ] || fail "fixtures missing: $FIXTURES" 66
    expected=(NO NO NO YES); names=(pr-591 plain-591 pr-591-v2 positive)
    rc=0
    for i in 0 1 2 3; do
      f="$FIXTURES/${names[$i]}.md"; [ -f "$f" ] || { echo "selftest: fixture missing: $f" >&2; rc=1; continue; }
      if out="$(run_one "$f" "selftest-${names[$i]}")"; then
        v="${out%% *}"; echo "selftest ${names[$i]}: derived=$v expected=${expected[$i]} ($out)"
        [ "$v" = "${expected[$i]}" ] || rc=1
      else rc=1; fi
    done
    [ $rc -eq 0 ] && echo "selftest: PASS (NO/NO/NO/YES)" || echo "selftest: FAIL" >&2
    exit $rc ;;
  input)
    [ -f "$INPUT" ] || fail "input not found: $INPUT" 66
    out="$(run_one "$INPUT" "${LABEL:-input}")" || exit 1
    echo "outsider.sh: report written: ${out##* } (derived ${out%% *}; no ledger row for --input)"; exit 0 ;;
  pr)
    command -v gh >/dev/null 2>&1 || fail "gh required" 69
    json="$(gh pr view "$PR" -R "$GH_REPO" --json title,body,headRefOid)" || fail "gh pr view failed for $PR" 66
    # Fetched PR text lives only in the trapped child directory: gone on every exit path.
    input="$CHILD_CWD/pr-${PR}.md"
    printf '%s' "$json" | "$PY" -c 'import json,sys; d=json.load(sys.stdin); print("# "+d["title"]+"\n\n"+d["body"])' > "$input"
    head_sha="$(printf '%s' "$json" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["headRefOid"])')"
    out="$(run_one "$input" "pr-${PR}")" || exit 1
    set -- $out; verdict="$1"; s3="$2"; s4="$3"; report="$4"
    echo "outsider.sh: report written: $report (derived $verdict; s3=$s3 s4=$s4)"
    # Optional comment FIRST: a run whose requested comment fails is not a measurement (R-3 / C-6).
    if [ "$COMMENT" -eq 1 ]; then
      gh pr comment "$PR" -R "$GH_REPO" --body-file "$report" >/dev/null && echo "outsider.sh: comment posted on #$PR" || fail "posting the comment failed; no ledger row written" 1
    fi
    rel_report="${report#"$WORKDIR"/}"
    "$PY" - "$TOOLS" "$LEDGER" "$GH_REPO" "$PR" "$head_sha" "$input" "$MODEL" "$PROMPT_DIGEST" "$TOOL_SHA" "$verdict" "$s3" "$s4" "$rel_report" <<'EOF' || fail "ledger append failed" 1
import importlib.util, sys
from pathlib import Path
tools, ledger, repo, pr, sha, inp, model, pdg, tsha, v, s3, s4, rep = sys.argv[1:]
spec = importlib.util.spec_from_file_location("ot", tools); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
row = m.ledger_row(repo=repo, pr=int(pr), head_sha=sha, input_text=Path(inp).read_text(encoding="utf-8"), model=model,
                   prompt_digest=pdg, tool_sha=tsha, verdict=v, s3=int(s3), s4=int(s4), report_path=rep)
m.append_ledger(Path(ledger), row, mode="pr")
print(f"ledger: +1 row ({m.distinct_pr_count(Path(ledger))} distinct PRs)")
EOF
    exit 0 ;;
esac
