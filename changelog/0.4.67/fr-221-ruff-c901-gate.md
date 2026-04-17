---
type: feat
scope: lint
req: REQ-YG-221
---
- **FR-221 Ruff C901 Cognitive Complexity Gate**: Enable `C901` in ruff `select` with `max-complexity = 15`; refactor `llm_nodes.py`, `agent.py`, and `checks.py` to reduce complexity below threshold; remaining suppressions documented in `docs/confessions.md`. (REQ-YG-221)
