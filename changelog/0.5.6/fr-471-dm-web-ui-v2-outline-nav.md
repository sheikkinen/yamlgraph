---
type: feat
scope: examples
req: REQ-YG-469
---
- **FR-471 DM Web UI v2 — Outline Navigation**: The dungeon-master web outline now lists chapters as navigation links; opening a chapter lazily materializes its beat stubs once (a `materialized` guard keeps revisits idempotent and preserves DM edits), chapter summaries and beat stubs are inline-editable and persist to the story document, and a breadcrumb links back to the outline while naming the current chapter. (REQ-YG-469)
