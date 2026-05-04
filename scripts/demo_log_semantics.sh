#!/bin/bash
# Shared semantic contract for demo-output.log validation (FR-325).
# shellcheck shell=bash

DEMO_LOG_FATAL_MARKERS='Node .+ failed|❌ Error:|\[ERROR\]|exit code [1-9]'
DEMO_LOG_SUCCESS_MARKERS='Graph execution completed successfully|Node .+ completed successfully|✓ Graph execution completed successfully|✅'

validate_demo_output_log_file() {
  local log_file="$1"
  local log_label="${2:-$log_file}"

  if [ ! -f "$log_file" ]; then
    echo "::error::demo-output.log missing from workspace: $log_label"
    return 1
  fi

  if ! grep -q '[^[:space:]]' "$log_file"; then
    echo "::error::demo-output.log is empty: $log_label"
    return 1
  fi

  if grep -Eiq "$DEMO_LOG_FATAL_MARKERS" "$log_file"; then
    echo "::error::demo-output.log contains fatal execution marker: $log_label"
    grep -Ein "$DEMO_LOG_FATAL_MARKERS" "$log_file" | head -n 5
    return 1
  fi

  if ! grep -Eiq "$DEMO_LOG_SUCCESS_MARKERS" "$log_file"; then
    echo "::error::demo-output.log missing success evidence: $log_label"
    echo "Expected one of: $DEMO_LOG_SUCCESS_MARKERS"
    return 1
  fi

  echo "✅ Demo proof validated: $log_label"
  return 0
}
