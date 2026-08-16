---
type: feat
scope: examples
req: REQ-YG-582
---
- **FR-781 macOS File-Hook Example**: `examples/demos/file-hook/` — launchd `WatchPaths` demo publishing artwork descriptions via the shared vision manifest; confidence gate (only `high` publishes), pairing-as-ledger idempotence, fail-safe filenames, plist template + `install-hook.sh --render-only`, canonical install-graphs-as-system-hooks README. Shared `describe_image` gains `max_dim` downscale, `quote`/`confidence` fields, and a `vision` extra (Pillow). (REQ-YG-582)
