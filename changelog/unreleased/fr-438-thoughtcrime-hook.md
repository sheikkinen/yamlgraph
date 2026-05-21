---
type: feat
scope: hooks
---
- **FR-438 Thoughtcrime Hook**: PostToolUse hook scans agent transcript for forbidden reasoning patterns, arms one-shot deny sentinel. Scans `reasoningText` with `content` fallback. Audit entries for all skip paths.
