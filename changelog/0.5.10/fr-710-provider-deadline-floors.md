---
type: fix
scope: llm
---
- **FR-710 Provider Deadline Floors**: the `LLM_REQUEST_TIMEOUT` knob (FR-708) now validates against provider-enforced deadline floors at construction — google/vertex require ≥ 10 s (field-verified via a live 400: *"Manually set deadline 5s is too short. Minimum allowed deadline is 10s."*). A below-floor value — env, caller kwarg, or `timeout=None` — raises once at construction naming the floor, the value, and its source, instead of a confusing 400 per request that silently drops the gemini candidate from every race. Non-floored providers unchanged; silent clamping deliberately rejected.
