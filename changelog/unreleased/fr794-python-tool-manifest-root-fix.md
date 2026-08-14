---
type: fix
scope: tools
req: REQ-YG-588
---
- **FR-794 Shared Python Tool Manifest Root Confinement Fix**: `type: python` tool manifests referenced via `manifest:` from a different directory than the consuming graph (the "one tool, many consumers" pattern) no longer fail FR-445's graph-root confinement check — confinement is relocated to the manifest's own declaration root, closing a previously-unguarded gap where a manifest's own path was never validated. Inline (non-manifest) Python tools keep FR-445 behavior unchanged. Repairs the already-merged FR-785 `endpoint-probe` graph's `curl_probe` tool loading. (REQ-YG-588)
