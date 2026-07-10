---
type: feat
scope: novel_fandom
req: REQ-YG-516
---
- **FR-685 Genesis Self-Correcting Pipeline**: Added gate→route→fix loop to genesis: `validate` writes `gate_result`, conditional edge routes to `fix_stubs` (LLM) on orphans, loops back to `validate`, capped by `loop_limits: validate: 3`. Happy path stays at 2 LLM calls. (REQ-YG-516)
