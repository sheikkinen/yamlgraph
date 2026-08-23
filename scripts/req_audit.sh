#!/usr/bin/env bash
# FR-860: scripted scaffolding for the real requirement-witness audit run.
#
# Orchestrates the FR-851 pipeline as four fail-fast sequential phases —
# record, construct, audit, report — each tee'd to a per-phase log under
# the output directory, with a frozen-schema provenance manifest
# (run-manifest.json) so the report can never outlive the tree it
# measured. Run from the repo root.
set -euo pipefail

MODEL="claude-haiku-4-5"
PROVIDER="anthropic"
SKIP_RECORD=0
OUT=""

PYTEST_CMD="COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q --cov-report= --cov=yamlgraph --cov-context=test"

usage() {
  cat <<EOF
Usage: scripts/req_audit.sh [--out DIR] [--skip-record] [--model M] [--provider P]

Runs the FR-851 requirement-witness audit end to end (FR-860):
  record     $PYTEST_CMD
             (sequential — no -n, no mark exclusions)
  construct  python scripts/req_audit_questions.py --out DIR
  audit      yamlgraph graph run examples/demos/req_witness_audit/graph.yaml
  report     python scripts/req_audit_report.py --audit-dir DIR

Flags (no environment-variable precedence; flags or defaults only):
  --out DIR       Output directory (default: tmp/req-audit-<shortsha>)
  --skip-record   Reuse the existing .coverage; the FR-850 boundary still
                  hard-refuses missing/context-free/poisoned DBs
  --model M       Audit/report model (default: claude-haiku-4-5)
  --provider P    LLM provider (default: anthropic)
  --help          This text
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --skip-record) SKIP_RECORD=1; shift ;;
    --model) MODEL="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 64 ;;
  esac
done

if [[ ! -f scripts/req_audit_questions.py ]]; then
  echo "req_audit.sh must run from the repo root" >&2
  exit 65
fi

GIT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
GIT_DIRTY=false
[[ -n $(git status --porcelain) ]] && GIT_DIRTY=true
OUT=${OUT:-tmp/req-audit-${SHORT_SHA}}
mkdir -p "$OUT"
# Stale-artifact policy: a report only exists when every phase of THIS
# run succeeded.
rm -f "$OUT/report.md" "$OUT/.phases.tsv"

RECORDED=-1
TAGGED=-1
SKIP_COUNT=-1

finalize_manifest() {
  RM_OUT="$OUT" RM_GIT_SHA="$GIT_SHA" RM_GIT_DIRTY="$GIT_DIRTY" \
  RM_SKIP_RECORD="$SKIP_RECORD" RM_PYTEST_CMD="$PYTEST_CMD" \
  RM_RECORDED="$RECORDED" RM_TAGGED="$TAGGED" RM_SKIP_COUNT="$SKIP_COUNT" \
  RM_PROVIDER="$PROVIDER" RM_MODEL="$MODEL" python - <<'PY'
import json
import os
import platform
from importlib.metadata import version
from pathlib import Path

out = Path(os.environ["RM_OUT"])
phases = {}
tsv = out / ".phases.tsv"
if tsv.exists():
    for line in tsv.read_text().splitlines():
        name, exit_code, log, command = line.split("\t", 3)
        phases[name] = {
            "command": command,
            "exit_code": int(exit_code),
            "log": log,
        }
manifest = {
    "git_sha": os.environ["RM_GIT_SHA"],
    "git_dirty": os.environ["RM_GIT_DIRTY"] == "true",
    "output_dir": os.environ["RM_OUT"],
    "skip_record": os.environ["RM_SKIP_RECORD"] == "1",
    "pytest_command": os.environ["RM_PYTEST_CMD"],
    "coverage_core": "ctrace",
    "recorded_context_count": int(os.environ["RM_RECORDED"]),
    "tagged_test_count": int(os.environ["RM_TAGGED"]),
    "skip_count": int(os.environ["RM_SKIP_COUNT"]),
    "python_version": platform.python_version(),
    "coverage_version": version("coverage"),
    "provider": os.environ["RM_PROVIDER"],
    "model": os.environ["RM_MODEL"],
    "phases": phases,
}
(out / "run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY
}

run_phase() {
  local name="$1"
  local cmd="$2"
  local log="$OUT/$name.log"
  echo "== phase: $name"
  set +e
  eval "$cmd" 2>&1 | tee "$log"
  local exit_code=${PIPESTATUS[0]}
  set -e
  printf '%s\t%d\t%s\t%s\n' "$name" "$exit_code" "$log" "$cmd" >> "$OUT/.phases.tsv"
  if [[ $exit_code -ne 0 ]]; then
    echo "phase $name failed (exit $exit_code) — see $log" >&2
    finalize_manifest
    exit "$exit_code"
  fi
}

# Phase 1: record — honest full-suite instrument (or reuse via --skip-record).
if [[ $SKIP_RECORD -eq 0 ]]; then
  run_phase record "$PYTEST_CMD"
  SKIP_COUNT=$(grep -oE '[0-9]+ skipped' "$OUT/record.log" | tail -1 | grep -oE '[0-9]+' || echo 0)
fi

# Instrument line: recorded contexts vs tagged tests, through the FR-850
# boundary — CoverageContextError propagates as a hard refusal here.
set +e
COUNTS=$(python - <<'PY' 2>"$OUT/instrument-err.log"
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from coverage_contexts import load_coverage_contexts
from req_coverage import FRAMEWORK_TEST_DIRS, extract_req_markers

root = Path(".")
tagged = set()
for rel in FRAMEWORK_TEST_DIRS:
    test_dir = root / rel
    if not test_dir.exists():
        continue
    for filepath in sorted(test_dir.rglob("test_*.py")):
        for _req, tests in extract_req_markers(filepath).items():
            tagged.update(tests)
_, recorded = load_coverage_contexts(root, tagged or None)
print(len(recorded), len(tagged))
PY
)
INSTRUMENT_EC=$?
set -e
if [[ $INSTRUMENT_EC -ne 0 ]]; then
  cat "$OUT/instrument-err.log" >&2
  echo "instrument check failed (exit $INSTRUMENT_EC) — coverage boundary refused" >&2
  finalize_manifest
  exit "$INSTRUMENT_EC"
fi
read -r RECORDED TAGGED <<<"$COUNTS"
echo "instrument: $RECORDED recorded contexts / $TAGGED tagged tests"

# Phase 2: construct (loads via the FR-850 boundary; refusal propagates).
run_phase construct "python scripts/req_audit_questions.py --out '$OUT'"

# Phase 3: audit — the FR-851 graph maps over batches.
run_phase audit "yamlgraph graph run examples/demos/req_witness_audit/graph.yaml --var batches_dir='$OUT/batches' --var raw_dir='$OUT/raw' --full"

# Provenance must exist before the report embeds it.
finalize_manifest

# Phase 4: report — reconcile and render with embedded provenance.
run_phase report "python scripts/req_audit_report.py --audit-dir '$OUT' --model '$MODEL' --provider '$PROVIDER' --run-manifest '$OUT/run-manifest.json'"

# Final manifest includes the report phase row.
finalize_manifest
echo "✓ audit complete → $OUT/report.md (provenance: $OUT/run-manifest.json)"
