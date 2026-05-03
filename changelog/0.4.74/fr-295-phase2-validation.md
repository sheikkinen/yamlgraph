---
type: feat
scope: fsm
---
- **FR-295 Phase 2 Single-Worker Validation**: Make dispatcher inbox path configurable via `{inbox_dir}` context variable (default: `.chaplain/inbox`). Add `.chaplain/inbox-fsm/` test inbox for isolated FSM validation. Added a single-worker validation harness (retired by FR-320).
