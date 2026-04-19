---
type: feat
scope: logging
---
- **FR-185 Root Logger Respects LOG_LEVEL**: `setup_logging()` now configures the root logger level and handler so non-yamlgraph modules (e.g. `projects.*`) also respect the `LOG_LEVEL` environment variable. (REQ-YG-046)
