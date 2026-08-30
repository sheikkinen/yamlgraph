---
type: fix
scope: hooks
req: REQ-YG-629
---
- **FR-925 Lane Delivery Reaches Agent Context**: SessionStart hook now emits the session lane through the structured `hookSpecificOutput.additionalContext` JSON envelope instead of plain stdout (which VS Code captures into hook telemetry and discards). Refusal and not-live paths stay envelope-free. (REQ-YG-629)
