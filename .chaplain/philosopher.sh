#!/usr/bin/env bash
# FR-184: Philosopher Daemon
# Scans diary for recurring patterns and proposes graduations to Scripture
#
# Usage: .chaplain/philosopher.sh [--once]
#   --once: Run once and exit (default mode)
#   Without --once: Poll every 24h (for background daemon use)

set -e

DIARY_DIR="${DIARY_DIR:-docs/diary}"
INBOX="${INBOX:-.chaplain/inbox}"
LOOKBACK_DAYS="${LOOKBACK_DAYS:-30}"
GRADUATION_THRESHOLD="${GRADUATION_THRESHOLD:-3}"
LOG="tmp/philosopher-$(date +%Y-%m-%d).log"

mkdir -p tmp

yamlgraph graph run examples/philosopher/graph.yaml \
  --var diary_dir="$DIARY_DIR" \
  --var inbox_dir="$INBOX" \
  --var lookback_days="$LOOKBACK_DAYS" \
  --var graduation_threshold="$GRADUATION_THRESHOLD" \
  --var date="$(date +%Y-%m-%d)" \
  --var diary_prefix="Philosopher" \
  --full 2>&1 | tee "$LOG"
