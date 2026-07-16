#!/usr/bin/env bash
# FR-less spike (scripts/vscode): enable the Copilot OTel file tap.
# Sets launchctl env (GUI-app scope, persists until logout/off-script).
# After running: FULLY quit VS Code (Cmd+Q) and reopen, send one chat
# turn, then verify tmp/copilot-otel.jsonl for HTTP spans with
# copilot_quota_snapshots / cache-split token fields.
#
# Deliberately NOT set: COPILOT_OTEL_CAPTURE_CONTENT (prompt text in
# spans — privacy-heavy; escalate only if the quota fields are absent
# without it, two_strike_split).
set -euo pipefail

OUT="${1:-$HOME/src/yamlgraph/tmp/copilot-otel.jsonl}"
mkdir -p "$(dirname "$OUT")"

launchctl setenv COPILOT_OTEL_ENABLED true
launchctl setenv COPILOT_OTEL_EXPORTER_TYPE file
launchctl setenv COPILOT_OTEL_FILE_EXPORTER_PATH "$OUT"
launchctl setenv COPILOT_OTEL_HTTP_INSTRUMENTATION true
launchctl setenv COPILOT_OTEL_LOG_LEVEL debug

echo "OTel tap armed → $OUT"
echo "Now: Cmd+Q VS Code, reopen, send one chat turn, then verify."
echo "Disarm with: scripts/vscode/otel-tap-off.sh"
