---
type: fix
scope: artifact-hash
req: REQ-YG-552
---
- **FR-1051 `artifact_hash` honours `defaults.prompts_relative`**: `compute_artifact_hash` read `prompts_relative` from the graph's top level only, while the loader and every other reader fall back to `defaults:`. A graph declaring its prompt settings under `defaults:` — the documented place — compiled and linted cleanly but died at run time with `Cannot hash executable artifact: unresolved prompt ...`. The hash now resolves the setting presence-based, exactly as `GraphConfig` does: absent at top level falls back to `defaults`, and an explicit top-level `false` still wins over `defaults: true`. First consumer: the csap voicebot upgrade past 0.5.23, whose 62 scripted conversations all failed on the first turn. (REQ-YG-552)
