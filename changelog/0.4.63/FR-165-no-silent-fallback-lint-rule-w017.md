---
type: feat
scope: no-silent-fallback
req: REQ-YG-114
---
- **FR-165 No-Silent-Fallback Lint Rule (W017)**: Add lint rule W017 that flags `on_error: skip` nodes as silent fallback patterns violating Commandment 6. Suggests `on_error: fail` or `on_error: fallback` with explicit fallback node instead. (REQ-YG-114)
