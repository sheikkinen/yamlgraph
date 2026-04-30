#!/usr/bin/env bash
# metrics.sh — Emit pipeline timing JSON
#
# Uses env vars: METRIC_DIR, T_CYCLE_START, TOPIC_FILE, CYCLE_OUTCOME

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

METRIC_DIR="${METRIC_DIR:-.chaplain/metrics}"
T_CYCLE_START="${T_CYCLE_START:-$(date +%s)}"
CYCLE_OUTCOME="${CYCLE_OUTCOME:-unknown}"

write_cycle_metrics() {
    local t_end elapsed ts_safe inbox_base
    t_end=$(date +%s)
    elapsed=$((t_end - T_CYCLE_START))
    ts_safe=$(date -u +%Y%m%dT%H%M%S)
    inbox_base=$(basename "$TOPIC_FILE")

    mkdir -p "$METRIC_DIR"

    printf '{\n  "pipeline": "watcher2",\n  "inbox_item": "%s",\n  "outcome": "%s",\n  "ci_result": "%s",\n  "total_seconds": %d\n}\n' \
        "$inbox_base" "$CYCLE_OUTCOME" "${CI_RESULT:-n/a}" "$elapsed" \
        > "$METRIC_DIR/watcher2-${ts_safe}.json" 2>/dev/null || log_warn "Failed to write metrics"

    log_info "Metrics written: ${elapsed}s total, outcome=$CYCLE_OUTCOME"
}

write_cycle_metrics
