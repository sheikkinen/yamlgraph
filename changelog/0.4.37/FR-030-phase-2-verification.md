---
type: feat
scope: phase
---
- **FR-030 Phase 2 Verification**: Tests confirm `subgraphs=True` also enables streaming from `mode=invoke` subgraphs — no async conversion needed. LangGraph's callback system propagates `StreamMessagesHandler` through sync `invoke()` boundary.
