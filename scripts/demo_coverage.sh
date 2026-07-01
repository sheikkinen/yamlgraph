#!/bin/bash
# FR-636 Phase 2: Run curated demos under coverage to prove framework code paths.
#
# Each demo exercises a unique yamlgraph/ code path. Combined, they prove
# ~70-75% of framework code is reachable from real YAML graph execution.
#
# Usage:
#   ./scripts/demo_coverage.sh           # Run all, report
#   ./scripts/demo_coverage.sh --report  # Just show existing report (no runs)
#   ./scripts/demo_coverage.sh --html    # Generate HTML report after runs
#
# Requirements: coverage, yamlgraph installed, LLM API keys set.
# NOT a CI gate — runs real LLMs. Use locally or in nightly jobs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

COV_FILE=".coverage.demo"
LOG_DIR="tmp/demo-coverage"
mkdir -p "$LOG_DIR"

# --- Configuration ---
# Each entry: "graph_path|var1=val1|var2=val2"
# Pipe-separated to avoid shell quoting hell with spaces in values.
DEMOS=(
  "examples/demos/hello/graph.yaml|name=World|style=pirate"
  "examples/demos/router/graph.yaml|message=I am absolutely furious about this"
  "examples/demos/map/graph.yaml|topic=testing"
  "examples/demos/guards/graph.yaml|topic=coverage|run_llm=true"
  "examples/demos/data-files/graph.yaml|response=I loved the product quality"
  "examples/demos/verification-gate/graph.yaml|topic=software testing"
  "examples/demos/git-report/graph.yaml|input=summarize recent changes"
  "examples/demos/reflexion/graph.yaml|topic=code coverage"
  "examples/demos/fan-out/graph.yaml|topic=integration testing"
  "examples/demos/race/graph.yaml|topic=what is 2+2"
  "examples/demos/subgraph/graph.yaml|raw_text=YAMLGraph is a framework for LLM pipelines"
  "examples/demos/python-variables/graph.yaml|user_name=tester|greeting_style=formal"
  "examples/demos/router-race-candidates/graph.yaml|user_query=I need technical support"
)

# Critical modules — 0% after all runs = provably dead
CRITICAL_MODULES="graph_loader|executor\.py|edge_compiler|llm_nodes|tool_nodes|race_node|subgraph_nodes|conditions|guard_evaluator|data_loader|verification"

# --- Functions ---
run_demo() {
  local entry="$1"
  local graph vars_str
  graph=$(echo "$entry" | cut -d'|' -f1)
  vars_str=$(echo "$entry" | cut -d'|' -f2- -s)

  local demo_name
  demo_name=$(basename "$(dirname "$graph")")
  local log_file="$LOG_DIR/$demo_name.log"

  # Build --var flags as array to preserve spaces in values
  local -a var_args=()
  if [[ -n "$vars_str" ]]; then
    IFS='|' read -ra VARS <<< "$vars_str"
    for v in "${VARS[@]}"; do
      var_args+=(--var "$v")
    done
  fi

  printf "  ▶ %-25s" "$demo_name"

  # Run under coverage, capture output
  local start_time
  start_time=$(python3 -c "import time; print(f'{time.time():.3f}')")

  if coverage run --data-file="$COV_FILE" --append --source=yamlgraph \
    -m yamlgraph.cli graph run "$graph" "${var_args[@]}" --full \
    > "$log_file" 2>&1; then
    local end_time
    end_time=$(python3 -c "import time; print(f'{time.time():.3f}')")
    local elapsed
    elapsed=$(python3 -c "print(f'{$end_time - $start_time:.1f}s')")
    printf "✓ %s\n" "$elapsed"
    return 0
  else
    local exit_code=$?
    printf "✗ (exit %d, see %s)\n" "$exit_code" "$log_file"
    return 0  # Don't abort — collect partial coverage
  fi
}

run_cli_commands() {
  printf "  ▶ %-25s" "graph lint"
  if coverage run --data-file="$COV_FILE" --append --source=yamlgraph \
    -m yamlgraph.cli graph lint examples/demos/hello/graph.yaml \
    > "$LOG_DIR/lint.log" 2>&1; then
    printf "✓\n"
  else
    printf "✗\n"
  fi

  printf "  ▶ %-25s" "graph info"
  if coverage run --data-file="$COV_FILE" --append --source=yamlgraph \
    -m yamlgraph.cli graph info examples/demos/hello/graph.yaml \
    > "$LOG_DIR/info.log" 2>&1; then
    printf "✓\n"
  else
    printf "✗\n"
  fi

  printf "  ▶ %-25s" "graph validate"
  if coverage run --data-file="$COV_FILE" --append --source=yamlgraph \
    -m yamlgraph.cli graph validate examples/demos/hello/graph.yaml \
    > "$LOG_DIR/validate.log" 2>&1; then
    printf "✓\n"
  else
    printf "✗\n"
  fi
}

check_critical() {
  echo ""
  echo "━━━ Critical Module Check ━━━"
  local zeros
  zeros=$(coverage report --data-file="$COV_FILE" 2>/dev/null \
    | grep -E "$CRITICAL_MODULES" \
    | grep " 0%" || true)

  if [[ -n "$zeros" ]]; then
    echo "❌ Critical modules at 0% — provably dead or misconfigured:"
    echo "$zeros"
    echo ""
    return 1
  else
    echo "✅ All critical modules have >0% demo coverage."
    return 0
  fi
}

# --- Main ---
if [[ "${1:-}" == "--report" ]]; then
  if [[ ! -f "$COV_FILE" ]]; then
    echo "No demo coverage data found. Run without --report first."
    exit 1
  fi
  coverage report --data-file="$COV_FILE" --skip-covered --show-missing
  exit 0
fi

echo "━━━ FR-636: Demo Coverage Run ━━━"
echo "Running ${#DEMOS[@]} demos + 3 CLI commands under coverage..."
echo ""

rm -f "$COV_FILE"

echo "📊 Graph demos:"
for entry in "${DEMOS[@]}"; do
  run_demo "$entry"
done

echo ""
echo "📊 CLI commands:"
run_cli_commands

echo ""
echo "━━━ Coverage Report (demo-only) ━━━"
coverage report --data-file="$COV_FILE" --skip-covered 2>/dev/null | tail -5
echo ""

# Full report to file
coverage report --data-file="$COV_FILE" --show-missing > "$LOG_DIR/coverage-report.txt" 2>/dev/null
echo "Full report: $LOG_DIR/coverage-report.txt"

if [[ "${1:-}" == "--html" ]]; then
  coverage html --data-file="$COV_FILE" -d "$LOG_DIR/htmlcov" 2>/dev/null
  echo "HTML report: $LOG_DIR/htmlcov/index.html"
fi

# Critical module gate
check_critical
