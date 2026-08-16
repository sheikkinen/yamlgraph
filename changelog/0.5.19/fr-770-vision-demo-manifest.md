---
type: feat
scope: examples
---
- **FR-770 Vision Demo Consumes the Tool Manifest**: the shared-vision-tool
  demo now declares `describe_image` via `manifest:` referencing
  `examples/shared/describe_image.tool.yaml` — the first committed consumer
  of the FR-768 manifest mechanism (REQ-YG-574, CAP-216), pinned by
  artifact-backed round-trip tests.
