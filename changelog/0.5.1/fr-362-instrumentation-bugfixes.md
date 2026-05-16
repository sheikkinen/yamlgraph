---
type: fix
scope: copilot
---
- **FR-362 Instrumentation bugfixes**: correct OTel env var (`COPILOT_OTEL_JSONL` → `COPILOT_OTEL_FILE_EXPORTER_PATH`), add `--allow-all-tools --allow-all-paths` to Copilot run command, fix OTel extractor to parse flat `{"type":"span"}` format instead of OTLP `resourceSpans` JSON.
