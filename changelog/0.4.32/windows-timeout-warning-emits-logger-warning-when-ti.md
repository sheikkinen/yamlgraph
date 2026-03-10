---
type: fix
scope: windows
---
- **Windows timeout warning**: Emits `logger.warning()` when `--timeout` is configured on Windows (unsupported platform) instead of silently ignoring.
