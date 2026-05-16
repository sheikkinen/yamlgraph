---
type: feat
scope: fsm
---
- **FR-392**: Forwarded `snapshot.payload_keys` from checkpoint `after_state.values` into shared FSM dispatch payloads with `json_safe()` serialization while preserving existing `output_key` behavior.
