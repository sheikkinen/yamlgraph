---
type: fix
scope: examples
---
- **FR-771 Vision Demo Executes the Manifest Tool**: the shared-vision demo's
  node is now `type: tool_call` invoking the manifest-declared `describe_image`
  through the tool registry with FR-772 inline args — the Python wrapper
  (registry bypass) is deleted and lint W001 is gone. Completes the FR-768
  smoke at the invocation boundary (reuses REQ-YG-574/REQ-YG-576 — no new
  requirement).
