---
type: feat
scope: hooks
---
- **FR-438 Thoughtcrime Hook**: PostToolUse hook scans agent transcript for forbidden reasoning patterns, arms one-shot deny sentinel. Scans `reasoningText` with `content` fallback when extended thinking is unavailable. Explicit audit entries (`skip/no-session-id`, `skip/no-transcript`, `skip/no-scannable-text`) for all skip paths. Armed entries include `source` field for traceability.
