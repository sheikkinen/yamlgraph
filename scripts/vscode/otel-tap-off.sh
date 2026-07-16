#!/usr/bin/env bash
# Disarm the Copilot OTel file tap (undo otel-tap-on.sh).
set -euo pipefail

for var in COPILOT_OTEL_ENABLED COPILOT_OTEL_EXPORTER_TYPE \
  COPILOT_OTEL_FILE_EXPORTER_PATH COPILOT_OTEL_HTTP_INSTRUMENTATION \
  COPILOT_OTEL_LOG_LEVEL COPILOT_OTEL_CAPTURE_CONTENT; do
  launchctl unsetenv "$var" 2>/dev/null || true
done

echo "OTel tap disarmed. Restart VS Code (Cmd+Q, reopen) to apply."
