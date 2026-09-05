---
type: feat
scope: census
---
- **FR-990 CAP Journey Census**: `examples/demos/cap_journey_census/` — per-capability census adding the columns the traceability chain cannot carry: customer journey (closed 10-entry catalog, off-catalog preserved), blast kind, keep/retire/extend disposition anchored to mechanically discovered consumers (demote-never-drop → `contested`), and a for-whom/pain/versus value proposition (`value_unstated` when incomplete). Graph and prompt authored via `scripts/author.sh`; `extract.py` computes consumers/incidents/tests before the model call; the LLM-free reducer verifies evidence substrings whitespace-normalized and runs the hidden-canary gate after artifacts are written so raw rows stay readable. Research plan: `docs/2026-09-05-research-plan-cap-journey-census.md`.
